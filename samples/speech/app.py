#!/usr/bin/env python3
"""
Windows On-Device AI Lab: Live Captions (Simplified Demo Version)
Real-time speech transcription using OpenAI Whisper models.

This simplified version demonstrates clean separation of concerns:
- AudioProcessor: Handles all audio capture, VAD, and processing coordination  
- WhisperTranscriber: Handles all transcription concerns
- EnhancedXTreeUI: Handles all UI concerns
- LiveCaptionsApp: Simple orchestration only
"""

import argparse
import asyncio
from typing import Optional
import sounddevice as sd
from utils.enhanced_ui import EnhancedXTreeUI
from utils.transcribe import WhisperTranscriber
from utils.audio_processor import AudioProcessor
from utils.logger import logger
from config import UI_REFRESH_RATE, UI_HEIGHT


class LiveCaptionsApp:
    """
    Simplified main application - orchestrates components only.
    
    This class demonstrates clean separation of concerns:
    - No audio processing logic (handled by AudioProcessor)
    - No transcription logic (handled by WhisperTranscriber) 
    - No complex UI logic (handled by EnhancedXTreeUI)
    - Just simple coordination between components
    """
    
    def __init__(self, model_size: str = "tiny", language: Optional[str] = None, 
                 mic_index: Optional[int] = None, use_vad: bool = True):
        
        # Initialize components - each handles its own concerns
        self.transcriber = WhisperTranscriber(
            model_size=model_size,
            language=language,
            device="cpu",
            compute_type="int8"
        )
        
        self.ui = EnhancedXTreeUI(refresh_per_second=UI_REFRESH_RATE, height=UI_HEIGHT)
        
        self.audio_processor = AudioProcessor(
            transcriber=self.transcriber,
            mic_index=mic_index,
            use_vad=use_vad
        )
        
        # Connect components via callbacks
        self.audio_processor.set_callbacks(
            status_callback=self.ui.set_live_audio,
            transcription_callback=self.ui.add_transcription
        )
        
        self.running = False
    
    def start_recording(self):
        """Start audio recording - simple delegation."""
        self.audio_processor.start_recording()
    
    def stop_recording(self):
        """Stop audio recording - simple delegation."""
        self.audio_processor.stop_recording()
    
    def toggle_recording(self):
        """Toggle recording state."""
        if self.audio_processor.audio_capture.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    async def run(self):
        """
        Main application loop - much simpler now!
        Just coordinates the three main async tasks.
        """
        self.running = True
        
        # Set up initial UI state
        self._setup_initial_ui()
        
        try:
            # Run the three main async tasks concurrently
            await asyncio.gather(
                self._run_ui(),
                self._update_vu_meter(),  
                self._process_audio(),
                self._demo_auto_start(),  # For demo purposes
                return_exceptions=True
            )
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutting down...")
        except Exception as e:
            logger.error(f"❌ Application error: {e}")
        finally:
            await self._cleanup()
    
    async def _run_ui(self):
        """Run the UI - simple delegation."""
        await self.ui.run()
    
    async def _update_vu_meter(self):
        """Update VU meter levels - simple coordination."""
        while self.running:
            try:
                vu_levels = self.audio_processor.get_vu_levels()
                self.ui.update_vu(vu_levels)
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
    
    async def _process_audio(self):
        """Process audio - simple delegation."""
        await self.audio_processor.process_audio_loop()
    
    async def _demo_auto_start(self):
        """Auto-start recording for demo purposes."""
        await asyncio.sleep(3)  # Wait a few seconds
        if self.running:
            self.start_recording()
    
    def _setup_initial_ui(self):
        """Set up initial UI messages."""
        self.ui.set_live_audio("Ready to start recording...")
        self.ui.add_transcription("Welcome to Live Captions!")
        self.ui.add_transcription("The recording will start automatically in a few seconds.")
        self.ui.add_transcription("Press Ctrl+C to exit.")
    
    async def _cleanup(self):
        """Clean up resources."""
        self.running = False
        self.audio_processor.stop()
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
    logger.info("  python simple_app.py --mic-index NUMBER")


def main():
    """
    Simple main function - just argument parsing and app creation.
    Much cleaner than the original!
    """
    parser = argparse.ArgumentParser(description="Live Captions using OpenAI Whisper (Simplified Demo)")
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

    # Create and run the app - much simpler!
    app = LiveCaptionsApp(
        model_size=args.model_size,
        language=args.language,
        mic_index=args.mic_index,
        use_vad=not args.no_vad
    )

    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logger.info("\n✅ Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application failed: {e}")


if __name__ == "__main__":
    main()
