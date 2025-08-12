#!/usr/bin/env python3
"""
Windows On-Device AI Lab: Live Captions
Real-time speech transcription using Whisper models via faster-whisper.
"""


import argparse
import asyncio
import queue
import random
import sys
import time
from typing import Generator, Optional, Tuple

import numpy as np
import sounddevice as sd
import webrtcvad
from faster_whisper import WhisperModel
from utils.ui import XTreeUI

# --- Constants ---
SAMPLE_RATE = 16000  # Whisper models expect 16kHz
FRAME_DURATION_MS = 30  # WebRTC VAD frame duration
FRAMES_PER_BUFFER = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # 480 samples
SILENCE_THRESHOLD = 20  # Number of silent frames to end utterance
AUDIO_QUEUE_SIZE = 100


class AudioCapture:
    """Handles microphone audio capture and VAD processing."""
    
    def __init__(self, device_index: Optional[int] = None, use_vad: bool = True):
        self.device_index = device_index
        self.use_vad = use_vad
        self.vad = webrtcvad.Vad(2) if use_vad else None  # Aggressiveness level 2
        self.audio_queue = queue.Queue(maxsize=AUDIO_QUEUE_SIZE)
        self.is_recording = False
        self.stream = None
        # VAD state
        self.current_utterance = []
        self.silent_frames = 0
        self.in_speech = False
    
    def audio_callback(self, indata, frames, time, status):
        """Called by sounddevice for each audio frame."""
        if status:
            print(f"Audio callback status: {status}")
        
        # Convert to int16 for VAD and queue for processing
        audio_int16 = (indata[:, 0] * 32767).astype(np.int16)
        
        # Log audio levels periodically
        if hasattr(self, '_callback_count'):
            self._callback_count += 1
        else:
            self._callback_count = 1
            
        if self._callback_count % 50 == 0:  # Every ~1.5 seconds at 30ms frames
            max_amplitude = np.max(np.abs(audio_int16))
            print(f"Audio level: {max_amplitude} (frames processed: {self._callback_count})")
        
        try:
            self.audio_queue.put_nowait(audio_int16)
        except queue.Full:
            print("Warning: Audio queue full, dropping frame")
            pass
    
    def start_capture(self):
        """Start audio capture."""
        print("🎙️ Starting audio capture...")
        self.is_recording = True

        # Use specified device or system default input device
        device_to_use = self.device_index
        if device_to_use is None:
            # Get the actual default input device from the system
            try:
                device_to_use = sd.default.device[0]  # [0] is input, [1] is output
                if device_to_use == -1:
                    print("ERROR: No default input device configured.")
                    print("Please run with --list-devices to see available devices")
                    print("Then select a specific device with --mic-index NUMBER")
                    raise ValueError("No default input device configured")
                print(f"Using system default input device: {device_to_use}")
            except Exception as e:
                print(f"ERROR: Could not get default input device: {e}")
                print("Please run with --list-devices to see available devices")
                print("Then select a specific device with --mic-index NUMBER")
                raise RuntimeError("No default input device available")

        # Get device info for display
        device_info = sd.query_devices(device_to_use)
        device_name = device_info['name']

        # Force 16kHz for Whisper and VAD compatibility
        target_rate = SAMPLE_RATE  # Always use 16kHz

        print(f"✓ Using device: {device_name}")
        print(f"Recording at 16kHz (Whisper/VAD compatible)")
        # Calculate frame size for 16kHz
        frames_per_buffer = int(target_rate * FRAME_DURATION_MS / 1000)
        print(f"Frame size: {frames_per_buffer} samples ({FRAME_DURATION_MS}ms)")
        try:
            self.stream = sd.InputStream(
                samplerate=target_rate,  # Force 16kHz
                channels=1,
                dtype=np.float32,
                blocksize=frames_per_buffer,
                device=device_to_use,
                callback=self.audio_callback
            )
            self.stream.start()
            print("✓ Audio stream started successfully!")
        except Exception as e:
            print(f"✗ Failed to start audio stream: {e}")
            raise
        print(f"Started audio capture (device: {device_to_use} - {device_name})")
    
    def stop_capture(self):
        """Stop audio capture."""
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        print("Stopped audio capture")
    
    def get_utterances(self) -> Generator[np.ndarray, None, None]:
        """Generator that yields complete utterances."""
        while self.is_recording:
            try:
                # Get audio frame from queue
                audio_frame = self.audio_queue.get(timeout=0.1)
                
                if self.use_vad:
                    # Use VAD to detect speech
                    is_speech = self.vad.is_speech(audio_frame.tobytes(), SAMPLE_RATE)
                    
                    if is_speech:
                        self.current_utterance.extend(audio_frame)
                        self.silent_frames = 0
                        self.in_speech = True
                    else:
                        if self.in_speech:
                            self.silent_frames += 1
                            self.current_utterance.extend(audio_frame)
                            
                            # End utterance after enough silence
                            if self.silent_frames >= SILENCE_THRESHOLD:
                                if len(self.current_utterance) > SAMPLE_RATE:  # At least 1 second
                                    utterance = np.array(self.current_utterance, dtype=np.float32) / 32767.0
                                    yield utterance
                                
                                # Reset for next utterance
                                self.current_utterance = []
                                self.silent_frames = 0
                                self.in_speech = False
                else:
                    # No VAD - accumulate audio and yield chunks periodically
                    self.current_utterance.extend(audio_frame)
                    if len(self.current_utterance) >= SAMPLE_RATE * 3:  # 3 seconds
                        utterance = np.array(self.current_utterance, dtype=np.float32) / 32767.0
                        yield utterance
                        self.current_utterance = []
                        
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing audio: {e}")
                break



