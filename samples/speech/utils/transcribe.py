"""
Transcription module for handling Whisper model interactions.
Isolates all Whisper-related concerns including output capture.
"""

import sys
import asyncio
import whisper
import numpy as np
from contextlib import contextmanager
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from .logger import logger


class WhisperTranscriber:
    """Handles OpenAI Whisper transcription with output capture."""
    
    def __init__(self, model_size: str = "tiny", language: Optional[str] = None, 
                 device: str = "cpu", compute_type: str = "int8"):
        """
        Initialize the Whisper transcriber.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            language: Language code (e.g., en, es, fr). None for auto-detection.
            device: Device for inference (not used with OpenAI Whisper)
            compute_type: Compute type (not used with OpenAI Whisper)
        """
        self.model_size = model_size
        self.language = language
        self.device = device  # Kept for compatibility
        self.compute_type = compute_type  # Kept for compatibility
        
        # Thread pool for async transcription
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="whisper")
        
        # Load the Whisper model with output capture
        with self._capture_whisper_output():
            logger.info(f"Loading Whisper model: {model_size}")
            self.model = whisper.load_model(model_size)
            logger.info("Model loaded successfully")
    
    @contextmanager
    def _capture_whisper_output(self):
        """
        Context manager to capture stdout/stderr from Whisper operations.
        Prevents library output from interfering with the rich UI.
        """
        class LoggerWriter:
            def __init__(self, level):
                self.level = level
            
            def write(self, message):
                # Only log non-empty lines
                for line in message.rstrip().splitlines():
                    if line.strip():
                        self.level(f"[WHISPER] {line.rstrip()}")
            
            def flush(self):
                pass
        
        # Store original stdout/stderr
        old_stdout, old_stderr = sys.stdout, sys.stderr
        
        # Redirect to logger
        sys.stdout = LoggerWriter(logger.info)
        sys.stderr = LoggerWriter(logger.error)
        
        try:
            yield
        finally:
            # Always restore original stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    def transcribe(self, audio: np.ndarray) -> str:
        """
        Transcribe audio using Whisper with output capture.
        
        Args:
            audio: Audio data as numpy array (16kHz, float32)
            
        Returns:
            Transcribed text or empty string on error
        """
        try:
            # Capture all Whisper output to prevent UI interference
            with self._capture_whisper_output():
                result = self.model.transcribe(
                    audio,
                    language=self.language,
                    task="transcribe",
                    verbose=False
                )
            return result["text"].strip()
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
    
    async def transcribe_async(self, audio: np.ndarray) -> str:
        """
        Asynchronously transcribe audio using Whisper.
        
        Args:
            audio: Audio data as numpy array (16kHz, float32)
            
        Returns:
            Transcribed text or empty string on error
        """
        def _transcribe_with_capture(audio_data):
            """Wrapper to ensure output capture works in thread pool."""
            try:
                # Capture all Whisper output to prevent UI interference
                with self._capture_whisper_output():
                    result = self.model.transcribe(
                        audio_data,
                        language=self.language,
                        task="transcribe",
                        verbose=False
                    )
                return result["text"].strip()
            except Exception as e:
                logger.error(f"Transcription error: {e}")
                return ""
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, _transcribe_with_capture, audio)
    
    def shutdown(self):
        """Shutdown the thread pool executor."""
        self._executor.shutdown(wait=True)
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_size": self.model_size,
            "language": self.language or "auto-detect",
            "device": self.device,
            "compute_type": self.compute_type
        }
