# Windows On-Device AI Lab: Background Remover (Python + ONNX Runtime)

This lab builds a small Windows desktop app that removes image backgrounds entirely on-device using ONNX Runtime (via the `rembg` library). After the first model download, it runs offline.

Why this is a good lab:
- Useful output: quickly create transparent PNGs of product shots, profile pics, etc.
- Fully local inference: showcases on-device AI.
- Easy setup: minimal code and dependencies.
- Windows GPU optional: works with DirectML if available.

## Prerequisites
- Windows 10/11
- Python 3.9–3.12 (from python.org)
- Optional for GPU: a DirectX 12-capable GPU and drivers

## Setup

```powershell
# 1) Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# 2) Install dependencies
pip install -r requirements.txt

# (Optional) Use GPU via DirectML. If you want GPU acceleration:
# Uninstall CPU runtime and install DirectML build (you can switch back anytime).
pip uninstall -y onnxruntime
pip install onnxruntime-directml
```

Notes:
- `rembg` will download the model on first run to your user cache. Default here is `u2netp` (small, quick). For higher quality later, switch to `isnet-general-use` in the UI dropdown.
- Everything runs locally; no data leaves your machine.

## Run

```powershell
python app.py
```

- Click "Open Image" to load a file (JPG/PNG).
- Choose a model (start with `u2netp` for speed).
- Click "Remove Background".
- Click "Save PNG" to export with transparency.

CLI mode (no GUI):
```powershell
python app.py --input path\to\image.jpg --output path\to\out.png --model u2netp
```

## Troubleshooting

- If you want GPU acceleration but don’t see it detected, ensure you installed `onnxruntime-directml` and have a DX12-capable GPU. The app shows the active providers (CPU/GPU) in the status bar.
- First run downloads the model (a few MB for `u2netp`; larger for `isnet-general-use`). Afterwards it runs fully offline.
- If Tkinter is missing, install a standard Python from python.org (it includes Tkinter on Windows).

## How it works

- The app uses `rembg` which wraps ONNX Runtime models for person/object segmentation (e.g., U^2-Net family, IS-Net).
- We create a session and run inference locally, returning a transparent PNG.
- ONNX Runtime CPU is used by default; if the DirectML build is installed, it can leverage your GPU.

## Try better quality

- Switch the model in-app to `isnet-general-use` for improved edges (larger download, slower on CPU, typically much better results).
- You can also try `u2net` (larger than `u2netp`) as a middle ground.

Enjoy building!