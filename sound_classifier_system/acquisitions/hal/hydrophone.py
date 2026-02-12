"""
Hydrophone / Standard USB Microphone / Bluetooth Audio Source
==============================================================
Uses ``sounddevice`` (PortAudio) to capture from any OS-enumerated
audio input device – USB hydrophones, built-in mics, Bluetooth
headsets, or ASIO interfaces (Windows, with SDK installed).
"""

import numpy as np
import sounddevice as sd
from typing import Dict, Any, Optional
from .base import AudioSource


class HydrophoneSource(AudioSource):
    """
    Capture audio from any PortAudio-supported device.

    Parameters
    ----------
    device_id : int or str or None
        PortAudio device index or substring of the device name.
        ``None`` uses the system default input.
    sample_rate : int
        Sampling frequency in Hz.
    channels : int
        Number of input channels.
    blocksize : int
        Frames per read (passed to sounddevice).
    """

    def __init__(self, device_id: Optional[int] = None,
                 sample_rate: int = 44100, channels: int = 1,
                 blocksize: int = 1024):
        super().__init__(sample_rate=sample_rate, channels=channels)
        self.device_id = device_id
        self.blocksize = blocksize
        self._stream: Optional[sd.InputStream] = None

    # ------------------------------------------------------------------
    def connect(self) -> None:
        self._stream = sd.InputStream(
            device=self.device_id,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            blocksize=self.blocksize,
        )
        self._stream.start()
        self.is_running = True

    def read_chunk(self, frames: int = 1024) -> np.ndarray:
        if self._stream is None or not self.is_running:
            raise RuntimeError("Source not connected. Call connect() first.")
        data, overflowed = self._stream.read(frames)
        if overflowed:
            print("[HydrophoneSource] ⚠ buffer overflow – frames dropped")
        return data  # shape (frames, channels), float32

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self.is_running = False

    def get_info(self) -> Dict[str, Any]:
        dev = sd.query_devices(self.device_id, kind="input")
        return {
            "type": "hydrophone",
            "device_name": dev["name"],
            "device_index": dev["index"] if isinstance(dev, dict) else self.device_id,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "host_api": dev.get("hostapi"),
        }

    # ------------------------------------------------------------------
    @staticmethod
    def list_devices() -> list:
        """Return all available PortAudio input devices."""
        devs = sd.query_devices()
        return [
            {"index": i, "name": d["name"], "channels": d["max_input_channels"],
             "default_sr": d["default_samplerate"]}
            for i, d in enumerate(devs)
            if d["max_input_channels"] > 0
        ]
