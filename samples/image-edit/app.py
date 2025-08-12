import argparse
import io
import os
import sys
import threading
from dataclasses import dataclass
from typing import Optional

# Use rich for all logging
from rich import print as rich_print
from rich.panel import Panel
from rich.console import Console

from PIL import Image, ImageTk

# rembg handles ONNX Runtime and model downloads internally
from rembg import remove, new_session

# Try to import onnxruntime to display provider info (CPU vs GPU DirectML)
try:
    import onnxruntime as ort
except Exception:
    ort = None

# Simple Tkinter GUI
import tkinter as tk
from tkinter import filedialog, messagebox

SUPPORTED_MODELS = [
    # Small and fast (good for labs)
    "u2netp",
    # Mid/large (better quality)
    "u2net",
    # High quality general model (larger download)
    "isnet-general-use",
]

DEFAULT_MODEL = "u2netp"


@dataclass
class AppState:
    input_path: Optional[str] = None
    output_image: Optional[Image.Image] = None
    preview_input: Optional[Image.Image] = None
    preview_output: Optional[Image.Image] = None
    session_cache: dict = None


def get_available_providers_str() -> str:
    if ort is None:
        return "ONNX Runtime not detected (rembg will manage)."
    try:
        providers = ort.get_available_providers()
        if "DmlExecutionProvider" in providers:
            return f"Providers: {providers} (GPU via DirectML detected)"
        return f"Providers: {providers} (CPU)"
    except Exception as e:
        return f"Providers: unknown ({e})"


def load_image_for_preview(path: str, max_size=(480, 480)) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    img.thumbnail(max_size, Image.LANCZOS)
    return img


def remove_bg_bytes(input_bytes: bytes, model_name: str) -> bytes:
    # new_session caches internally; we also cache per-model in our app state
    session = new_session(model_name)
    return remove(input_bytes, session=session)


def pil_from_bytes(b: bytes) -> Image.Image:
    return Image.open(io.BytesIO(b)).convert("RGBA")


