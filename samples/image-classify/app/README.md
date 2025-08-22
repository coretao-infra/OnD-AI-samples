
# App Plan: YOLOv8 Vision Demo (Multi-Task)

This document outlines the plan and developer notes for building a YOLOv8-based on-device vision demo, optimized for AMD APU/DirectML and a local desktop GUI (Tkinter). The demo will showcase multiple YOLOv8 vision tasks, starting from the easiest and most visually impactful, progressing to more advanced capabilities. The main user experience is a simple, interactive desktop app.

---


## App Objectives & Demo Task Plan

**YOLOv8 Vision Tasks to Showcase (in demo order):**

1. **Object Detection (Low Hanging Fruit)**
  - Draw bounding boxes and class labels on images.
  - Fast, reliable, and visually impactful.

2. **Instance Segmentation (More Interesting/Fun)**
  - Draw pixel-precise masks over detected objects.
  - Visually impressive and demonstrates advanced model capability.

3. **Pose/Keypoints Detection (Fun/Engaging)**
  - Detect and draw human/animal skeletons (keypoints) on images.
  - Interactive and memorable for audiences.

4. **Oriented Object Detection (Sophisticated/Complex)**
  - Detect rotated objects and draw oriented bounding boxes.
  - Advanced use case, impressive for technical audiences.

5. **Classification (Optional/Completeness)**
  - Predict the main class of an image (no boxes, just a label).
  - Easy to add, but less visually exciting.

---

---


## Implementation Plan (Developer-Focused)

**Recommended Python Libraries:**
- `onnxruntime` (with DirectML provider) — for ONNX inference on AMD APU
- `opencv-python` — for image preprocessing, drawing, and visualization
- `numpy` — for array manipulation
- `tkinter` — for the local GUI (built-in with Python)
- `pillow` — for image I/O and Tkinter image display

**Steps:**

1. **Model Integration**
  - Download/export YOLOv8n/s ONNX models for each task (detection, segmentation, pose, etc.).
  - Set up ONNX Runtime with DirectML provider for AMD APU compatibility.
  - Implement image preprocessing (resize, normalization) to match YOLOv8 input requirements.
  - Implement postprocessing for each task:
    - Detection: bounding boxes, class labels, confidence
    - Segmentation: masks overlay
    - Pose: keypoints overlay
    - Oriented detection: rotated boxes
    - Classification: top class label

2. **Local GUI Development (Tkinter)**
  - Build a simple, cross-platform desktop GUI using Tkinter.
  - Support image upload via file picker (and optionally drag-and-drop).
  - Display the original image with results overlaid (boxes, masks, keypoints, etc.) in the GUI window.
  - Show a table or list of detected objects, classes, and confidence scores below or beside the image.
  - Add optional features: "Surprise Me!" button, system info panel, confidence/class filters, and real-time feedback.

3. **Demo/Workshop Enhancements**
  - Display inference time and ONNX provider in the UI.
  - Add tooltips or info boxes to explain on-device inference and hardware usage.
  - Provide clear error handling and user feedback.

4. **Testing & Optimization**
  - Test on AMD APU hardware with DirectML.
  - Optimize for speed and responsiveness.
  - Document any known limitations or fallback options (e.g., fallback to YOLOv5s if needed).

---

# Parked/Future Ideas

- Live provider switching (CPU vs. DirectML) [see project TODO]
- CLI-only interface (focus is on web UI for demo)
- Extensibility hooks for advanced features (see project TODO)

---

## Directory Structure (app/)

- `app.py` — (Entry point, if used as a standalone app)
- `config/` — Configuration files
  - `config.ini` — Main config for normalization, LLM, etc.
  - `meta_schema_profiles.json` — Metadata schema profiles
- `routes/` — (Reserved for API or web routes; currently placeholder)
- `templates/` — (Reserved for HTML or other templates; currently placeholder)
- `utils/` — Core logic modules:
  - `baseline_util.py` — Baseline discovery and analysis helpers
  - `config.py` — Config parsing and validation
  - `llm.py` — LLM prompt and connection logic
  - `metadata.py` — Metadata extraction helpers
  - `normalize_file.py` — Image normalization routines
- `__init__.py` — Makes `app` a Python package

---

## Advanced Configuration

- All normalization, prompt structure, and allowed values are controlled via `config/config.ini`.
- To change allowed color modes, edit `allowed_color_modes` in the `[normalize]` section.
- To extend validation, add new `allowed_*` entries in config and update the schema/profile as needed.
- Prompts for the LLM are template-driven, with placeholders for schema, metadata summary, and one-shot examples.

