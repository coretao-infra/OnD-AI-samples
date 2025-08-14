#!/usr/bin/env python3
"""
On-Device AI Lab: Live Captions Demo

This script demonstrates real-time speech-to-text transcription using OpenAI Whisper models,
with voice activity detection (VAD) and a modern terminal UI. It is designed for learning and
demonstration purposes, with clear comments for those new to Python or AI.
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
from utils.enhanced_ui import EnhancedXTreeUI
from utils.logger import logger
from utils.transcribe import WhisperTranscriber

# --- Constants ---
SAMPLE_RATE = 16000  # Whisper models expect 16kHz audio
FRAME_DURATION_MS = 30  # Each audio frame is 30ms (good for VAD)
FRAMES_PER_BUFFER = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # 480 samples per frame
SILENCE_THRESHOLD = 20  # Number of silent frames to end an utterance
AUDIO_QUEUE_SIZE = 500  # Buffer size for audio frames (about 15 seconds)

class AudioCapture:
    """
    Handles microphone audio capture and (optionally) voice activity detection (VAD).
    - Captures audio from the selected input device.
    - Segments speech using VAD (WebRTC) to detect when someone is speaking.
    - Maintains a VU meter buffer for real-time audio level visualization.
    """
    def __init__(self, device_index: Optional[int] = None, use_vad: bool = True):
        self.device_index = device_index
        self.use_vad = use_vad
        self.vad = webrtcvad.Vad(2) if use_vad else None  # Aggressiveness: 0-3 (higher = more filtering)
        self.audio_queue = queue.Queue(maxsize=AUDIO_QUEUE_SIZE)
        self.is_recording = False
        self.stream = None
        # VAD state
        self.current_utterance = []  # Buffer for the current speech segment
        self.silent_frames = 0
        self.in_speech = False
        # VU meter data (for UI)
        self.vu_buffer = np.zeros(FRAMES_PER_BUFFER * 5)  # Last 5 frames for VU
        self.vu_write_pos = 0
    
    def audio_callback(self, indata, frames, time, status):
        """
        Called by sounddevice for each audio frame.
        - Converts audio to int16 for VAD and processing.
        - Updates the VU meter buffer.
        - Puts audio frames into the processing queue.
        """
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Convert float32 audio to int16 (required by VAD)
        audio_int16 = (indata[:, 0] * 32767).astype(np.int16)
        
        # Update VU buffer (for real-time audio level display)
        frame_size = len(audio_int16)
        if self.vu_write_pos + frame_size > len(self.vu_buffer):
            self.vu_write_pos = 0  # Wrap around
        self.vu_buffer[self.vu_write_pos:self.vu_write_pos + frame_size] = audio_int16
        self.vu_write_pos += frame_size
        
        # Log audio levels periodically (for debugging)
        if hasattr(self, '_callback_count'):
            self._callback_count += 1
        else:
            self._callback_count = 1
        if self._callback_count % 50 == 0:  # Every ~1.5 seconds
            max_amplitude = np.max(np.abs(audio_int16))
            logger.info(f"Audio level: {max_amplitude} (frames processed: {self._callback_count})")
        
        try:
            self.audio_queue.put_nowait(audio_int16)
        except queue.Full:
            logger.warning("Warning: Audio queue full, dropping frame")
            pass
    
    def start_capture(self):
        """
        Start capturing audio from the selected device.
        - Uses the system default input if none specified.
        - Sets up the stream for 16kHz mono audio (required by Whisper and VAD).
        """
        logger.info("🎙️ Starting audio capture...")
        self.is_recording = True
        device_to_use = self.device_index
        if device_to_use is None:
            # Use system default input device
            try:
                device_to_use = sd.default.device[0]  # [0] is input
                if device_to_use == -1:
                    logger.error("ERROR: No default input device configured.")
                    raise ValueError("No default input device configured")
                logger.info(f"Using system default input device: {device_to_use}")
            except Exception as e:
                logger.error(f"ERROR: Could not get default input device: {e}")
                raise RuntimeError("No default input device available")
        device_info = sd.query_devices(device_to_use)
        device_name = device_info['name']
        target_rate = SAMPLE_RATE
        logger.info(f"✓ Using device: {device_name}")
        logger.info(f"Recording at 16kHz (Whisper/VAD compatible)")
        frames_per_buffer = int(target_rate * FRAME_DURATION_MS / 1000)
        logger.info(f"Frame size: {frames_per_buffer} samples ({FRAME_DURATION_MS}ms)")
        try:
            self.stream = sd.InputStream(
                samplerate=target_rate,
                channels=1,
                dtype=np.float32,
                blocksize=frames_per_buffer,
                device=device_to_use,
                callback=self.audio_callback
            )
            self.stream.start()
            logger.info("✓ Audio stream started successfully!")
        except Exception as e:
            logger.error(f"✗ Failed to start audio stream: {e}")
            raise
        logger.info(f"Started audio capture (device: {device_to_use} - {device_name})")
    
    def stop_capture(self):
        """
        Stop audio capture and close the stream.
        """
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        logger.info("Stopped audio capture")
    
    def get_vu_levels(self):
        """
        Calculate the current VU (volume unit) levels for the UI.
        Returns a list of two floats (left/right), but audio is mono so both are the same.
        """
        try:
            rms_level = np.sqrt(np.mean((self.vu_buffer.astype(np.float32) / 32767.0) ** 2))
            left_level = min(1.0, rms_level * 50)
            right_level = min(1.0, rms_level * 48)
            return [left_level, right_level]
        except:
            return [0.0, 0.0]
    
    def get_utterances(self) -> Generator[np.ndarray, None, None]:
        """
        Generator that yields complete speech utterances (as numpy arrays).
        Uses VAD to segment speech from silence.
        """
        while self.is_recording:
            try:
                audio_frame = self.audio_queue.get(timeout=0.05)
                if self.use_vad:
                    is_speech = self.vad.is_speech(audio_frame.tobytes(), SAMPLE_RATE)
                    if is_speech:
                        self.current_utterance.extend(audio_frame)
                        self.silent_frames = 0
                        self.in_speech = True
                    else:
                        if self.in_speech:
                            self.silent_frames += 1
                            self.current_utterance.extend(audio_frame)
                            if self.silent_frames >= SILENCE_THRESHOLD:
                                if len(self.current_utterance) > SAMPLE_RATE:  # At least 1 second
                                    utterance = np.array(self.current_utterance, dtype=np.float32) / 32767.0
                                    yield utterance
                                self.current_utterance = []
                                self.silent_frames = 0
                                self.in_speech = False
                else:
                    # No VAD: yield every 3 seconds
                    self.current_utterance.extend(audio_frame)
                    if len(self.current_utterance) >= SAMPLE_RATE * 3:
                        utterance = np.array(self.current_utterance, dtype=np.float32) / 32767.0
                        yield utterance
                        self.current_utterance = []
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                break

class LiveCaptionsApp:
    """
    Main application class for live speech captioning.
    - Manages audio capture, transcription, and UI updates.
    - Uses async tasks for real-time responsiveness.
    """
    def __init__(self, model_size: str = "tiny", language: Optional[str] = None, 
                 device: str = "cpu", compute_type: str = "int8", 
                 mic_index: Optional[int] = None, use_vad: bool = True):
        # Store configuration
        self.model_size = model_size
        self.language = language
        self.device = device
        self.compute_type = compute_type
        self.use_vad = use_vad
        # Initialize the Whisper transcriber (loads the model)
        self.transcriber = WhisperTranscriber(
            model_size=model_size,
            language=language,
            device=device,
            compute_type=compute_type
        )
        # Set up audio capture
        self.audio_capture = AudioCapture(mic_index, use_vad)
        self.running = False
        self.transcript_history = []
        # Set up the Rich UI
        self.ui = EnhancedXTreeUI(refresh_per_second=10, height=24)

    def start_recording(self):
        """
        Start audio recording and update the UI.
        """
        try:
            self.audio_capture.start_capture()
            self.ui.start_capture()
            self.ui.set_live_audio("🎤 Recording started - listening for speech...")
        except Exception as e:
            self.ui.set_live_audio(f"❌ Failed to start recording: {str(e)}")

    def stop_recording(self):
        """
        Stop audio recording and update the UI.
        """
        self.audio_capture.stop_capture()
        self.ui.stop_capture()
        self.ui.set_live_audio("⏸️ Recording stopped")

    def toggle_recording(self):
        """
        Toggle between recording and stopped states.
        """
        if self.audio_capture.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def transcribe_audio(self, audio: np.ndarray) -> str:
        """
        Transcribe a chunk of audio using the Whisper model.
        """
        return self.transcriber.transcribe(audio)
    
    async def run(self):
        """
        Main async event loop for the app.
        - Runs the UI, audio processing, and keyboard handler concurrently.
        - Handles graceful shutdown on Ctrl+C.
        """
        self.running = True
        
        async def keyboard_handler():
            """
            Handle keyboard input for controlling the app.
            Note: In a real production app, you'd use libraries like 'pynput' for proper keyboard handling.
            For now, this is a simplified handler that mainly waits for Ctrl+C to exit.
            """
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
            """
            Updates the UI continuously (VU meters, status displays, etc.).
            This runs in parallel with audio processing to keep the interface responsive.
            The UI refresh rate is controlled by the sleep interval (currently 10 FPS).
            """
            while self.running:
                try:
                    # Get VU (Volume Unit) levels from the dedicated VU buffer
                    # This is separate from the main audio processing queue to avoid interference
                    if self.audio_capture.is_recording:
                        vu_levels = self.audio_capture.get_vu_levels()
                        self.ui.update_vu(vu_levels)
                    else:
                        # Not recording, show silence (zero levels)
                        self.ui.update_vu([0.0, 0.0])
                    
                    # Sleep briefly to control UI refresh rate and avoid overwhelming the terminal
                    await asyncio.sleep(0.1)  # 10 FPS refresh rate
                except asyncio.CancelledError:
                    self.running = False
                    break

        async def process_audio_loop():
            """
            Main audio processing loop - the heart of the speech recognition system.
            
            This function:
            1. Reads audio frames from the capture queue
            2. Uses Voice Activity Detection (VAD) to identify speech vs. silence
            3. Accumulates speech frames into complete utterances
            4. Sends complete utterances to Whisper for transcription
            5. Updates the UI with transcription results
            
            The VAD approach allows for natural speech segmentation rather than arbitrary time-based chunks.
            """
            try:
                while self.running:
                    try:
                        if self.audio_capture.is_recording:
                            # Check if we have new audio frames to process (non-blocking)
                            try:
                                # Get audio frame from the queue without waiting
                                if not self.audio_capture.audio_queue.empty():
                                    audio_frame = self.audio_capture.audio_queue.get_nowait()
                                    
                                    # Apply Voice Activity Detection (VAD) if enabled
                                    if self.audio_capture.use_vad:
                                        # Ask VAD: "Is this 30ms frame speech or silence?"
                                        is_speech = self.audio_capture.vad.is_speech(audio_frame.tobytes(), SAMPLE_RATE)
                                        
                                        if is_speech:
                                            # This frame contains speech - add it to current utterance
                                            self.audio_capture.current_utterance.extend(audio_frame)
                                            self.audio_capture.silent_frames = 0  # Reset silence counter
                                            self.audio_capture.in_speech = True   # Mark that we're in a speech segment
                                        else:
                                            # This frame is silence
                                            if self.audio_capture.in_speech:
                                                # We were previously hearing speech, but now we have silence
                                                self.audio_capture.silent_frames += 1
                                                # Still add the silent frame to maintain timing
                                                self.audio_capture.current_utterance.extend(audio_frame)
                                                
                                                # Have we had enough consecutive silent frames to end the utterance?
                                                if self.audio_capture.silent_frames >= SILENCE_THRESHOLD:
                                                    # Check if the utterance is long enough to be meaningful (at least 1 second)
                                                    if len(self.audio_capture.current_utterance) > SAMPLE_RATE:
                                                        # Convert from int16 to float32 for Whisper processing
                                                        utterance = np.array(self.audio_capture.current_utterance, dtype=np.float32) / 32767.0
                                                        
                                                        # Send the complete utterance to Whisper for transcription
                                                        self.ui.set_live_audio("🎙️ Processing speech...")
                                                        text = await self.transcriber.transcribe_async(utterance)
                                                        
                                                        if text:
                                                            # Add the transcribed text to the UI with timestamp
                                                            self.ui.add_transcription(f"[{time.strftime('%H:%M:%S')}] {text}")
                                                            self.ui.set_live_audio("✓ Speech processed successfully")
                                                        else:
                                                            # Whisper didn't detect any speech in this audio
                                                            self.ui.set_live_audio("⚠️ No speech detected in audio")
                                                        
                                                        # Show the result briefly, then return to listening status
                                                        await asyncio.sleep(0.5)
                                                        if self.audio_capture.is_recording:
                                                            self.ui.set_live_audio("🎤 Listening for speech...")
                                                    
                                                    # Reset the utterance buffer for the next speech segment
                                                    self.audio_capture.current_utterance = []
                                                    self.audio_capture.silent_frames = 0
                                                    self.audio_capture.in_speech = False
                                    else:
                                        # VAD is disabled - use simple time-based chunking (every 3 seconds)
                                        self.audio_capture.current_utterance.extend(audio_frame)
                                        if len(self.audio_capture.current_utterance) >= SAMPLE_RATE * 3:  # 3 seconds worth of audio
                                            # Convert to float32 and send to Whisper
                                            utterance = np.array(self.audio_capture.current_utterance, dtype=np.float32) / 32767.0
                                            
                                            # Process the 3-second chunk
                                            self.ui.set_live_audio("🎙️ Processing speech...")
                                            text = await self.transcriber.transcribe_async(utterance)
                                            if text:
                                                self.ui.add_transcription(f"[{time.strftime('%H:%M:%S')}] {text}")
                                                self.ui.set_live_audio("✓ Speech processed")
                                            else:
                                                self.ui.set_live_audio("⚠️ No speech detected")
                                            
                                            # Clear and reset for next chunk
                                            await asyncio.sleep(0.5)
                                            self.audio_capture.current_utterance = []
                                            if self.audio_capture.is_recording:
                                                self.ui.set_live_audio("🎤 Listening for speech...")
                                else:
                                    # No audio data available right now, yield control to other async tasks
                                    await asyncio.sleep(0.01)
                                    
                            except Exception as e:
                                # Handle any processing errors gracefully
                                self.ui.set_live_audio(f"⚠️ Audio processing issue: {str(e)}")
                                await asyncio.sleep(0.1)
                        else:
                            # Not currently recording, just wait
                            await asyncio.sleep(0.1)
                    except asyncio.CancelledError:
                        # Task was cancelled (app shutdown)
                        self.running = False
                        break
                        
            except Exception as e:
                # Handle any unexpected errors in the audio processing loop
                self.ui.set_live_audio(f"❌ Audio processing error: {str(e)}")
            finally:
                # Cleanup: stop audio capture and UI when exiting the loop
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
            logger.info("\n🛑 Shutting down...")
            self.running = False
        except Exception as e:
            logger.error(f"❌ Application error: {e}")
        finally:
            if self.audio_capture.is_recording:
                self.audio_capture.stop_capture()
            # Shutdown transcriber thread pool
            self.transcriber.shutdown()
            self.ui.stop()


def list_audio_devices():
    """List available audio input devices."""
    logger.info("Available audio input devices:")
    devices = sd.query_devices()
    found = False
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            logger.info(f"  {i}: {device['name']} (inputs: {device['max_input_channels']})")
            found = True
    
    if not found:
        logger.info("  No audio input devices found!")
    
    logger.info("\nTo use a specific device:")
    logger.info("  python app.py --mic-index NUMBER")



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
        # Start the async event loop and run the application
        # asyncio.run() handles setting up the event loop and cleaning up when done
        asyncio.run(app.run())
    except KeyboardInterrupt:
        # User pressed Ctrl+C - this is normal and expected
        logger.info("\n✅ Application stopped by user")
    except Exception as e:
        # Something unexpected went wrong
        logger.error(f"❌ Application failed: {e}")


if __name__ == "__main__":
    """
    This block only runs when the script is executed directly (not imported).
    It's the standard Python pattern for making a script both importable and executable.
    """
    main()
