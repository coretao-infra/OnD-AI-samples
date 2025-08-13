#!/usr/bin/env python3
"""
Windows On-Device AI Lab: Live Captions
Real-time speech transcription using OpenAI Whisper models.
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
import whisper
from utils.enhanced_ui import EnhancedXTreeUI

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
                # Get audio frame from queue with shorter timeout for better responsiveness
                audio_frame = self.audio_queue.get(timeout=0.05)
                
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
                # No audio available right now, that's OK
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
        # Load OpenAI Whisper model
        print(f"Loading Whisper model: {model_size}")
        self.model = whisper.load_model(model_size)
        print("Model loaded successfully")
        self.audio_capture = AudioCapture(mic_index, use_vad)
        self.running = False
        self.transcript_history = []
        self.ui = EnhancedXTreeUI(refresh_per_second=10, height=24)

    def start_recording(self):
        """Start audio recording."""
        try:
            self.audio_capture.start_capture()
            self.ui.start_capture()
            self.ui.set_live_audio("🎤 Recording started - listening for speech...")
        except Exception as e:
            self.ui.set_live_audio(f"❌ Failed to start recording: {str(e)}")

    def stop_recording(self):
        """Stop audio recording."""
        self.audio_capture.stop_capture()
        self.ui.stop_capture()
        self.ui.set_live_audio("⏸️ Recording stopped")

    def toggle_recording(self):
        """Toggle recording state."""
        if self.audio_capture.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def transcribe_audio(self, audio: np.ndarray) -> str:
        try:
            # Use OpenAI Whisper transcription
            result = self.model.transcribe(
                audio,
                language=self.language,
                task="transcribe",
                verbose=False
            )
            return result["text"].strip()
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""

    async def run(self):
        self.running = True
        # Don't start capture immediately - wait for user to start it
        
        async def keyboard_handler():
            """Handle keyboard input for controlling the app."""
            # Simplified keyboard handling for cross-platform compatibility
            # In a production app, you'd want to use a proper keyboard library like pynput
            while self.running:
                try:
                    # For now, we'll just handle basic app control
                    await asyncio.sleep(0.1)
                    # Note: Real keyboard handling would require additional libraries
                    # For demo purposes, the user can use Ctrl+C to exit
                except KeyboardInterrupt:
                    self.running = False
                    break
                except asyncio.CancelledError:
                    self.running = False
                    break
        
        async def update_ui_loop():
            while self.running:
                try:
                    # Only calculate VU levels if we're actually capturing
                    if self.audio_capture.is_recording:
                        try:
                            # Get recent audio data for VU calculation using non-blocking approach
                            recent_frames = []
                            
                            # Collect up to 5 recent frames without blocking
                            for _ in range(min(5, self.audio_capture.audio_queue.qsize())):
                                try:
                                    frame = self.audio_capture.audio_queue.get_nowait()
                                    recent_frames.append(frame)
                                    # Put frame back for processing
                                    self.audio_capture.audio_queue.put_nowait(frame)
                                except:
                                    break
                            
                            if recent_frames:
                                # Calculate VU levels from recent audio
                                combined_audio = np.concatenate(recent_frames)
                                rms_level = np.sqrt(np.mean(combined_audio.astype(np.float32)**2))
                                # Simulate stereo by adding slight variation
                                left_level = min(1.0, rms_level * 50)  # Scale for visualization
                                right_level = min(1.0, rms_level * 48)  # Slight difference for stereo effect
                                self.ui.update_vu([left_level, right_level])
                            else:
                                # No audio, show silence
                                self.ui.update_vu([0.0, 0.0])
                        except:
                            # Show silence if audio calculation fails
                            self.ui.update_vu([0.0, 0.0])
                    else:
                        # Not recording, show silence
                        self.ui.update_vu([0.0, 0.0])
                    
                    await asyncio.sleep(0.1)
                except asyncio.CancelledError:
                    self.running = False
                    break

        async def process_audio_loop():
            try:
                while self.running:
                    try:
                        if self.audio_capture.is_recording:
                            # Instead of using the generator, check the queue directly
                            try:
                                # Try to get audio data without blocking
                                if not self.audio_capture.audio_queue.empty():
                                    audio_frame = self.audio_capture.audio_queue.get_nowait()
                                    
                                    # Process the frame (simplified VAD approach)
                                    if self.audio_capture.use_vad:
                                        is_speech = self.audio_capture.vad.is_speech(audio_frame.tobytes(), SAMPLE_RATE)
                                        
                                        if is_speech:
                                            self.audio_capture.current_utterance.extend(audio_frame)
                                            self.audio_capture.silent_frames = 0
                                            self.audio_capture.in_speech = True
                                        else:
                                            if self.audio_capture.in_speech:
                                                self.audio_capture.silent_frames += 1
                                                self.audio_capture.current_utterance.extend(audio_frame)
                                                
                                                # End utterance after enough silence
                                                if self.audio_capture.silent_frames >= SILENCE_THRESHOLD:
                                                    if len(self.audio_capture.current_utterance) > SAMPLE_RATE:
                                                        utterance = np.array(self.audio_capture.current_utterance, dtype=np.float32) / 32767.0
                                                        
                                                        # Process the utterance
                                                        self.ui.set_live_audio("🎙️ Processing speech...")
                                                        text = self.transcribe_audio(utterance)
                                                        if text:
                                                            self.ui.add_transcription(f"[{time.strftime('%H:%M:%S')}] {text}")
                                                            self.ui.set_live_audio("✓ Speech processed successfully")
                                                        else:
                                                            self.ui.set_live_audio("⚠️ No speech detected in audio")
                                                        
                                                        # Clear status after a moment
                                                        await asyncio.sleep(0.5)
                                                        if self.audio_capture.is_recording:
                                                            self.ui.set_live_audio("🎤 Listening for speech...")
                                                    
                                                    # Reset for next utterance
                                                    self.audio_capture.current_utterance = []
                                                    self.audio_capture.silent_frames = 0
                                                    self.audio_capture.in_speech = False
                                    else:
                                        # No VAD - simpler approach
                                        self.audio_capture.current_utterance.extend(audio_frame)
                                        if len(self.audio_capture.current_utterance) >= SAMPLE_RATE * 3:  # 3 seconds
                                            utterance = np.array(self.audio_capture.current_utterance, dtype=np.float32) / 32767.0
                                            
                                            # Process the utterance
                                            self.ui.set_live_audio("🎙️ Processing speech...")
                                            text = self.transcribe_audio(utterance)
                                            if text:
                                                self.ui.add_transcription(f"[{time.strftime('%H:%M:%S')}] {text}")
                                                self.ui.set_live_audio("✓ Speech processed")
                                            else:
                                                self.ui.set_live_audio("⚠️ No speech detected")
                                            
                                            # Clear and reset
                                            await asyncio.sleep(0.5)
                                            self.audio_capture.current_utterance = []
                                            if self.audio_capture.is_recording:
                                                self.ui.set_live_audio("🎤 Listening for speech...")
                                else:
                                    # No audio data available, just wait
                                    await asyncio.sleep(0.01)
                                    
                            except Exception as e:
                                self.ui.set_live_audio(f"⚠️ Audio processing issue: {str(e)}")
                                await asyncio.sleep(0.1)
                        else:
                            # Not recording, just wait
                            await asyncio.sleep(0.1)
                    except asyncio.CancelledError:
                        self.running = False
                        break
                        
            except Exception as e:
                self.ui.set_live_audio(f"❌ Audio processing error: {str(e)}")
            finally:
                if self.audio_capture.is_recording:
                    self.audio_capture.stop_capture()
                self.ui.stop()

        # Set initial status - ready to start
        self.ui.set_live_audio("Ready to start recording. Use app controls to begin.")
        self.ui.add_transcription("Welcome to Live Captions! The UI is ready.")
        self.ui.add_transcription("Note: Keyboard controls in terminal apps require special handling.")
        self.ui.add_transcription("For demo purposes, you can start recording programmatically.")
        
        # For demo purposes, let's auto-start after a few seconds
        async def demo_auto_start():
            await asyncio.sleep(3)
            if self.running:
                self.start_recording()
        
        try:
            await asyncio.gather(
                self.ui.run(), 
                update_ui_loop(), 
                process_audio_loop(),
                keyboard_handler(),
                demo_auto_start(),
                return_exceptions=True
            )
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            self.running = False
        except Exception as e:
            print(f"❌ Application error: {e}")
        finally:
            if self.audio_capture.is_recording:
                self.audio_capture.stop_capture()
            self.ui.stop()


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
    parser = argparse.ArgumentParser(description="Live Captions using OpenAI Whisper")
    parser.add_argument("--model-size", choices=["tiny", "base", "small", "medium", "large"], 
                       default="tiny", help="Whisper model size")
    parser.add_argument("--language", help="Language code (e.g., en, es, fr)")
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
        device="cpu",  # OpenAI Whisper handles device internally
        compute_type="int8",  # Not used with OpenAI Whisper but kept for compatibility
        mic_index=args.mic_index,
        use_vad=not args.no_vad
    )

    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\n✅ Application stopped by user")
    except Exception as e:
        print(f"❌ Application failed: {e}")


if __name__ == "__main__":
    main()
