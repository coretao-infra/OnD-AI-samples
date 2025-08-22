import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

class YoloVisionDemoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLOv8 Vision Demo (Tkinter)")
        self.image_label = tk.Label(root, text="Open an image to begin", width=60, height=20, bg="#eee")
        self.image_label.pack(padx=10, pady=10)
        self.open_button = tk.Button(root, text="Open Image", command=self.open_image)
        self.open_button.pack(pady=5)
        self.imgtk = None  # Keep reference to avoid garbage collection

    def open_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
        if not file_path:
            return
        img = Image.open(file_path)
        img.thumbnail((640, 480))
        self.imgtk = ImageTk.PhotoImage(img)
        self.image_label.config(image=self.imgtk, text="")

if __name__ == "__main__":
    root = tk.Tk()
    app = YoloVisionDemoApp(root)
    root.mainloop()
