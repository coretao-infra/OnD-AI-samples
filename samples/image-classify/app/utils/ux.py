"""
ux.py: UI utility functions and layout helpers for the YOLOv8 Vision Demo app.
- Provides reusable, DRY, and visually welcoming UI construction for Tkinter.
- Centralizes widget creation, layout, and style for a consistent, expandable UX.
"""
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

def create_main_window(title="YOLOv8 Vision Demo (Tkinter)"):
    root = tk.Tk()
    root.title(title)
    root.minsize(900, 650)
    root.configure(bg="#f7f7fa")
    return root

def create_image_area(parent):
    frame = tk.Frame(parent, bg="#f7f7fa", relief="groove", bd=2)
    frame.pack(fill="both", expand=True, padx=30, pady=(30, 10))
    image_label = tk.Label(frame, text="👋 Welcome!\nOpen an image to get started.",
        bg="#f7f7fa", fg="#444", font=("Segoe UI", 16, "bold"), justify="center")
    image_label.pack(expand=True)
    return frame, image_label

def create_controls_bar(parent, on_open, on_detect):
    bar = tk.Frame(parent, bg="#f7f7fa")
    bar.pack(fill="x", padx=30, pady=(0, 20))
    open_btn = ttk.Button(bar, text="Open Image", command=on_open)
    open_btn.pack(side="left", padx=(0, 12), ipadx=8, ipady=4)
    detect_btn = ttk.Button(bar, text="Run Detection", command=on_detect, state="disabled")
    detect_btn.pack(side="left", ipadx=8, ipady=4)
    return bar, open_btn, detect_btn

def create_status_label(parent):
    status = tk.Label(parent, text="", anchor="w", fg="#666", bg="#f7f7fa", font=("Segoe UI", 10))
    status.pack(side="left", padx=(20, 0), fill="x", expand=True)
    return status
