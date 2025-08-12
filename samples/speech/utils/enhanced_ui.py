import asyncio
import sounddevice as sd
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich.table import Table
from rich.columns import Columns

class EnhancedXTreeUI:
    def __init__(self, refresh_per_second=10, height=24):
        self.console = Console()
        self.transcription_log = []
        self.vu_levels = [0.0, 0.0]
        self.live_audio_text = ""
        self.refresh_per_second = refresh_per_second
        self.height = height
        self._live = None
        self._running = False
        
        # Enhanced state
        self.is_capturing = False
        self.current_file = "untitled.txt"
        self.include_system_audio = False
        self.selected_device_index = None
        self.available_devices = []
        self.default_device_index = None
        self._load_audio_devices()

    def _load_audio_devices(self):
        """Load available audio input devices."""
        try:
            devices = sd.query_devices()
            self.available_devices = []
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    self.available_devices.append({
                        'index': i,
                        'name': device['name'],
                        'inputs': device['max_input_channels']
                    })
            
            # Get default device
            try:
                self.default_device_index = sd.default.device[0]
                if self.default_device_index == -1:
                    self.default_device_index = None
            except:
                self.default_device_index = None
                
            # Set selected device to default if none selected
            if self.selected_device_index is None:
                self.selected_device_index = self.default_device_index
                
        except Exception as e:
            self.available_devices = []
            self.default_device_index = None

    def _make_stereo_vu_meter(self, levels, height=3):
        """Create a horizontal stereo VU meter for better space usage."""
        left = levels[0] if len(levels) > 0 else 0.0
        right = levels[1] if len(levels) > 1 else 0.0
        
        # Create horizontal bars (width=35 chars each)
        bar_width = 35
        left_filled = int(left * bar_width)
        right_filled = int(right * bar_width)
        
        # Left channel bar
        left_bar = Text()
        for i in range(bar_width):
            if i < left_filled:
                if i > bar_width * 0.8:  # Red zone (80%+)
                    left_bar.append("█", style="bold red")
                elif i > bar_width * 0.6:  # Yellow zone (60-80%)
                    left_bar.append("█", style="bold yellow")
                else:  # Green zone (0-60%)
                    left_bar.append("█", style="bold green")
            else:
                left_bar.append("─", style="dim")
        
        # Right channel bar
        right_bar = Text()
        for i in range(bar_width):
            if i < right_filled:
                if i > bar_width * 0.8:
                    right_bar.append("█", style="bold red")
                elif i > bar_width * 0.6:
                    right_bar.append("█", style="bold yellow")
                else:
                    right_bar.append("█", style="bold green")
            else:
                right_bar.append("─", style="dim")
        
        # Combine with labels - NO percentages
        vu_text = Text()
        vu_text.append("L ", style="bold white")
        vu_text.append_text(left_bar)
        vu_text.append("\nR ", style="bold white")
        vu_text.append_text(right_bar)
        
        return vu_text

    def _make_device_panel(self):
        """Create device selector with single-line entries for each device."""
        device_lines = []
        
        for device in self.available_devices:
            # Determine status marker and color
            if device['index'] == self.default_device_index:
                marker = "●"
                status_style = "bold green"
            elif device['index'] == self.selected_device_index:
                marker = "◆"
                status_style = "bold yellow"
            else:
                marker = "○"
                status_style = "dim white"
            
            # Create single line per device - NO channel info, NO second line
            device_line = Text()
            device_line.append(f"{marker} ", style=status_style)
            device_line.append(f"{device['index']:2d}: ", style="cyan")
            
            # Truncate device name to fit in one line
            name = device['name'][:35] + ("..." if len(device['name']) > 35 else "")
            device_line.append(name, style="bright_white" if device['index'] in [self.default_device_index, self.selected_device_index] else "white")
            
            device_lines.append(device_line)
        
        if not self.available_devices:
            no_devices = Text("No input devices found", style="dim red")
            device_lines.append(no_devices)
        
        # Show last 6 devices (scrollable concept)
        visible_lines = device_lines[-6:] if len(device_lines) > 6 else device_lines
        device_text = Text()
        for i, line in enumerate(visible_lines):
            device_text.append_text(line)
            if i < len(visible_lines) - 1:
                device_text.append("\n")
        
        return Panel(
            device_text,
            title="[bold cyan]Audio Devices[/]" + (f" ({len(self.available_devices)} total)" if len(self.available_devices) > 6 else ""),
            title_align="left",
            border_style="cyan",
            height=8,  # Enough space for multiple device lines
            padding=(0, 1)
        )

    def _make_controls_panel(self):
        """Create controls and file operations panel."""
        controls_text = Text()
        
        # File section
        controls_text.append("File Operations:\n", style="bold yellow")
        controls_text.append(f"Current: {self.current_file}\n", style="white")
        controls_text.append("F2: Save transcript\n", style="cyan")
        controls_text.append("F3: Load file to transcribe\n", style="cyan")
        controls_text.append("F4: New transcript\n", style="cyan")
        
        controls_text.append("\nCapture Controls:\n", style="bold yellow")
        status = "RECORDING" if self.is_capturing else "STOPPED"
        status_color = "green" if self.is_capturing else "red"
        controls_text.append(f"Status: {status}\n", style=f"bold {status_color}")
        controls_text.append("SPACE: Start/Stop capture\n", style="cyan")
        
        # Audio options
        controls_text.append("\nAudio Options:\n", style="bold yellow")
        sys_audio = "ON" if self.include_system_audio else "OFF"
        sys_color = "green" if self.include_system_audio else "red"
        controls_text.append(f"System Audio: {sys_audio}\n", style=f"bold {sys_color}")
        controls_text.append("F5: Toggle system audio\n", style="cyan")
        controls_text.append("F6: Select input device\n", style="cyan")
        
        controls_text.append("\nGeneral:\n", style="bold yellow")
        controls_text.append("ESC: Exit application\n", style="cyan")
        controls_text.append("F1: Show/hide hotkeys\n", style="cyan")
        
        return Panel(
            controls_text,
            title="[yellow]Controls & Hotkeys[/yellow]",
            border_style="yellow",
            padding=(0, 1)
        )

    def _make_layout(self):
        """Create the XTree-style layout with proper positioning."""
        layout = Layout()
        
        # Split into top and bottom sections
        layout.split_column(
            Layout(name="top", ratio=4),
            Layout(name="bottom", size=5)  # Bottom row for audio processing + VU
        )
        
        # Split top into left (transcript) and right (controls + devices)
        layout["top"].split_row(
            Layout(name="transcript", ratio=3),
            Layout(name="right_panel", size=45)
        )
        
        # Split right panel into controls (top) and devices (bottom)
        layout["right_panel"].split_column(
            Layout(name="controls", ratio=2),
            Layout(name="devices", size=8)  # Device list with multiple lines
        )
        
        # Split bottom into audio processing (left) and VU meter (right)
        layout["bottom"].split_row(
            Layout(name="audio_processing", ratio=3),
            Layout(name="vu", size=45)  # VU meter on bottom right
        )
        
        # Transcription log (top left - main area)
        trans_text = Text("\n".join(self.transcription_log[-30:]), style="white")
        trans_panel = Panel(
            trans_text,
            title="[yellow]Live Transcription[/yellow]",
            border_style="blue",
            padding=(1, 2),
            subtitle="(vertical scrolling)"
        )
        
        # Audio processing status (bottom left - two lines)
        live_panel = Panel(
            Text(self.live_audio_text, style="bold white"),
            title="[magenta]Audio Processing[/magenta]",
            border_style="magenta",
            padding=(0, 2)
        )
        
        # Horizontal VU meter panel (bottom right)
        vu_panel = Panel(
            self._make_stereo_vu_meter(self.vu_levels, height=3),
            title="[green]Stereo VU Meter[/green]",
            border_style="green",
            padding=(0, 1)
        )
        
        # Update layouts
        layout["transcript"].update(trans_panel)
        layout["audio_processing"].update(live_panel)
        layout["controls"].update(self._make_controls_panel())
        layout["devices"].update(self._make_device_panel())
        layout["vu"].update(vu_panel)
        
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

    def start_capture(self):
        self.is_capturing = True

    def stop_capture(self):
        self.is_capturing = False

    def toggle_capture(self):
        self.is_capturing = not self.is_capturing

    def set_current_file(self, filename):
        self.current_file = filename

    def toggle_system_audio(self):
        self.include_system_audio = not self.include_system_audio

    def select_device(self, device_index):
        self.selected_device_index = device_index

    def clear_transcription(self):
        self.transcription_log = []
