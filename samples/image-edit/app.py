import argparse
import io
import os
import sys
import threading
from dataclasses import dataclass
from typing import Optional

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
        self.status = tk.Label(root, textvariable=self.status_var, anchor="w")
        self.status.pack(fill=tk.X, padx=8)

        # Previews
        previews = tk.Frame(root)
        previews.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        left = tk.Frame(previews)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(left, text="Input").pack(anchor="w")
        self.in_canvas = tk.Label(left, bd=1, relief=tk.SOLID)
        self.in_canvas.pack(fill=tk.BOTH, expand=True, padx=(0, 4), pady=4)

        right = tk.Frame(previews)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(right, text="Output").pack(anchor="w")
        self.out_canvas = tk.Label(right, bd=1, relief=tk.SOLID)
        self.out_canvas.pack(fill=tk.BOTH, expand=True, padx=(4, 0), pady=4)

    def on_open(self):
        path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.webp"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            preview = load_image_for_preview(path)
        except Exception as e:
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

    def on_run(self):
        if not self.state.input_path:
            return
        self.run_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        self.status_var.set("Running on-device inference...")

        def work():
            try:
                with open(self.state.input_path, "rb") as f:
                    data = f.read()
                model_name = self.model_var.get()
                out_bytes = remove_bg_bytes(data, model_name)
                out_img = pil_from_bytes(out_bytes)
                preview = out_img.copy()
                preview.thumbnail((480, 480), Image.LANCZOS)
                # Update UI in main thread
                self.root.after(0, self._finish_run, out_img, preview)
            except Exception as e:
                self.root.after(0, self._error_run, e)

        threading.Thread(target=work, daemon=True).start()

    def _finish_run(self, out_img: Image.Image, preview: Image.Image):
        self.state.output_image = out_img
        self.state.preview_output = preview
        self.update_preview(self.out_canvas, preview)
        self.run_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.NORMAL)
        self.status_var.set("Done. You can Save PNG now.")

    def _error_run(self, e: Exception):
        self.run_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.DISABLED)
        messagebox.showerror("Error", f"Inference failed:\n{e}")
        self.status_var.set(f"Error: {e}")

    def on_save(self):
        if self.state.output_image is None:
            return
        out_path = filedialog.asksaveasfilename(
            title="Save output PNG",
            defaultextension=".png",
            filetypes=[("PNG", "*.png")]
        )
        if not out_path:
            return
        try:
            self.state.output_image.save(out_path, "PNG")
            self.status_var.set(f"Saved: {os.path.basename(out_path)}")
        except Exception as e:
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
        print("CLI mode requires --input and --output", file=sys.stderr)
        sys.exit(2)
    try:
        with open(args.input, "rb") as f:
            data = f.read()
        out_bytes = remove_bg_bytes(data, args.model)
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "wb") as f:
            f.write(out_bytes)
        print(f"Saved: {args.output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def parse_args():
    p = argparse.ArgumentParser(description="On-Device Background Remover (GUI + CLI)")
    p.add_argument("--input", type=str, help="Input image path (CLI mode)")
    p.add_argument("--output", type=str, help="Output PNG path (CLI mode)")
    p.add_argument("--model", type=str, default=DEFAULT_MODEL, choices=SUPPORTED_MODELS, help="Model to use")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.input and args.output:
        run_cli(args)
    else:
        root = tk.Tk()
        app = BackgroundRemoverApp(root)
        root.geometry("1000x650")
        root.mainloop()