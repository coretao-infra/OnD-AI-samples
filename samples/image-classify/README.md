# Quick Start

1. **Clone and set up environment:**
  ```powershell
  git clone <repo-url>
  cd samples/image-classify
  .\scripts\setup.ps1
  ```
2. **Run the baseline generation script:**
  ```powershell
  python -m scripts.gen_baseline --profile <profile>
  ```
  - Input: `assets/input/img/`
  - Output: `assets/output/normalize-mk1/meta/metadata.csv`

---
# Windows On-Device AI Lab: Image Classifier (ONNX Runtime)

## Directory Structure

```text
image-classify/
├── app/           # App package (see app/README.md for internals)
├── assets/        # Input/output images and web assets
├── scripts/       # Setup and normalization scripts
├── README.md      # Main project documentation
└── ...
```

---
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

For app internals and developer notes, see [`app/README.md`](app/README.md).

This project includes a robust workflow for preparing image datasets for AI/ML classification. The normalization process is designed to:
- Analyze the actual distribution of image properties (resolution, compression, file size, color mode, etc.)
- Use an LLM (via Foundry Local) to recommend optimal normalization parameters that maximize consistency while minimizing unnecessary loss of richness
- Normalize images accordingly and randomize output filenames to remove source bias


---

## Detailed Normalization Design

This section expands on the normalization workflow, providing objectives, step-by-step design, and configuration structure for reproducible, data-driven image normalization.

### Objectives

- **Data-driven Normalization:**
  - Normalize a collection of images to a common baseline for downstream ML/classification tasks.
  - Avoid arbitrary downscaling or compression—preserve as much image richness as possible.
  - Determine normalization parameters (resolution, compression, file size, etc.) based on the actual characteristics of the current image set.
  - Use an LLM (via Foundry Local) to analyze metadata and recommend optimal normalization parameters.
  - Ensure the process is reproducible and well-logged for future reference.

### Step-by-Step Workflow

1. **Metadata Extraction (Mark 1):**
   - Use Python (Pillow, exifread, or similar) to extract for each image:
     - Dimensions (width, height)
     - Color mode (RGB, grayscale, etc.)
     - DPI (if available)
     - File size (bytes)
     - Compression level/quality (if available)
     - Any other relevant EXIF metadata
   - Store metadata in a structured format (e.g., CSV, DataFrame, or JSON).
   - **MCP-based Metadata Extraction (Alternative/Upgrade):**
     - Use the Model Context Protocol (MCP) image metadata extraction endpoint to extract rich metadata for each image.
     - The MCP tool can provide structured metadata including dimensions, color mode, DPI, file size, compression, EXIF, and more, in a single call.
     - Example workflow:
       1. Call the MCP endpoint with the input directory and desired profile (e.g., "rich").
       2. Receive a structured list of metadata for all images.
       3. Store or process as needed for downstream analysis.

2. **Metadata Analysis & Baseline Discovery (Mark 1):**
   - Summarize the distribution of key properties (e.g., histograms of width, height, file size).
   - Identify outliers and clusters (e.g., most common resolutions, file sizes).
   - Prepare a summary for LLM input (e.g., "Most images are 3000x2000, file sizes range 1-4MB, 90% are JPEG, ...").

3. **LLM-Assisted Baseline Selection (Mark 1):**
   - Use a self-initializing, config-driven LLM module (see `llm.py`) that:
     - Reads all LLM connection/model details from `config.ini` ([llm] section).
     - Initializes with a default meta prompt (`default_meta_prompt` in `[llm]`), which can be overridden at runtime.
     - The LLM module generically manages and prepends a meta/system prompt as configured or set at runtime, for any context or use case.
   - Use Foundry Local LLM to:
     - Review the metadata summary.
     - Recommend normalization parameters that maximize consistency while minimizing unnecessary loss (e.g., "resize only images above 2500px wide to 2048px, set JPEG quality to 85, ...").
     - Optionally, provide rationale for chosen parameters.

4. **Image Normalization (Mark 1):**
   - Apply the recommended normalization:
     - Downscale only if above baseline.
     - Adjust compression/quality as needed.
     - Convert color mode if required.
     - Save to output directory with randomized filenames (e.g., UUIDs).

5. **Output & Logging (Mark 1):**
   - Intended output is for AI image classification jobs
   - Randomize output filenames to remove source bias.
   - Save normalized images to a new directory.
   - Log mapping of original to new filenames and applied transformations.
   - Optionally, generate a report summarizing the normalization process and statistics.

#### Example Configuration Structure

```ini
[llm]
alias = phi-3.5-mini
variant = instruct-generic-gpu
endpoint = http://localhost:8000/v1
api_key =
default_meta_prompt = "You always prepend a warning in your responses that the default prompt is active."

[normalize]
normalize_meta_prompt = "You are a seasoned LM scientist's brain with powerful intuition encapsulated as an API responder."
```

---

For future plans and semantic-aware normalization (Mark 2), see the "Phase 2" section below.

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

### Parked/Future App Features

1.3. **Live Provider Switching**
  - Allow switching between CPU and DirectML (GPU) for inference in the app UI, and compare performance.

2.1. **CLI-Only Interface**
  - Add a command-line interface for image inference and results (if needed for headless/demo scenarios).

6.1. **Extensibility Hooks**
  - Add clear extension points for future features (e.g., Grad-CAM, saliency maps, custom postprocessing).
- Make padding optional in the normalization pipeline (allow disabling padding; default to crop-only).
- Implement interactive baseline-refinement loop in `scripts/gen_baseline.py`.
- Integrate LLM-assisted cropping and optional background padding logic.
- Strip metadata from output images and enforce output format conversion.
- Enhance logging and reporting of normalization statistics.

### Web UI & App Sample Extensions (for future contributors)

2. **Live Model Switching**
  - Add a dropdown in the web UI to switch between available ONNX models (e.g., MobileNetV2, ResNet50).
  - Instantly re-run inference on the last image with the new model.

3. **Image Preprocessing Visualization**
  - Show the original and preprocessed (normalized, resized, color-converted) image side-by-side in the UI.
  - Optionally, let the user toggle normalization steps to see their effect.

4. **Batch Upload & Results Table**
  - Allow uploading multiple images at once.
  - Show a table/grid of images with their top prediction and confidence.

8. **Workshop/Teaching Mode**
  - Step-by-step UI mode: walk users through upload, preprocessing, inference, and result interpretation.
  - Inline tooltips explaining each step and what’s happening on-device.

## Phase 2: Vision-Enabled Normalization (Mark 2)
In addition to the basic Mark 1 pipeline, leverage vision models and image analysis to further refine normalization:

- Straighten and deskew images by detecting and aligning to the majority orientation.
- Detect primary subjects or objects (e.g., via object detection or saliency mapping) and compute aggregate bounding boxes.
- Crop images tightly around detected content to remove excess background before resizing or compression.
- Re-center cropped subjects within the normalized frame to ensure consistent alignment across the dataset.
- Optionally apply minimal padding after subject-aware cropping to restore baseline dimensions while preserving aspect ratio.
- LLM should consider when padding/background may be useful (e.g., for document scans, portrait framing, or to meet model input requirements), not just default to no padding.
- Integrate specialized detectors (e.g., face detectors) for targeted crops in portrait datasets.
- Use saliency or attention maps to adaptively weight normalization parameters based on content importance.
- Automatically remove empty borders or margins using edge or contour detection.
- Normalize bit depth across the dataset (e.g., convert all images to 8-bit per channel for consistency).
- Implement vision-based background filling for padding instead of single color. Use semantic segmentation or inpainting to extend image context for padded regions.