class BackgroundRemoverApp:
    def __init__(self, root: tk.Tk):
        self.bg_path = os.path.join(os.path.dirname(__file__), "assets", "grain.jpeg")
        self.show_composite = tk.BooleanVar(value=False)
        self.root = root
        self.state = AppState(session_cache={})
        self.root.title("On-Device Background Remover (ONNX Runtime)")

        # Top bar: buttons and model selector
        top = tk.Frame(root)
        top.pack(fill=tk.X, padx=8, pady=8)

        self.open_btn = tk.Button(top, text="Open Image", command=self.on_open)
        self.open_btn.pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(top, text="Model:").pack(side=tk.LEFT)
        self.model_var = tk.StringVar(value=DEFAULT_MODEL)
        self.model_menu = tk.OptionMenu(top, self.model_var, *SUPPORTED_MODELS)
        self.model_menu.pack(side=tk.LEFT, padx=8)

        self.run_btn = tk.Button(top, text="Remove Background", command=self.on_run, state=tk.DISABLED)
        self.run_btn.pack(side=tk.LEFT, padx=8)

        self.save_btn = tk.Button(top, text="Save PNG", command=self.on_save, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=8)


        self.status_var = tk.StringVar(value=get_available_providers_str())
        self.status = tk.Label(self.root, textvariable=self.status_var, anchor="w")
        self.status.pack(fill=tk.X, padx=8)

        # Composite toggle
        self.composite_btn = tk.Checkbutton(top, text="Show on Background", variable=self.show_composite, command=self.update_output_preview)
        self.composite_btn.pack(side=tk.LEFT, padx=8)

        # Previews
        self.previews = tk.Frame(self.root)
        self.previews.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.left = tk.Frame(self.previews)
        self.left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(self.left, text="Input").pack(anchor="w")
        self.in_canvas = tk.Label(self.left, bd=1, relief=tk.SOLID)
        self.in_canvas.pack(fill=tk.BOTH, expand=True, padx=(0, 4), pady=4)

        self.right = tk.Frame(self.previews)
        self.right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(self.right, text="Output").pack(anchor="w")
        self.out_canvas = tk.Label(self.right, bd=1, relief=tk.SOLID)
        self.out_canvas.pack(fill=tk.BOTH, expand=True, padx=(4, 0), pady=4)

    def on_open(self):
        rich_print("[bold cyan][INFO][/bold cyan] Open Image dialog triggered.")
        path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.webp"), ("All files", "*.*")]
        )
        if not path:
            rich_print("[yellow][INFO][/yellow] No image selected.")
            return
        try:
            rich_print(f"[bold cyan][INFO][/bold cyan] Loading image: [white]{path}[/white]")
            preview = load_image_for_preview(path)
        except Exception as e:
            rich_print(f"[bold red][ERROR][/bold red] Failed to open image: {e}")
            messagebox.showerror("Error", f"Failed to open image:\n{e}")
            return

        self.state.input_path = path
        self.state.preview_input = preview
        self.state.output_image = None
        self.state.preview_output = None
        self.update_preview(self.in_canvas, preview)
        self.update_preview(self.out_canvas, None)
        self.run_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.DISABLED)
        self.status_var.set(f"Loaded: {os.path.basename(path)} | {get_available_providers_str()}")
        rich_print(f"[bold cyan][INFO][/bold cyan] Image loaded and preview updated: [white]{os.path.basename(path)}[/white]")

    def on_run(self):
        if not self.state.input_path:
            rich_print("[bold yellow][WARN][/bold yellow] Run triggered but no input image loaded.")
            return
        self.run_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        self.status_var.set("Running on-device inference...")
        rich_print(f"[bold cyan][INFO][/bold cyan] Starting background removal for: [white]{self.state.input_path}[/white]")

        def work():
            import time
            try:
                self._last_infer_start = time.time()
                with open(self.state.input_path, "rb") as f:
                    data = f.read()
                model_name = self.model_var.get()
                rich_print(f"[bold cyan][INFO][/bold cyan] Using model: [white]{model_name}[/white]")
                rich_print("[bold cyan][INFO][/bold cyan] Downloading model if needed and running inference...")
                out_bytes = remove_bg_bytes(data, model_name)
                out_img = pil_from_bytes(out_bytes)
                preview = out_img.copy()
                preview.thumbnail((480, 480), Image.LANCZOS)
                self._last_infer_end = time.time()
                rich_print(f"[bold green][INFO][/bold green] Inference complete in [white]{self._last_infer_end-self._last_infer_start:.2f}[/white] seconds.")
                # Update UI in main thread
                self.root.after(0, self._finish_run, out_img, preview)
            except Exception as e:
                rich_print(f"[bold red][ERROR][/bold red] Inference failed: {e}")
                self.root.after(0, self._error_run, e)

        threading.Thread(target=work, daemon=True).start()

    def _finish_run(self, out_img: Image.Image, preview: Image.Image):
        rich_print("[bold green][INFO][/bold green] Background removal finished. Output image ready.")
        self.state.output_image = out_img
        self.state.preview_output = preview
        self.update_output_preview()
        self.run_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.NORMAL)
        self.status_var.set("Done. You can Save PNG now.")

        # Rich log entry
        try:
            import datetime
            width, height = out_img.size
            pixels = width * height
            model = self.model_var.get()
            mode = out_img.mode
            # Input file details
            input_path = self.state.input_path or "?"
            input_name = os.path.basename(input_path)
            try:
                input_size = os.path.getsize(input_path)
                for unit in ['B','KB','MB','GB']:
                    if input_size < 1024.0:
                        break
                    input_size /= 1024.0
                input_size_str = f"{input_size:.2f} {unit}"
            except Exception:
                input_size_str = "?"
            # HW provider
            try:
                providers = ort.get_available_providers()
                if "DmlExecutionProvider" in providers:
                    hw = f"GPU (DirectML): {providers}"
                else:
                    hw = f"CPU: {providers}"
            except Exception as e:
                hw = f"Unknown ({e})"
            # Benchmark: pixels/sec and time
            t0 = getattr(self, '_last_infer_start', None)
            t1 = getattr(self, '_last_infer_end', None)
            if t0 and t1 and t1 > t0:
                px_per_sec = int(pixels / (t1 - t0))
                bench = f"{px_per_sec:,} px/sec"
                elapsed = t1 - t0
                elapsed_str = f"{elapsed:.2f} sec"
            else:
                bench = "N/A"
                elapsed_str = "?"
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rich_print(Panel(
                f"[bold green]Background Removal Complete[/bold green]\n"
                f"[white]Input:[/white] [bold]{input_name}[/bold]  ([cyan]{input_size_str}[/cyan])\n"
                f"[white]Mode:[/white] [magenta]{mode}[/magenta]\n"
                f"Model: [cyan]{model}[/cyan]\n"
                f"Resolution: [yellow]{width}x{height}[/yellow] ([white]{pixels:,} px[/white])\n"
                f"HW: [magenta]{hw}[/magenta]\n"
                f"Benchmark: [bold]{bench}[/bold]  |  Time: [bold]{elapsed_str}[/bold]\n"
                f"[dim]Processed: {timestamp}[/dim]",
                title="[white on blue] Image Stats ", expand=False))
        except Exception as e:
            rich_print(f"[yellow][WARN][/yellow] Could not print rich log: {e}")

    def update_output_preview(self):
        if self.state.preview_output is None:
            self.update_preview(self.out_canvas, None)
            return
        if self.show_composite.get():
            try:
                bg = Image.open(self.bg_path).convert("RGBA")
                fg = self.state.preview_output
                # Resize bg to match fg
                bg = bg.resize(fg.size, Image.LANCZOS)
                composite = Image.alpha_composite(bg, fg)
                self.update_preview(self.out_canvas, composite)
            except Exception as e:
                print(f"[ERROR] Failed to composite background: {e}")
                self.update_preview(self.out_canvas, self.state.preview_output)
        else:
            self.update_preview(self.out_canvas, self.state.preview_output)

    def _error_run(self, e: Exception):
        rich_print(f"[bold red][ERROR][/bold red] {e}")
        self.run_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.DISABLED)
        messagebox.showerror("Error", f"Inference failed:\n{e}")
        self.status_var.set(f"Error: {e}")

    def on_save(self):
        if self.state.output_image is None:
            rich_print("[bold yellow][WARN][/bold yellow] Save triggered but no output image available.")
            return
        out_path = filedialog.asksaveasfilename(
            title="Save output PNG",
            defaultextension=".png",
            filetypes=[("PNG", "*.png")]
        )
        if not out_path:
            rich_print("[yellow][INFO][/yellow] Save dialog cancelled.")
            return
        try:
            self.state.output_image.save(out_path, "PNG")
            self.status_var.set(f"Saved: {os.path.basename(out_path)}")
            rich_print(f"[bold green][INFO][/bold green] Output image saved: [white]{out_path}[/white]")
        except Exception as e:
            rich_print(f"[bold red][ERROR][/bold red] Failed to save image: {e}")
            messagebox.showerror("Error", f"Failed to save image:\n{e}")

    def update_preview(self, widget: tk.Label, pil_img: Optional[Image.Image]):
        if pil_img is None:
            widget.config(image="", text="(no image)")
            widget.image = None
            return
        tk_img = ImageTk.PhotoImage(pil_img)
        widget.config(image=tk_img, text="")
        widget.image = tk_img  # keep ref


