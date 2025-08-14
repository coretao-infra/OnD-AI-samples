#!/usr/bin/env python3
"""
Simple UI test for the Enhanced XTree UI
This runs just the UI without audio processing to verify it works correctly.
"""

import asyncio
import random
import time
from utils.enhanced_ui import EnhancedXTreeUI

async def main():
    """Test the enhanced UI with simulated data."""
    ui = EnhancedXTreeUI(refresh_per_second=10)
    
    # Set initial status
    ui.set_live_audio("UI Test Mode - Simulating live captions")
    ui.add_transcription("Welcome to the Enhanced XTree UI test!")
    ui.add_transcription("This is a demonstration of the user interface.")
    ui.add_transcription("The UI should show:")
    ui.add_transcription("- Top left: This scrolling transcript area")
    ui.add_transcription("- Top right: Controls and hotkeys panel") 
    ui.add_transcription("- Middle right: Audio devices (single line per device)")
    ui.add_transcription("- Bottom left: Live audio processing status")
    ui.add_transcription("- Bottom right: Horizontal stereo VU meter")
    
    async def simulate_activity():
        """Simulate live activity for demonstration."""
        messages = [
            "Testing stereo VU meter visualization...",
            "Device list should show available audio inputs",
            "Controls panel shows keyboard shortcuts",
            "Audio processing status appears in bottom left",
            "This transcript area scrolls automatically",
            "Press Ctrl+C to exit the application"
        ]
        
        counter = 0
        while True:
            # Simulate VU meter activity
            left_level = random.random() * 0.8
            right_level = random.random() * 0.8
            ui.update_vu([left_level, right_level])
            
            # Add periodic messages
            if counter % 50 == 0:  # Every 5 seconds at 10 FPS
                message_index = (counter // 50) % len(messages)
                timestamp = time.strftime('%H:%M:%S')
                ui.add_transcription(f"[{timestamp}] {messages[message_index]}")
            
            # Update status periodically
            if counter % 30 == 0:  # Every 3 seconds
                statuses = [
                    "🎤 Simulating audio input...",
                    "🔍 Processing voice activity...", 
                    "💭 Transcribing speech...",
                    "✅ Ready for input..."
                ]
                status = statuses[(counter // 30) % len(statuses)]
                ui.set_live_audio(status)
            
            counter += 1
            await asyncio.sleep(0.1)
    
    # Run UI and simulation concurrently
    await asyncio.gather(
        ui.run(),
        simulate_activity()
    )

if __name__ == "__main__":
    print("Starting Enhanced XTree UI Test...")
    print("Press Ctrl+C to exit")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nUI test completed!")
