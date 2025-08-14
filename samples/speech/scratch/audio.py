import sounddevice as sd
import soundcard as sc  # For robust Windows Core Audio device enumeration
import whisper
import numpy as np
import threading
import queue
import time
from collections import deque
import torch
from typing import Optional, Callable

class RealTimeWhisperTranscriber:
    def __init__(
        self,
        model_name: str = "base",
        device: Optional[str] = None,
        sample_rate: int = 16000,
        chunk_duration: float = 1.0,  # seconds of audio per chunk
        overlap_duration: float = 0.5,  # seconds of overlap between chunks
        vad_threshold: float = 0.01,  # voice activity detection threshold
        silence_timeout: float = 2.0,  # seconds of silence before processing
        callback: Optional[Callable[[str], None]] = None
    ):
        """
        Real-time transcription with Whisper
        
        Args:
            model_name: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
            device: Audio input device ID from soundcard (None for default)
            sample_rate: Audio sample rate (16kHz recommended for Whisper)
            chunk_duration: Length of each audio chunk to process
            overlap_duration: Overlap between chunks to avoid cutting words
            vad_threshold: Threshold for voice activity detection
            silence_timeout: How long to wait after silence before transcribing
            callback: Function to call with transcribed text
        """
        self.model_name = model_name
        self.device = device
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.overlap_duration = overlap_duration
        self.vad_threshold = vad_threshold
        self.silence_timeout = silence_timeout
        self.callback = callback
        
        # Calculate buffer sizes
        self.chunk_samples = int(sample_rate * chunk_duration)
        self.overlap_samples = int(sample_rate * overlap_duration)
        
        # Audio buffers
        self.audio_queue = queue.Queue()
        self.audio_buffer = deque(maxlen=int(sample_rate * 30))  # 30 second rolling buffer
        
        # State management
        self.is_recording = False
        self.is_processing = False
        self.last_voice_time = 0
        
        # Threading
        self.record_thread = None
        self.process_thread = None
        
        # Load Whisper model
        print(f"Loading Whisper model: {model_name}")
        self.model = whisper.load_model(model_name)
        print("Model loaded successfully")

    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio input stream"""
        if status:
            print(f"Audio callback status: {status}")
        
        # Convert to mono if stereo
        if indata.shape[1] > 1:
            audio_data = np.mean(indata, axis=1)
        else:
            audio_data = indata[:, 0]
        
        # Add to buffer
        self.audio_buffer.extend(audio_data)
        
        # Voice Activity Detection (simple RMS-based)
        rms = np.sqrt(np.mean(audio_data ** 2))
        if rms > self.vad_threshold:
            self.last_voice_time = time.inputBufferAdcTime
        
        # Add chunk to processing queue if we have enough data
        if len(self.audio_buffer) >= self.chunk_samples:
            chunk = np.array(list(self.audio_buffer)[-self.chunk_samples:])
            try:
                self.audio_queue.put_nowait(chunk.copy())
            except queue.Full:
                # Skip if queue is full (processing can't keep up)
                pass

    def _process_audio(self):
        """Process audio chunks for transcription"""
        while self.is_processing:
            try:
                # Get audio chunk with timeout
                chunk = self.audio_queue.get(timeout=0.1)
                
                # Process every chunk immediately for now (simplify logic)
                print(f"Processing chunk immediately")
                # Transcribe chunk
                text = self._transcribe_chunk(chunk)
                
                if text.strip():
                    print(f"Transcribed: {text}")
                    if self.callback:
                        self.callback(text)
                
                self.audio_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Processing error: {e}")

    def _transcribe_chunk(self, audio_chunk: np.ndarray) -> str:
        """Transcribe a single audio chunk"""
        try:
            # Debug audio data
            print(f"Audio chunk shape: {audio_chunk.shape}, dtype: {audio_chunk.dtype}")
            print(f"Audio range: {np.min(audio_chunk):.4f} to {np.max(audio_chunk):.4f}")
            print(f"Audio RMS: {np.sqrt(np.mean(audio_chunk ** 2)):.4f}")
            
            # Ensure audio is float32 and properly formatted
            if audio_chunk.dtype != np.float32:
                audio_chunk = audio_chunk.astype(np.float32)
            
            # Check if audio has actual content
            if np.max(np.abs(audio_chunk)) < 1e-6:
                print("Audio chunk appears to be silent")
                return ""
            
            # Normalize audio to [-1, 1] range
            max_val = np.max(np.abs(audio_chunk))
            if max_val > 0:
                audio_chunk = audio_chunk / max_val
            
            print(f"Normalized audio range: {np.min(audio_chunk):.4f} to {np.max(audio_chunk):.4f}")
            
            # Transcribe with Whisper
            result = self.model.transcribe(
                audio_chunk,
                language="en",  # Specify language for better performance
                task="transcribe",
                fp16=torch.cuda.is_available(),  # Use FP16 if CUDA available
                verbose=False
            )
            
            return result["text"].strip()
            
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""

    def start(self):
        """Start real-time transcription"""
        if self.is_recording:
            print("Already recording")
            return
        
        print("Starting real-time transcription...")
        print(f"Using audio device: {self.device}")
        print(f"Sample rate: {self.sample_rate} Hz")
        print(f"Chunk duration: {self.chunk_duration}s")
        
        self.is_recording = True
        self.is_processing = True
        self.last_voice_time = time.time()
        
        # Start processing thread
        self.process_thread = threading.Thread(target=self._process_audio, daemon=True)
        self.process_thread.start()
        
        # Use soundcard for audio capture
        try:
            # Get the microphone by ID or use default
            if self.device:
                mic = sc.get_microphone(self.device)
            else:
                mic = sc.default_microphone()
            
            print("Recording started. Press Ctrl+C to stop.")
            
            # Use larger buffer size to reduce discontinuities
            buffer_frames = int(self.sample_rate * 0.5)  # 500ms buffer
            
            with mic.recorder(samplerate=self.sample_rate, channels=1, blocksize=buffer_frames) as recorder:
                while self.is_recording:
                    # Read larger chunks less frequently
                    data = recorder.record(numframes=buffer_frames)
                    
                    if data is not None and len(data) > 0:
                        # Convert to mono if needed
                        if data.ndim > 1:
                            audio_data = np.mean(data, axis=1)
                        else:
                            audio_data = data
                        
                        # Add to buffer
                        self.audio_buffer.extend(audio_data)
                        
                        # Voice Activity Detection on the chunk
                        rms = np.sqrt(np.mean(audio_data ** 2))
                        if rms > self.vad_threshold:
                            self.last_voice_time = time.time()
                            print(f"Voice detected (RMS: {rms:.4f})")
                        
                        # Add chunk to processing queue if we have enough data
                        if len(self.audio_buffer) >= self.chunk_samples:
                            chunk = np.array(list(self.audio_buffer)[-self.chunk_samples:])
                            try:
                                self.audio_queue.put_nowait(chunk.copy())
                                print(f"Added chunk to queue (size: {self.audio_queue.qsize()})")
                            except queue.Full:
                                # Skip if queue is full
                                print("Queue full, skipping chunk")
                    
        except KeyboardInterrupt:
            print("\nStopping...")
        except Exception as e:
            print(f"Audio stream error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stop transcription"""
        print("Stopping transcription...")
        self.is_recording = False
        self.is_processing = False
        
        if self.process_thread and self.process_thread.is_alive():
            self.process_thread.join(timeout=2.0)

    def get_available_devices(self):
        """
        Get list of available audio input devices using Windows Core Audio (soundcard).
        No fallback. Only real microphones, no loopback, no virtual devices.
        """
        microphones = sc.all_microphones(include_loopback=False)
        input_devices = []
        for mic in microphones:
            input_devices.append({
                'id': mic.id,
                'name': mic.name,
                'channels': mic.channels,
            })
        return input_devices


def main():
    """Example usage"""
    
    # Create transcriber
    def on_transcription(text):
        print(f">>> {text}")
    
    transcriber = RealTimeWhisperTranscriber(
        model_name="base",  # or "tiny" for faster processing
        device="{0.0.1.00000000}.{96e55d27-35b5-4b63-ae14-7fb2f30b5801}",  # Use actual device ID
        chunk_duration=2.0,  # 2 second chunks
        overlap_duration=0.5,  # 0.5 second overlap
        vad_threshold=0.005,  # Lower threshold for more sensitive detection
        silence_timeout=1.0,  # Shorter timeout for faster processing
        callback=on_transcription
    )
    
    # Show available devices
    print("Available input devices:")
    devices = transcriber.get_available_devices()
    for device in devices:
        print(f"  {device['id']}: {device['name']}")
    
    # Start transcription
    try:
        transcriber.start()
    except KeyboardInterrupt:
        transcriber.stop()


if __name__ == "__main__":
    main()