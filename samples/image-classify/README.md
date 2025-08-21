# Major Improvements (2025-08)

## Configuration-Driven Normalization Pipeline
- All normalization logic, prompt structure, and allowed values are controlled via `app/config/config.ini`.
- Prompts for the LLM are fully template-driven, with placeholders for schema, metadata summary, and one-shot examples.
- To change allowed color modes, edit `allowed_color_modes` in the `[normalize]` section.
- Validation logic enforces all config constraints, including allowed color modes and value ranges.
- The pipeline is robust to LLM quirks (e.g., outputting the actual most common color mode instead of the literal string "commonest").
- To extend validation to other fields, add new allowed_* entries in config and update the schema accordingly.

## Example: Allowed Color Modes
```ini
[normalize]
allowed_color_modes = RGB, L, CMYK
```

## Example: Baseline Output
```json
{
  "baseline_marker": "v1",
  "target_width": 2733,
  "target_height": 1448,
  "color_mode": "RGB",
  ...
}
```

## Extensibility
- All changes are made by editing the config, not the code.
- The config pattern can be extended to any other field (e.g., allowed formats, resize modes).


# Windows On-Device AI Lab: Image Classifier (ONNX Runtime)

## Project Context & Normalization Workflow

This project includes a robust workflow for preparing image datasets for AI/ML classification. The normalization process is designed to:
- Analyze the actual distribution of image properties (resolution, compression, file size, color mode, etc.)
- Use an LLM (via Foundry Local) to recommend optimal normalization parameters that maximize consistency while minimizing unnecessary loss of richness
- Normalize images accordingly and randomize output filenames to remove source bias

See `app/scripts/NORMALIZATION_DESIGN.md` for detailed objectives and design, including future plans for LLM-assisted cropping and enrichment.

### Minimal Project Structure

```text
image-classify/
├── app/
│   ├── scripts/
│   │   ├── NORMALIZATION_DESIGN.md
│   │   └── gen_baseline.py
│   ├── routes/
│   ├── templates/
│   └── utils/
├── assets/
│   ├── input/      # Raw images
│   ├── output/     # Normalized images
│   └── web/        # (Optional) Web assets
├── README.md
└── ...
```


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

## 📝 TODO / Roadmap
- Make padding optional in the normalization pipeline (allow disabling padding; default to crop-only).
- Implement interactive baseline-refinement loop in `scripts/gen_baseline.py`.
- Integrate LLM-assisted cropping and optional background padding logic.
- Strip metadata from output images and enforce output format conversion.
- Enhance logging and reporting of normalization statistics.