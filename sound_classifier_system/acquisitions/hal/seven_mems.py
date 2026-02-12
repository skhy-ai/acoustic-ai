"""
7-MEMS HISPEED Sound Board Source
===================================
The HISPEED board presents as a high-channel-count ALSA capture device
(7 channels interleaved).  This source uses ``sounddevice`` with the
channel count set to 7 and de-interleaves the raw data into a clean
(N, 7) matrix.
"""

import numpy as np
import sounddevice as sd
from typing import Dict, Any, Optional
from .base import AudioSource


class SevenMEMSSource(AudioSource):
    """
    Capture 7-channel audio from the HISPEED MEMS board.

    Parameters
    ----------
    device_id : int or str or None
        PortAudio device index or substring of the device name
        (e.g. ``"HISPEED"``).
    sample_rate : int
        Sampling frequency (Hz). The HISPEED board may support
        up to 96 kHz – check your board's datasheet.
    blocksize : int
        Frames per read.
    """

    CHANNELS = 7

    def __init__(self, device_id: Optional[int] = None,
                 sample_rate: int = 48000, blocksize: int = 1024):
        super().__init__(sample_rate=sample_rate, channels=self.CHANNELS)
        self.device_id = device_id
        self.blocksize = blocksize
        self._stream: Optional[sd.InputStream] = None

    # ------------------------------------------------------------------
    def connect(self) -> None:
        self._stream = sd.InputStream(
            device=self.device_id,
            samplerate=self.sample_rate,
            channels=self.CHANNELS,
            dtype="float32",
            blocksize=self.blocksize,
        )
        self._stream.start()
        self.is_running = True
        print(f"[SevenMEMSSource] Connected – {self.CHANNELS}ch @ "
              f"{self.sample_rate} Hz")

    def read_chunk(self, frames: int = 1024) -> np.ndarray:
        if self._stream is None or not self.is_running:
            raise RuntimeError("Source not connected. Call connect() first.")
        data, overflowed = self._stream.read(frames)
        if overflowed:
            print("[SevenMEMSSource] ⚠ buffer overflow")
        # data is already (frames, 7) float32 from sounddevice
        return data

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self.is_running = False

    def get_info(self) -> Dict[str, Any]:
        dev = sd.query_devices(self.device_id, kind="input")
        return {
            "type": "7mems_hispeed",
            "device_name": dev["name"],
            "sample_rate": self.sample_rate,
            "channels": self.CHANNELS,
            "blocksize": self.blocksize,
        }

    # ------------------------------------------------------------------
    def get_channel(self, data: np.ndarray, ch: int) -> np.ndarray:
        """Extract a single channel from multi-channel data."""
        if ch < 0 or ch >= self.CHANNELS:
            raise ValueError(f"Channel {ch} out of range [0, {self.CHANNELS})")
        return data[:, ch]
