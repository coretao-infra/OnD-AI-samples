"""
Audio processing coordinator - orchestrates audio capture, VAD, and transcription.
This separates the complex async audio processing logic from the main app.
"""

import asyncio
import time
from typing import Optional
import numpy as np
from utils.audio_capture import AudioCapture
from utils.voice_activity import VoiceActivityDetector
from utils.transcribe import WhisperTranscriber
from utils.logger import logger


class AudioProcessor:
    """Coordinates audio capture, voice activity detection, and transcription."""
    
    def __init__(self, transcriber: WhisperTranscriber, mic_index: Optional[int] = None, use_vad: bool = True):
        self.transcriber = transcriber
        self.audio_capture = AudioCapture(mic_index)
        self.voice_detector = VoiceActivityDetector(use_vad)
        self.is_running = False
        
        # Callbacks for UI updates
        self.on_status_update = None
        self.on_transcription = None
    
    def set_callbacks(self, status_callback=None, transcription_callback=None):
        """Set callback functions for UI updates."""
        self.on_status_update = status_callback
        self.on_transcription = transcription_callback
    
    def start_recording(self):
        """Start audio recording."""
        try:
            self.audio_capture.start_capture()
            self._update_status("🎤 Recording started - listening for speech...")
        except Exception as e:
            self._update_status(f"❌ Failed to start recording: {str(e)}")
            raise
    
    def stop_recording(self):
        """Stop audio recording."""
        self.audio_capture.stop_capture()
        self._update_status("⏸️ Recording stopped")
    
    def get_vu_levels(self):
        """Get current audio levels for VU meter."""
        if self.audio_capture.is_recording:
            return self.audio_capture.get_vu_levels()
        return [0.0, 0.0]
    
    async def process_audio_loop(self):
        """Main audio processing loop - handles VAD and transcription."""
        self.is_running = True
        self._update_status("Ready to start recording...")
        
        try:
            while self.is_running:
                if not self.audio_capture.is_recording:
                    await asyncio.sleep(0.1)
                    continue
                
                # Get next audio frame
                audio_frame = self.audio_capture.get_audio_frame()
                if audio_frame is None:
                    await asyncio.sleep(0.01)
                    continue
                
                # Process frame through VAD and get any complete utterances
                for utterance in self.voice_detector.process_frame(audio_frame):
                    await self._process_utterance(utterance)
                    
        except Exception as e:
            self._update_status(f"❌ Audio processing error: {str(e)}")
            logger.error(f"Audio processing error: {e}")
        finally:
            self.stop_recording()
    
    async def _process_utterance(self, utterance: np.ndarray):
        """Process a complete utterance through transcription."""
        try:
            self._update_status("🎙️ Processing speech...")
            
            # Transcribe the utterance
            text = await self.transcriber.transcribe_async(utterance)
            
            if text:
                # Add timestamp and send to UI
                timestamp = time.strftime('%H:%M:%S')
                self._add_transcription(f"[{timestamp}] {text}")
                self._update_status("✓ Speech processed successfully")
            else:
                self._update_status("⚠️ No speech detected in audio")
            
            # Clear status after a moment
            await asyncio.sleep(0.5)
            if self.audio_capture.is_recording:
                self._update_status("🎤 Listening for speech...")
                
        except Exception as e:
            self._update_status(f"⚠️ Transcription error: {str(e)}")
            logger.error(f"Transcription error: {e}")
    
    def stop(self):
        """Stop the audio processor."""
        self.is_running = False
        self.stop_recording()
    
    def _update_status(self, message: str):
        """Update status through callback."""
        if self.on_status_update:
            self.on_status_update(message)
    
    def _add_transcription(self, text: str):
        """Add transcription through callback."""
        if self.on_transcription:
            self.on_transcription(text)
