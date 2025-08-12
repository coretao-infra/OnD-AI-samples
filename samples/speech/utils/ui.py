import asyncio
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.align import Align

# this is the UI helper utility module that implements the complexity of the 90's xtree gold style look.

class XTreeUI:
    def __init__(self, refresh_per_second=10, height=24):
        self.console = Console()
        self.transcription_log = []
        self.vu_levels = [0.0, 0.0]
        self.live_audio_text = ""
        self.refresh_per_second = refresh_per_second
        self.height = height
        self._live = None
        self._running = False

    def _make_stereo_vu_meter(self, levels, height=20):
        left = levels[0] if len(levels) > 0 else 0.0
        right = levels[1] if len(levels) > 1 else 0.0
        bars = [[], []]
        for idx, level in enumerate((left, right)):
            filled = int(level * height)
            for i in range(height):
                if i < height - filled:
                    bars[idx].append(("│", "dim"))
                else:
                    color = "yellow" if i >= height - 3 else ("green" if i >= height - 7 else "bright_blue")
                    bars[idx].append(("█", f"bold {color}"))
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
        return Align.center(Text.assemble(*[Text(str(line) + "\n") for line in lines]), vertical="middle")

    def _make_layout(self):
        layout = Layout()
        layout.split_column(
            Layout(name="main", ratio=3),
            Layout(name="live", size=3)
        )
        layout["main"].split_row(
            Layout(name="transcription"),
            Layout(name="vu", size=12)
        )
        trans_text = Text("\n".join(self.transcription_log[-20:]), style="white")
        trans_panel = Panel(
            trans_text,
            title="[yellow]Transcription Log[/yellow]",
            border_style="blue",
            padding=(1,2),
            height=self.height,
            subtitle="(last 20 lines)"
        )
        vu_panel = Panel(
            self._make_stereo_vu_meter(self.vu_levels),
            title="[green]VU L   R[/green]",
            border_style="green",
            padding=(1,1)
        )
        live_panel = Panel(
            Text(self.live_audio_text, style="bold white"),
            title="[magenta]Live Audio (in progress)[/magenta]",
            border_style="magenta",
            padding=(0,2)
        )
        layout["main"]["transcription"].update(trans_panel)
        layout["main"]["vu"].update(vu_panel)
        layout["live"].update(live_panel)
        return layout

    async def run(self):
        self._running = True
        with Live(self._make_layout(), refresh_per_second=self.refresh_per_second, screen=True, console=self.console) as live:
            self._live = live
            while self._running:
                live.update(self._make_layout())
                await asyncio.sleep(1 / self.refresh_per_second)

    def stop(self):
        self._running = False

    def update_vu(self, levels):
        self.vu_levels = list(levels)

    def add_transcription(self, text):
        self.transcription_log.append(text)

    def set_live_audio(self, text):
        self.live_audio_text = text
