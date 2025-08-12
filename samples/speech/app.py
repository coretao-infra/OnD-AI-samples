#!/usr/bin/env python3
"""
Windows On-Device AI Lab: Live Captions
Real-time speech transcription using Whisper models via faster-whisper.
"""

import argparse
import queue
import sys
import threading
import time
from typing import Generator, Optional, Tuple

import numpy as np
import sounddevice as sd
import webrtcvad
from faster_whisper import WhisperModel
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

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
        self.console = Console()
        
        # VAD state
        self.current_utterance = []
        self.silent_frames = 0
        self.in_speech = False
    
    def audio_callback(self, indata, frames, time, status):
        """Called by sounddevice for each audio frame."""
        if status:
            self.console.print(f"[yellow]Audio callback status: {status}[/yellow]")
        
        # Convert to int16 for VAD and queue for processing
        audio_int16 = (indata[:, 0] * 32767).astype(np.int16)
        
        # Log audio levels periodically
        if hasattr(self, '_callback_count'):
            self._callback_count += 1
        else:
            self._callback_count = 1
            
        if self._callback_count % 50 == 0:  # Every ~1.5 seconds at 30ms frames
            max_amplitude = np.max(np.abs(audio_int16))
            self.console.print(f"[dim]Audio level: {max_amplitude} (frames processed: {self._callback_count})[/dim]")
        
        try:
            self.audio_queue.put_nowait(audio_int16)
        except queue.Full:
            self.console.print("[red]Warning: Audio queue full, dropping frame[/red]")
            pass
    
    def start_capture(self):
        """Start audio capture."""
        self.console.print("[blue]🎙️ Starting audio capture...[/blue]")
        self.is_recording = True
        
        # Use specified device or system default input device
        device_to_use = self.device_index
        if device_to_use is None:
            # Get the actual default input device from the system
            try:
                device_to_use = sd.default.device[0]  # [0] is input, [1] is output
                if device_to_use == -1:
                    raise ValueError("No default input device configured")
                self.console.print(f"[green]Using system default input device: {device_to_use}[/green]")
            except Exception as e:
                self.console.print(f"[yellow]Could not get default input device ({e}), searching manually...[/yellow]")
                # Fallback: find first real microphone device (skip Stereo Mix and PC Speaker)
                devices = sd.query_devices()
                for i, device in enumerate(devices):
                    if (device['max_input_channels'] > 0 and 
                        'microphone' in device['name'].lower() and 
                        'stereo mix' not in device['name'].lower() and
                        'pc speaker' not in device['name'].lower()):
                        device_to_use = i
                        self.console.print(f"[green]Found microphone device {i}: {device['name']}[/green]")
                        break
                if device_to_use is None:
                    raise RuntimeError("No suitable input devices found")
        
        # Get device info and use its native sample rate
        device_info = sd.query_devices(device_to_use)
        native_rate = int(device_info['default_samplerate'])
        device_name = device_info['name']
        
        self.console.print(f"[green]✓ Using device: {device_name} @ {native_rate}Hz[/green]")
        
        # Calculate frame size for this sample rate
        frames_per_buffer = int(native_rate * FRAME_DURATION_MS / 1000)
        self.console.print(f"[blue]Frame size: {frames_per_buffer} samples ({FRAME_DURATION_MS}ms)[/blue]")
        
        try:
            self.stream = sd.InputStream(
                samplerate=native_rate,
                channels=1,
                dtype=np.float32,
                blocksize=frames_per_buffer,
                device=device_to_use,
                callback=self.audio_callback
            )
            self.stream.start()
            self.console.print("[green]✓ Audio stream started successfully![/green]")
        except Exception as e:
            self.console.print(f"[red]✗ Failed to start audio stream: {e}[/red]")
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
    """Main application for live speech captioning."""
    
    def __init__(self, model_size: str = "tiny", language: Optional[str] = None, 
                 device: str = "cpu", compute_type: str = "int8", 
                 mic_index: Optional[int] = None, use_vad: bool = True):
        self.console = Console()
        self.model_size = model_size
        self.language = language
        self.device = device
        self.compute_type = compute_type
        self.use_vad = use_vad
        
        # Initialize Whisper model
        self.console.print(f"[cyan]Loading Whisper model ({model_size})...[/cyan]")
        self.model = WhisperModel(
            model_size, 
            device=device, 
            compute_type=compute_type
        )
        self.console.print("[green]✓ Model loaded[/green]")
        
        # Initialize audio capture
        self.audio_capture = AudioCapture(mic_index, use_vad)
        
        # State
        self.running = False
        self.current_text = ""
        self.transcript_history = []
    
    def transcribe_audio(self, audio: np.ndarray) -> str:
        """Transcribe audio using Whisper."""
        try:
            segments, info = self.model.transcribe(
                audio,
                language=self.language,
                beam_size=1,  # Faster
                word_timestamps=False
            )
            
            # Combine all segments
            text = " ".join(segment.text.strip() for segment in segments)
            return text.strip()
        except Exception as e:
            self.console.print(f"[red]Transcription error: {e}[/red]")
            return ""
    
    def update_display(self, text: str, is_final: bool = False):
        """Update the display with new text."""
        if is_final and text:
            self.transcript_history.append(text)
            # Keep only last 10 lines
            if len(self.transcript_history) > 10:
                self.transcript_history.pop(0)
        
        # Create display content
        history_text = "\n".join(self.transcript_history)
        current_display = f"{history_text}\n[dim]{text}[/dim]" if not is_final else history_text
        
        return Panel(
            current_display or "[dim]Listening for speech...[/dim]",
            title="[bold blue]Live Captions[/bold blue]",
            border_style="blue"
        )
    
    def run_console(self):
        """Run the app with console output."""
        self.console.print("[yellow]Starting Live Captions (Press Ctrl+C to stop)...[/yellow]")
        self.console.print(f"Model: {self.model_size} | Device: {self.device} | VAD: {'ON' if self.use_vad else 'OFF'}")
        
        self.running = True
        self.audio_capture.start_capture()
        
        try:
            with Live(self.update_display(""), console=self.console, refresh_per_second=4) as live:
                for utterance in self.audio_capture.get_utterances():
                    if not self.running:
                        break
                    
                    # Show processing indicator
                    live.update(self.update_display("[yellow]Processing...[/yellow]"))
                    
                    # Transcribe
                    text = self.transcribe_audio(utterance)
                    
                    if text:
                        # Update with final result
                        live.update(self.update_display(text, is_final=True))
                    else:
                        # Clear processing indicator
                        live.update(self.update_display(""))
                        
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Stopping...[/yellow]")
        finally:
            self.running = False
            self.audio_capture.stop_capture()


def list_audio_devices():
    """List available audio input devices."""
    console = Console()
    console.print("[cyan]Available audio devices:[/cyan]")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            console.print(f"  {i}: {device['name']} (inputs: {device['max_input_channels']})")


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
    
    # Create and run app
    app = LiveCaptionsApp(
        model_size=args.model_size,
        language=args.language,
        device=args.device,
        compute_type=args.compute_type,
        mic_index=args.mic_index,
        use_vad=not args.no_vad
    )
    
    app.run_console()


if __name__ == "__main__":
    main()
