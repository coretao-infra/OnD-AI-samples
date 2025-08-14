"""
Audio capture module - handles microphone input only.
Separated from audio processing for better modularity.
"""

import queue
from typing import Optional
import numpy as np
import sounddevice as sd
from config import SAMPLE_RATE, FRAME_DURATION_MS, FRAMES_PER_BUFFER, AUDIO_QUEUE_SIZE, VU_BUFFER_FRAMES
from utils.logger import logger


class AudioCapture:
    """Simple audio capture from microphone - single responsibility."""
    
    def __init__(self, device_index: Optional[int] = None):
        self.device_index = device_index
        self.audio_queue = queue.Queue(maxsize=AUDIO_QUEUE_SIZE)
        self.is_recording = False
        self.stream = None
        
        # VU meter data (separate circular buffer)
        self.vu_buffer = np.zeros(FRAMES_PER_BUFFER * VU_BUFFER_FRAMES)
        self.vu_write_pos = 0
        self._callback_count = 0
    
    def audio_callback(self, indata, frames, time, status):
        """Called by sounddevice for each audio frame."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Convert to int16 for processing
        audio_int16 = (indata[:, 0] * 32767).astype(np.int16)
        
        # Update VU buffer for level monitoring
        self._update_vu_buffer(audio_int16)
        
        # Log audio levels periodically for debugging
        self._log_audio_levels(audio_int16)
        
        # Queue audio for processing
        try:
            self.audio_queue.put_nowait(audio_int16)
        except queue.Full:
            logger.warning("Audio queue full, dropping frame")
    
    def _update_vu_buffer(self, audio_data):
        """Update the circular VU buffer."""
        frame_size = len(audio_data)
        if self.vu_write_pos + frame_size > len(self.vu_buffer):
            self.vu_write_pos = 0  # Wrap around
        self.vu_buffer[self.vu_write_pos:self.vu_write_pos + frame_size] = audio_data
        self.vu_write_pos += frame_size
    
    def _log_audio_levels(self, audio_data):
        """Log audio levels periodically for debugging."""
        self._callback_count += 1
        if self._callback_count % 50 == 0:  # Every ~1.5 seconds
            max_amplitude = np.max(np.abs(audio_data))
            logger.info(f"Audio level: {max_amplitude} (frames: {self._callback_count})")
    
    def start_capture(self):
        """Start audio capture from microphone."""
        logger.info("🎙️ Starting audio capture...")
        
        # Determine device to use
        device_to_use = self._get_input_device()
        device_info = sd.query_devices(device_to_use)
        device_name = device_info['name']
        
        logger.info(f"✓ Using device: {device_name}")
        logger.info(f"Recording at {SAMPLE_RATE}Hz (Whisper compatible)")
        
        try:
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype=np.float32,
                blocksize=FRAMES_PER_BUFFER,
                device=device_to_use,
                callback=self.audio_callback
            )
            self.stream.start()
            self.is_recording = True
            logger.info("✓ Audio capture started successfully!")
        except Exception as e:
            logger.error(f"✗ Failed to start audio capture: {e}")
            raise
    
    def _get_input_device(self):
        """Get the input device to use."""
        if self.device_index is not None:
            return self.device_index
        
        # Use system default input device
        try:
            device_to_use = sd.default.device[0]  # Input device
            if device_to_use == -1:
                raise ValueError("No default input device configured")
            logger.info(f"Using system default input device: {device_to_use}")
            return device_to_use
        except Exception as e:
            logger.error(f"Could not get default input device: {e}")
            logger.error("Run with --list-devices to see available devices")
            raise RuntimeError("No default input device available")
    
    def stop_capture(self):
        """Stop audio capture."""
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            logger.info("Audio capture stopped")
    
    def get_vu_levels(self):
        """Get current VU levels for display."""
        try:
            # Calculate RMS from the circular buffer
            rms_level = np.sqrt(np.mean((self.vu_buffer.astype(np.float32) / 32767.0) ** 2))
            # Simulate stereo with slight variation
            left_level = min(1.0, rms_level * 50)
            right_level = min(1.0, rms_level * 48)
            return [left_level, right_level]
        except:
            return [0.0, 0.0]
    
    def get_audio_frame(self, timeout=0.05):
        """Get next audio frame from queue (non-blocking)."""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
