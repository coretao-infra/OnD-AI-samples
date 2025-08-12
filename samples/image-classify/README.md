# Windows On-Device AI Lab: Image Classifier (ONNX Runtime)

This lab builds a small desktop or CLI tool that classifies images with a local ONNX model (e.g., MobileNetV2 or ResNet50). It runs entirely on-device and can optionally use your GPU via DirectML on Windows.

Why this is a good lab
- Useful: quickly identify objects in images.
- Fully local inference: no network calls after the first model download.
- Simple: minimal preprocessing and a single forward pass.

What you build
- A simple app that:
  - Loads an ONNX classifier (MobileNetV2 by default)
  - Preprocesses an image (resize/crop/normalize)
  - Runs inference with ONNX Runtime
  - Displays top-5 labels with confidences

Optional
- Small Tkinter GUI (drag-and-drop or “Open Image”).
- GPU acceleration with onnxruntime-directml.

## Prerequisites

- Windows 10/11
- Python 3.9–3.12
- Optional GPU: DirectX 12-capable GPU and drivers (for DirectML)

## Setup

```powershell
# 1) Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# 2) Install dependencies (CPU by default)
pip install onnxruntime pillow numpy

# 3) (Optional) Use GPU via DirectML on Windows:
pip uninstall -y onnxruntime
pip install onnxruntime-directml
```

Model files
- Use MobileNetV2 or ResNet50 ONNX classifiers trained on ImageNet.
- Your app can auto-download the model and labels on first run and cache them locally.
- ImageNet class labels are typically provided as a 1000-line text file (index → class).

## Run

GUI (if included):
```powershell
python app.py
```

CLI (typical flags your app can support):
```powershell
python app.py --image path\to\image.jpg --model mobilenetv2 --topk 5
```

Suggested flags (implement as appropriate in your app.py)
- --image: input image path
- --model: mobilenetv2 | resnet50 (you can support others if you add pre/postprocess logic)
- --topk: number of results to show (default 5)

## How it works

1) Preprocess
- Resize shortest side to 256, center-crop to 224x224.
- Convert to RGB, float32 tensor, normalize with ImageNet mean/std:
  - mean = [0.485, 0.456, 0.406]
  - std = [0.229, 0.224, 0.225]
- Reorder to NCHW (1, 3, 224, 224).

2) Inference
- Create an ONNX Runtime session (CPU or DirectML).
- Run forward pass on the preprocessed tensor.

3) Postprocess
- Apply softmax to logits, pick top-k indices.
- Map indices to human-readable class names via labels file.

## GPU and providers

- CPU: `onnxruntime` uses CPUExecutionProvider.
- GPU: `onnxruntime-directml` enables DmlExecutionProvider on Windows (works across vendors).
- You can display active providers in-app:
  - In Python:
    ```python
    import onnxruntime as ort
    print(ort.get_available_providers())
    ```

## Troubleshooting

- Model mismatch: ensure input dims and normalization match your chosen model.
- Slow inference on CPU: try smaller models (MobileNetV2) or enable DirectML.
- Pillow errors: ensure the image is a supported format and not corrupted.
- First-run download blocked: if your environment restricts downloads, place model/labels files in a known local path and configure the app to load from there.

## Next steps

- Add drag-and-drop support and a simple preview thumbnail.
- Batch classify a folder and write results to CSV.
- Add Grad-CAM or saliency visualization to explain predictions.