---

## Developer Workflow

1. **Environment Setup**
  - From the project root (`samples/image-classify`), run:
    ```powershell
    .\scripts\setup.ps1
    ```
  - This creates a `.venv` and installs dependencies from `requirements.txt`.

2. **Running Baseline Generation**
  - From the project root, run:
    ```powershell
    python -m scripts.gen_baseline --profile <profile>
    ```
  - Uses config in `app/config/config.ini` and processes images in `assets/input/img`.
  - Output: `assets/output/normalize-mk1/meta/metadata.csv`.

3. **Notes**
  - All config paths are relative to the project root.
  - You can edit `app/config/config.ini` to change input/output locations or schema.
  - The project uses package-style imports for maintainability.

---

## Extending the App

- Add new modules to `utils/` for additional normalization or metadata logic.
- Add routes or templates as needed for web/API extensions.
- Update `config.ini` and schema/profile files to support new fields or validation rules.

---

## Troubleshooting & Tips

- If you encounter import errors, ensure you are running from the project root and the virtual environment is activated.
- For LLM or config issues, check `config/config.ini` and logs/output for error details.

---

For project-wide context, normalization pipeline, and user instructions, see the main [README](../README.md).


# Image Classify App – Developer & Internal Notes

This document covers the internal structure, advanced configuration, and developer workflow for the `app/` package. For project-wide usage, normalization pipeline, and setup, see the main [README](../README.md).

---

## App Objectives

**Core Demo Goals:**

1. **On-Device Inference (ONNX, DirectML/CPU):**
  - Load a normalized image and run it through a local ONNX classifier (e.g., MobileNetV2).
  - Display top-5 predictions with confidence scores.

2. **Minimal Web UI:**
  - Provide a simple web interface for drag-and-drop or file picker image upload.
  - Show the image and predictions in the browser for instant feedback.

---

# Parked/Future Ideas

- Live provider switching (CPU vs. DirectML) [see project TODO]
- CLI-only interface (focus is on web UI for demo)
- Extensibility hooks for advanced features (see project TODO)

---

---

## Directory Structure (app/)

- `app.py` — (Entry point, if used as a standalone app)
- `config/` — Configuration files
  - `config.ini` — Main config for normalization, LLM, etc.
  - `meta_schema_profiles.json` — Metadata schema profiles
- `routes/` — (Reserved for API or web routes; currently placeholder)
- `templates/` — (Reserved for HTML or other templates; currently placeholder)
- `utils/` — Core logic modules:
  - `baseline_util.py` — Baseline discovery and analysis helpers
  - `config.py` — Config parsing and validation
  - `llm.py` — LLM prompt and connection logic
  - `metadata.py` — Metadata extraction helpers
  - `normalize_file.py` — Image normalization routines
- `__init__.py` — Makes `app` a Python package

---

## Advanced Configuration

- All normalization, prompt structure, and allowed values are controlled via `config/config.ini`.
- To change allowed color modes, edit `allowed_color_modes` in the `[normalize]` section.
- To extend validation, add new `allowed_*` entries in config and update the schema/profile as needed.
- Prompts for the LLM are template-driven, with placeholders for schema, metadata summary, and one-shot examples.

---

## Developer Workflow

1. **Environment Setup**
   - From the project root (`samples/image-classify`), run:
     ```powershell
     .\scripts\setup.ps1
     ```
   - This creates a `.venv` and installs dependencies from `requirements.txt`.

2. **Running Baseline Generation**
   - From the project root, run:
     ```powershell
     python -m scripts.gen_baseline --profile <profile>
     ```
   - Uses config in `app/config/config.ini` and processes images in `assets/input/img`.
   - Output: `assets/output/normalize-mk1/meta/metadata.csv`.

3. **Notes**
   - All config paths are relative to the project root.
   - You can edit `app/config/config.ini` to change input/output locations or schema.
   - The project uses package-style imports for maintainability.

---

## Extending the App

- Add new modules to `utils/` for additional normalization or metadata logic.
- Add routes or templates as needed for web/API extensions.
- Update `config.ini` and schema/profile files to support new fields or validation rules.

---

## Troubleshooting & Tips

- If you encounter import errors, ensure you are running from the project root and the virtual environment is activated.
- For LLM or config issues, check `config/config.ini` and logs/output for error details.

---

For project-wide context, normalization pipeline, and user instructions, see the main [README](../README.md).
