"""
Hardware Abstraction Layer – Base Class
=======================================
Every hardware source (hydrophone, MEMS array, Bluetooth mic, ASIO device)
inherits from ``AudioSource`` and implements four methods:
    connect  – open the device / socket
    read_chunk – return (N, C) numpy float32 array
    stop     – release resources
    get_info – diagnostic dict
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import numpy as np


class AudioSource(ABC):
    """Abstract base class for all audio capture sources."""

    def __init__(self, sample_rate: int = 44100, channels: int = 1,
                 dtype: np.dtype = np.float32):
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.is_running = False

    # ---- lifecycle ---------------------------------------------------
    @abstractmethod
    def connect(self) -> None:
        """Open the device / socket and prepare for reading."""
        ...

    @abstractmethod
    def read_chunk(self, frames: int = 1024) -> np.ndarray:
        """
        Return the next chunk of audio.

        Returns
        -------
        np.ndarray of shape ``(frames, channels)`` with dtype float32
        normalised to [-1, 1].
        """
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop capture and release the underlying resource."""
        ...

    # ---- diagnostics -------------------------------------------------
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Return a JSON-serialisable dict with device diagnostics."""
        ...

    # ---- helpers -----------------------------------------------------
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *exc):
        self.stop()
