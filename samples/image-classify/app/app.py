import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.vision_actions import VisionActions
from utils.ux import create_main_window, create_image_area, create_controls_bar, create_status_label

class YoloVisionDemoApp:
    def __init__(self):
        self.root = create_main_window()
        # UI construction via utils.ux
        self.image_frame, self.image_label = create_image_area(self.root)
        self.controls_bar, self.open_button, self.detect_button = create_controls_bar(
            self.root, self.open_image, self.run_detection)
        self.status_label = create_status_label(self.controls_bar)
        # State
        self.imgtk = None
        self.vision = VisionActions()
        self.current_image = None
        self.current_image_path = None

    def open_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
        if not file_path:
            return
        try:
            img = Image.open(file_path).convert("RGB")
            img.thumbnail((640, 480))
            self.imgtk = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.imgtk, text="")
            self.current_image = img.copy()
            self.current_image_path = file_path
            self.detect_button.config(state="normal")
            self.status_label.config(text=f"Loaded: {os.path.basename(file_path)}")
        except Exception as e:
            self.image_label.config(text=f"Error loading image: {e}", image="")
            self.detect_button.config(state="disabled")
            self.status_label.config(text=f"Error: {e}")
            self.current_image = None
            self.current_image_path = None

    def run_detection(self):
        if self.current_image is None:
            return
        try:
            import numpy as np
            img = self.current_image.copy()
            img_np = np.array(img)
            self.status_label.config(text="Running detection...")
            results = self.vision.detect_objects(img_np)
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except Exception:
                font = ImageFont.load_default()
            for det in results[0] if isinstance(results, (list, tuple)) else []:
                if len(det) < 6:
                    continue
                x1, y1, x2, y2, conf, class_id = det[:6]
                label = f"{int(class_id)}: {conf:.2f}"
                draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
                draw.text((x1, y1 - 10), label, fill="red", font=font)
            self.imgtk = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.imgtk, text="")
            self.status_label.config(text="Detection complete.")
        except Exception as e:
            self.image_label.config(text=f"Detection error: {e}", image="")
            self.status_label.config(text=f"Detection error: {e}")

if __name__ == "__main__":
    app = YoloVisionDemoApp()
    app.root.mainloop()
