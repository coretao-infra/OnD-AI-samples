"""
Configuration constants for the Live Captions application.
"""

# Audio Configuration
SAMPLE_RATE = 16000  # Whisper models expect 16kHz
FRAME_DURATION_MS = 30  # WebRTC VAD frame duration in milliseconds
FRAMES_PER_BUFFER = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # 480 samples

# Voice Activity Detection
SILENCE_THRESHOLD = 20  # Number of silent frames to end utterance
VAD_AGGRESSIVENESS = 2  # WebRTC VAD aggressiveness level (0-3)

# Audio Processing
AUDIO_QUEUE_SIZE = 500  # Audio queue buffer size (~15 seconds)
MIN_UTTERANCE_LENGTH = SAMPLE_RATE  # Minimum 1 second for processing
CHUNK_DURATION_SECONDS = 3  # For non-VAD mode processing

# UI Configuration
UI_REFRESH_RATE = 10  # Refreshes per second
UI_HEIGHT = 24  # Terminal height for UI

# VU Meter
VU_BUFFER_FRAMES = 5  # Number of frames to keep for VU calculations