def run_cli(args: argparse.Namespace):
    # CLI mode for headless usage
    if not args.input or not args.output:
        rich_print("[bold red][ERROR][/bold red] CLI mode requires --input and --output")
        sys.exit(2)
    try:
        with open(args.input, "rb") as f:
            data = f.read()
        out_bytes = remove_bg_bytes(data, args.model)
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "wb") as f:
            f.write(out_bytes)
        rich_print(f"[bold green][INFO][/bold green] Saved: [white]{args.output}[/white]")
    except Exception as e:
        rich_print(f"[bold red][ERROR][/bold red] {e}")
        sys.exit(1)


def parse_args():
    p = argparse.ArgumentParser(description="On-Device Background Remover (GUI + CLI)")
    p.add_argument("--input", type=str, help="Input image path (CLI mode)")
    p.add_argument("--output", type=str, help="Output PNG path (CLI mode)")
    p.add_argument("--model", type=str, default=DEFAULT_MODEL, choices=SUPPORTED_MODELS, help="Model to use")
    return p.parse_args()


if __name__ == "__main__":
    import time
    args = parse_args()
    if args.input and args.output:
        rich_print(f"[bold cyan][INFO][/bold cyan] CLI mode: input=[white]{args.input}[/white], output=[white]{args.output}[/white], model=[white]{args.model}[/white]")
        run_cli(args)
    else:
        rich_print("[bold cyan][INFO][/bold cyan] Starting Background Remover GUI...")
        root = tk.Tk()
        app = BackgroundRemoverApp(root)
        rich_print("[bold cyan][INFO][/bold cyan] GUI window created. Waiting for user action.")
        root.geometry("1000x650")
        root.mainloop()