class LiveCaptionsApp:
    """Main application for live speech captioning with async XTreeUI."""
    def __init__(self, model_size: str = "tiny", language: Optional[str] = None, 
                 device: str = "cpu", compute_type: str = "int8", 
                 mic_index: Optional[int] = None, use_vad: bool = True):
        self.model_size = model_size
        self.language = language
        self.device = device
        self.compute_type = compute_type
        self.use_vad = use_vad
        self.model = WhisperModel(
            model_size, 
            device=device, 
            compute_type=compute_type
        )
        self.audio_capture = AudioCapture(mic_index, use_vad)
        self.running = False
        self.transcript_history = []
        self.ui = XTreeUI(refresh_per_second=10, height=24)

    def transcribe_audio(self, audio: np.ndarray) -> str:
        try:
            segments, info = self.model.transcribe(
                audio,
                language=self.language,
                beam_size=1,
                word_timestamps=False
            )
            text = " ".join(segment.text.strip() for segment in segments)
            return text.strip()
        except Exception as e:
            return ""

    async def run(self):
        self.running = True
        self.audio_capture.start_capture()

        async def update_ui_loop():
            while self.running:
                # Simulate VU meter with random values (replace with real audio levels if available)
                # For real VU, you would analyze the most recent audio frame
                self.ui.update_vu([random.random(), random.random()])
                await asyncio.sleep(0.1)

        async def process_audio_loop():
            try:
                for utterance in self.audio_capture.get_utterances():
                    if not self.running:
                        break
                    self.ui.set_live_audio("Processing...")
                    text = self.transcribe_audio(utterance)
                    self.ui.set_live_audio("")
                    if text:
                        self.ui.add_transcription(text)
                    else:
                        self.ui.add_transcription("[No speech detected]")
            except Exception:
                pass
            finally:
                self.running = False
                self.audio_capture.stop_capture()
                self.ui.stop()

        await asyncio.gather(self.ui.run(), update_ui_loop(), process_audio_loop())


def list_audio_devices():
    """List available audio input devices."""
    print("Available audio input devices:")
    devices = sd.query_devices()
    found = False
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"  {i}: {device['name']} (inputs: {device['max_input_channels']})")
            found = True
    
    if not found:
        print("  No audio input devices found!")
    
    print("\nTo use a specific device:")
    print("  python app.py --mic-index NUMBER")



def main():
    parser = argparse.ArgumentParser(description="Live Captions using Whisper")
    parser.add_argument("--model-size", choices=["tiny", "base", "small", "medium", "large"], 
                       default="tiny", help="Whisper model size")
    parser.add_argument("--language", help="Language code (e.g., en, es, fr)")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu", 
                       help="Processing device")
    parser.add_argument("--compute-type", choices=["int8", "int8_float16", "float16", "float32"], 
                       default="int8", help="Compute precision")
    parser.add_argument("--mic-index", type=int, help="Microphone device index")
    parser.add_argument("--no-vad", action="store_true", help="Disable voice activity detection")
    parser.add_argument("--list-devices", action="store_true", help="List audio devices and exit")

    args = parser.parse_args()

    if args.list_devices:
        list_audio_devices()
        return

    app = LiveCaptionsApp(
        model_size=args.model_size,
        language=args.language,
        device=args.device,
        compute_type=args.compute_type,
        mic_index=args.mic_index,
        use_vad=not args.no_vad
    )

    asyncio.run(app.run())


if __name__ == "__main__":
    main()
