"""
16-MEMS Orange Pi UDP Stream Source
=====================================
The Orange Pi streams 16-channel PCM audio over the network as UDP
packets.  This source binds a UDP socket, receives raw data, and
assembles it into (N, 16) numpy arrays.

Packet format
-------------
Each UDP datagram is assumed to be raw bytes:
    [4 bytes: sequence_number (uint32)] +
    [4 bytes: sample_count   (uint32)] +
    [remaining: interleaved int16 samples for 16 channels]

If your Orange Pi sends a different format, override ``_decode_packet``.
"""

import socket
import struct
import threading
import collections
import numpy as np
from typing import Dict, Any, Optional, Tuple
from .base import AudioSource


class SixteenMEMSSource(AudioSource):
    """
    Receive 16-channel audio streamed over UDP from an Orange Pi.

    Parameters
    ----------
    host : str
        IP to bind the receiver socket to (``"0.0.0.0"`` for all interfaces).
    port : int
        UDP port to listen on.
    sample_rate : int
        Expected sampling frequency from the Orange Pi.
    buffer_seconds : float
        Ring-buffer length in seconds (to absorb network jitter).
    sample_format : str
        ``"int16"`` or ``"float32"``  – how the Orange Pi encodes samples.
    """

    CHANNELS = 16
    HEADER_SIZE = 8  # seq (4) + sample_count (4)

    def __init__(self, host: str = "0.0.0.0", port: int = 5000,
                 sample_rate: int = 48000, buffer_seconds: float = 2.0,
                 sample_format: str = "int16"):
        super().__init__(sample_rate=sample_rate, channels=self.CHANNELS)
        self.host = host
        self.port = port
        self.sample_format = sample_format

        buf_frames = int(sample_rate * buffer_seconds)
        self._buffer: collections.deque = collections.deque(maxlen=buf_frames)
        self._sock: Optional[socket.socket] = None
        self._recv_thread: Optional[threading.Thread] = None
        self._last_seq: int = -1
        self._dropped_packets: int = 0

    # ------------------------------------------------------------------
    def connect(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.settimeout(1.0)
        self.is_running = True

        self._recv_thread = threading.Thread(target=self._recv_loop,
                                             daemon=True)
        self._recv_thread.start()
        print(f"[SixteenMEMSSource] Listening on {self.host}:{self.port}")

    def _recv_loop(self) -> None:
        while self.is_running:
            try:
                data, addr = self._sock.recvfrom(65535)
                frames = self._decode_packet(data)
                if frames is not None:
                    for frame in frames:
                        self._buffer.append(frame)
            except socket.timeout:
                continue
            except OSError:
                break

    def _decode_packet(self, raw: bytes) -> Optional[np.ndarray]:
        """Decode a single UDP datagram into (N, 16) float32 array."""
        if len(raw) < self.HEADER_SIZE:
            return None

        seq, n_samples = struct.unpack("<II", raw[:self.HEADER_SIZE])

        # Packet-loss detection
        if self._last_seq >= 0 and seq != self._last_seq + 1:
            gap = seq - self._last_seq - 1
            self._dropped_packets += gap
            print(f"[SixteenMEMSSource] ⚠ {gap} packet(s) dropped "
                  f"(total: {self._dropped_packets})")
        self._last_seq = seq

        payload = raw[self.HEADER_SIZE:]
        if self.sample_format == "int16":
            samples = np.frombuffer(payload, dtype=np.int16)
            samples = samples.astype(np.float32) / 32768.0
        else:
            samples = np.frombuffer(payload, dtype=np.float32)

        # Reshape to (n_frames, 16)
        n_frames = len(samples) // self.CHANNELS
        if n_frames == 0:
            return None
        return samples[:n_frames * self.CHANNELS].reshape(n_frames,
                                                          self.CHANNELS)

    # ------------------------------------------------------------------
    def read_chunk(self, frames: int = 1024) -> np.ndarray:
        if not self.is_running:
            raise RuntimeError("Source not connected. Call connect() first.")

        available = len(self._buffer)
        n = min(frames, available)
        if n == 0:
            return np.zeros((frames, self.CHANNELS), dtype=np.float32)

        out = np.array([self._buffer.popleft() for _ in range(n)])
        # If we got fewer frames than requested, zero-pad
        if out.shape[0] < frames:
            pad = np.zeros((frames - out.shape[0], self.CHANNELS),
                           dtype=np.float32)
            out = np.vstack([out, pad])
        return out

    def stop(self) -> None:
        self.is_running = False
        if self._sock is not None:
            self._sock.close()
            self._sock = None
        if self._recv_thread is not None:
            self._recv_thread.join(timeout=2)
            self._recv_thread = None

    def get_info(self) -> Dict[str, Any]:
        return {
            "type": "16mems_orange_pi",
            "host": self.host,
            "port": self.port,
            "sample_rate": self.sample_rate,
            "channels": self.CHANNELS,
            "buffer_len": len(self._buffer),
            "dropped_packets": self._dropped_packets,
            "sample_format": self.sample_format,
        }
