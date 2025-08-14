"""
Voice Activity Detection module.
Handles speech detection and utterance segmentation.
"""

from typing import Generator, List
import numpy as np
import webrtcvad
from config import SAMPLE_RATE, SILENCE_THRESHOLD, VAD_AGGRESSIVENESS, MIN_UTTERANCE_LENGTH, CHUNK_DURATION_SECONDS
from utils.logger import logger


class VoiceActivityDetector:
    """Handles voice activity detection and utterance segmentation."""
    
    def __init__(self, use_vad: bool = True):
        self.use_vad = use_vad
        self.vad = webrtcvad.Vad(VAD_AGGRESSIVENESS) if use_vad else None
        
        # State for utterance tracking
        self.current_utterance: List[np.ndarray] = []
        self.silent_frames = 0
        self.in_speech = False
    
    def process_frame(self, audio_frame: np.ndarray) -> Generator[np.ndarray, None, None]:
        """
        Process an audio frame and yield complete utterances.
        
        Args:
            audio_frame: Audio frame as int16 array
            
        Yields:
            Complete utterances as float32 arrays normalized to [-1, 1]
        """
        if self.use_vad:
            yield from self._process_with_vad(audio_frame)
        else:
            yield from self._process_without_vad(audio_frame)
    
    def _process_with_vad(self, audio_frame: np.ndarray):
        """Process audio frame using voice activity detection."""
        try:
            is_speech = self.vad.is_speech(audio_frame.tobytes(), SAMPLE_RATE)
            
            if is_speech:
                self.current_utterance.append(audio_frame)
                self.silent_frames = 0
                self.in_speech = True
            else:
                if self.in_speech:
                    self.silent_frames += 1
                    self.current_utterance.append(audio_frame)
                    
                    # End utterance after enough silence
                    if self.silent_frames >= SILENCE_THRESHOLD:
                        utterance = self._finalize_utterance()
                        if utterance is not None:
                            yield utterance
        except Exception as e:
            logger.error(f"VAD processing error: {e}")
    
    def _process_without_vad(self, audio_frame: np.ndarray):
        """Process audio frame without VAD (time-based chunking)."""
        self.current_utterance.append(audio_frame)
        
        # Yield chunk when it reaches the target duration
        total_samples = sum(len(frame) for frame in self.current_utterance)
        if total_samples >= SAMPLE_RATE * CHUNK_DURATION_SECONDS:
            utterance = self._finalize_utterance()
            if utterance is not None:
                yield utterance
    
    def _finalize_utterance(self) -> np.ndarray | None:
        """Convert current utterance to normalized float array."""
        if not self.current_utterance:
            return None
        
        # Concatenate all frames in the utterance
        utterance_int16 = np.concatenate(self.current_utterance)
        
        # Check minimum length
        if len(utterance_int16) < MIN_UTTERANCE_LENGTH:
            self._reset_utterance()
            return None
        
        # Convert to float32 normalized to [-1, 1]
        utterance = utterance_int16.astype(np.float32) / 32767.0
        self._reset_utterance()
        return utterance
    
    def _reset_utterance(self):
        """Reset utterance tracking state."""
        self.current_utterance = []
        self.silent_frames = 0
        self.in_speech = False
