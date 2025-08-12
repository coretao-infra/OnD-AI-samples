import time
import random
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.align import Align

def make_stereo_vu_meter(levels, height=20):
    """Create a stereo (L/R) vertical VU meter as a Rich Text object (no markdown)."""
    from rich.text import Text
    # Defensive: always two channels
    left = levels[0] if len(levels) > 0 else 0.0
    right = levels[1] if len(levels) > 1 else 0.0
    bars = [[], []]  # Each will be a list of (char, style) tuples
    for idx, level in enumerate((left, right)):
        filled = int(level * height)
        for i in range(height):
            if i < height - filled:
                bars[idx].append(("│", "dim"))
            else:
                color = "yellow" if i >= height - 3 else ("green" if i >= height - 7 else "bright_blue")
                bars[idx].append(("█", f"bold {color}"))
    # Ensure both bars are exactly 'height' tall
    for idx in range(2):
        while len(bars[idx]) < height:
            bars[idx].insert(0, ("│", "dim"))
        while len(bars[idx]) > height:
            bars[idx] = bars[idx][:height]
    lines = []
    for i in range(height):
        l_char, l_style = bars[0][i]
        r_char, r_style = bars[1][i]
        line = Text(l_char, style=l_style) + Text("  ") + Text(r_char, style=r_style)
        lines.append(line)
    # Join lines with newlines for vertical bar
    return Align.center(Text.assemble(*[Text(str(line) + "\n") for line in lines]), vertical="middle")
    # Combine L/R bars side by side
    lines = []
    for i in range(height):
        l = bars[0].plain.splitlines()[i] if i < len(bars[0].plain.splitlines()) else " "
        r = bars[1].plain.splitlines()[i] if i < len(bars[1].plain.splitlines()) else " "
        # Use Text.assemble to preserve color
        lines.append(Text.assemble(bars[0][i*2], "  ", bars[1][i*2]))
    return Align.center(Text.assemble(*lines), vertical="middle")


def make_layout(transcription_log, vu_levels, live_audio_text):
    layout = Layout()
    layout.split_column(
        Layout(name="main", ratio=3),
        Layout(name="live", size=3)
    )
    layout["main"].split_row(
        Layout(name="transcription"),
        Layout(name="vu", size=12)
    )
    # Transcription log (scrolling, with scrollbar)
    trans_text = Text("\n".join(transcription_log[-20:]), style="white")
    trans_panel = Panel(
        trans_text,
        title="[yellow]Transcription Log[/yellow]",
        border_style="blue",
        padding=(1,2),
        height=24,
        subtitle="(last 20 lines)"
    )
    # Stereo VU meter (right)
    vu_panel = Panel(
        make_stereo_vu_meter(vu_levels),
        title="[green]VU L   R[/green]",
        border_style="green",
        padding=(1,1)
    )
    # Live audio text (bottom)
    live_panel = Panel(
        Text(live_audio_text, style="bold white"),
        title="[magenta]Live Audio (in progress)[/magenta]",
        border_style="magenta",
        padding=(0,2)
    )
    layout["main"]["transcription"].update(trans_panel)
    layout["main"]["vu"].update(vu_panel)
    layout["live"].update(live_panel)
    return layout

def main():
    console = Console()
    transcription_log = []
    vu_levels = [0.0, 0.0]
    live_audio_text = ""
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
    with Live(make_layout(transcription_log, vu_levels, live_audio_text), refresh_per_second=10, screen=True, console=console) as live:
        for i in range(200):
            # Simulate stereo VU
            vu_levels = [random.random(), random.random()]
            # Simulate live audio text (rotating)
            live_audio_text = live_audio_texts[i % len(live_audio_texts)]
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
                transcription_log.append(new_line)
            live.update(make_layout(transcription_log, vu_levels, live_audio_text))
            time.sleep(0.1)

if __name__ == "__main__":
    main()
