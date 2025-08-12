import asyncio
import random
from utils.enhanced_ui import EnhancedXTreeUI

async def main():
    ui = EnhancedXTreeUI(refresh_per_second=10, height=24)
    
    # Set some initial state
    ui.set_current_file("meeting_transcript_2025-08-12.txt")
    ui.start_capture()  # Start in capture mode
    ui.toggle_system_audio()  # Enable system audio

    async def update_loop():
        live_audio_texts = [
            "Listening for speech...",
            "Processing: The quick brown fox jumps over the lazy dog.",
            "VAD: Voice activity detected",
            "Partial: Hello, worl",
            "Partial: Hello, world! How are you today?",
            "Partial: We need to discuss the project timeline",
            "Processing complete.",
            "Silence detected.",
            ""
        ]
        
        sample_transcripts = [
            "Welcome to today's meeting. Let's start with the project updates.",
            "The development team has completed phase one of the application.",
            "We need to review the budget allocation for the next quarter.",
            "The new features are working well in the testing environment.",
            "Let's schedule a follow-up meeting for next week.",
            "Are there any questions about the implementation plan?",
            "Thank you all for your participation today.",
            "[Meeting ended - 3:47 PM]"
        ]
        
        transcript_index = 0
        
        for i in range(500):  # Run longer to show more features
            # Simulate stereo VU with more realistic patterns
            left_level = abs(random.normalvariate(0.3, 0.2))
            right_level = abs(random.normalvariate(0.3, 0.2))
            ui.update_vu([min(left_level, 1.0), min(right_level, 1.0)])
            
            # Simulate live audio text (rotating)
            ui.set_live_audio(live_audio_texts[i % len(live_audio_texts)])
            
            # Add transcription periodically
            if i % 35 == 0 and transcript_index < len(sample_transcripts):
                ui.add_transcription(sample_transcripts[transcript_index])
                transcript_index += 1
            
            # Simulate some state changes
            if i == 100:
                ui.stop_capture()  # Stop capture after a while
                ui.set_current_file("archived_meeting.txt")
                
            if i == 200:
                ui.start_capture()  # Resume capture
                ui.set_current_file("new_session.txt")
                
            if i == 300:
                ui.toggle_system_audio()  # Toggle system audio off
                
            await asyncio.sleep(0.1)
        
        ui.stop()

    await asyncio.gather(ui.run(), update_loop())

if __name__ == "__main__":
    asyncio.run(main())
