import asyncio
import random
from utils.ui import XTreeUI

async def main():
    ui = XTreeUI(refresh_per_second=10, height=24)

    async def update_loop():
        live_audio_texts = [
            "Listening...",
            "The quick brown fox jumps over the lazy dog.",
            "This is a test of the live audio input.",
            "Partial: Hello, worl",
            "Partial: Hello, world!",
            "Partial: How are you do",
            "Partial: How are you doing?",
            "Partial: Thank you.",
            ""
        ]
        for i in range(200):
            # Simulate stereo VU
            ui.update_vu([random.random(), random.random()])
            # Simulate live audio text (rotating)
            ui.set_live_audio(live_audio_texts[i % len(live_audio_texts)])
            # Simulate transcription log
            if i % 20 == 0:
                new_line = random.choice([
                    "Hello, world!",
                    "Testing one two three...",
                    "¡El ogelón!",
                    "How are you?",
                    "Thank you.",
                    "[No speech detected]"
                ])
                ui.add_transcription(new_line)
            await asyncio.sleep(0.1)
        ui.stop()

    await asyncio.gather(ui.run(), update_loop())

if __name__ == "__main__":
    asyncio.run(main())
