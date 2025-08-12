#!/usr/bin/env python3
"""
Simple audio oscilloscope - shows real-time audio levels
"""

import sounddevice as sd
import numpy as np
import time
import sys
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

console = Console()

def make_bar(value, max_width=50):
    """Create a simple ASCII bar graph"""
    if value < 0:
        return ""
    
    normalized = min(value / 32767, 1.0)  # Normalize to 0-1
    bar_length = int(normalized * max_width)
    bar = "█" * bar_length + "░" * (max_width - bar_length)
    return f"{bar} {value:6.0f}"

def audio_callback(indata, frames, time, status):
    """Audio callback - process each frame"""
    if status:
        console.print(f"Status: {status}", style="yellow")
    
    # Store the latest audio data
    audio_callback.latest_data = indata[:, 0]

# Initialize callback data
audio_callback.latest_data = np.zeros(1024)

def main():
    console.print("[bold blue]🎙️ Audio Oscilloscope[/bold blue]")
    console.print("This will show real-time audio levels from your microphone")
    console.print("Press Ctrl+C to stop\n")
    
    # List available devices
    console.print("[bold]Available input devices:[/bold]")
    devices = sd.query_devices()
    input_devices = []
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            marker = " <-- DEFAULT" if i == sd.default.device[0] else ""
            console.print(f"  {i}: {device['name']} ({device['max_input_channels']}ch @ {device['default_samplerate']:.0f}Hz){marker}")
            input_devices.append(i)
    
    # Use default or let user choose
    if len(sys.argv) > 1:
        device_id = int(sys.argv[1])
    else:
        try:
            device_id = sd.default.device[0]
            if device_id == -1:
                device_id = input_devices[0] if input_devices else None
        except:
            device_id = input_devices[0] if input_devices else None
    
    if device_id is None:
        console.print("[red]No input devices found![/red]")
        return
    
    device_info = sd.query_devices(device_id)
    console.print(f"\n[green]Using device {device_id}: {device_info['name']}[/green]")
    console.print(f"Sample rate: {device_info['default_samplerate']:.0f}Hz")
    
    # Start audio stream
    try:
        with sd.InputStream(
            device=device_id,
            channels=1,
            samplerate=device_info['default_samplerate'],
            callback=audio_callback,
            blocksize=1024
        ):
            console.print("\n[bold green]🎵 Audio stream started! Make some noise...[/bold green]\n")
            
            with Live(console=console, refresh_per_second=10) as live:
                while True:
                    try:
                        # Get latest audio data
                        audio_data = audio_callback.latest_data
                        
                        # Calculate statistics
                        max_val = np.max(np.abs(audio_data))
                        rms = np.sqrt(np.mean(audio_data**2))
                        
                        # Convert to int16 range for display
                        max_int16 = max_val * 32767
                        rms_int16 = rms * 32767
                        
                        # Create visualization
                        content = Text()
                        content.append("🎙️ AUDIO LEVELS\n\n", style="bold blue")
                        content.append(f"Max:  {make_bar(max_int16)}\n", style="red")
                        content.append(f"RMS:  {make_bar(rms_int16)}\n", style="green")
                        content.append(f"\nRaw values:\n")
                        content.append(f"  Peak: {max_val:.6f} ({max_int16:.0f})\n")
                        content.append(f"  RMS:  {rms:.6f} ({rms_int16:.0f})\n")
                        
                        # Activity indicator
                        if max_int16 > 1000:
                            content.append("\n🔊 AUDIO DETECTED!", style="bold green")
                        elif max_int16 > 100:
                            content.append("\n🔉 Quiet audio", style="yellow")
                        else:
                            content.append("\n🔇 Silence", style="dim")
                        
                        panel = Panel(content, title="Audio Oscilloscope", border_style="blue")
                        live.update(panel)
                        
                        time.sleep(0.1)
                        
                    except KeyboardInterrupt:
                        break
                        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1
    
    console.print("\n[blue]Stopped.[/blue]")
    return 0

if __name__ == "__main__":
    sys.exit(main())
