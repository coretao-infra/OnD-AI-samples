# Image Collection Normalization: Objectives & Design

_This document describes the normalization workflow for preparing image datasets for AI/ML classification, with a focus on maximizing data richness and reproducibility._


## Objectives

- **Data-driven Normalization:**
  - Normalize a collection of images to a common baseline for downstream ML/classification tasks.
  - Avoid arbitrary downscaling or compression—preserve as much image richness as possible.
  - Determine normalization parameters (resolution, compression, file size, etc.) based on the actual characteristics of the current image set.
  - Use an LLM (via Foundry Local) to analyze metadata and recommend optimal normalization parameters.
  - Ensure the process is reproducible and well-logged for future reference.

## Proposed Design

### 1. Metadata Extraction (Mark 1)
- Use Python (Pillow, exifread, or similar) to extract for each image:
  - Dimensions (width, height)
  - Color mode (RGB, grayscale, etc.)
  - DPI (if available)
  - File size (bytes)
  - Compression level/quality (if available)
  - Any other relevant EXIF metadata
- Store metadata in a structured format (e.g., CSV, DataFrame, or JSON).

### 2. Metadata Analysis & Baseline Discovery (Mark 1)
- Summarize the distribution of key properties (e.g., histograms of width, height, file size).
- Identify outliers and clusters (e.g., most common resolutions, file sizes).
- Prepare a summary for LLM input (e.g., "Most images are 3000x2000, file sizes range 1-4MB, 90% are JPEG, ...").

### 3. LLM-Assisted Baseline Selection (Mark 1)
- Use Foundry Local LLM to:
  - Review the metadata summary.
  - Recommend normalization parameters that maximize consistency while minimizing unnecessary loss (e.g., "resize only images above 2500px wide to 2048px, set JPEG quality to 85, ...").
  - Optionally, provide rationale for chosen parameters.

### 4. Image Normalization (Mark 1)
- Apply the recommended normalization:
  - Downscale only if above baseline.
  - Adjust compression/quality as needed.
  - Convert color mode if required.
  - Save to output directory with randomized filenames (e.g., UUIDs).

### 5. Output & Logging (Mark 1)
- Intended output is for AI image classification jobs
- Randomize output filenames to remove source bias.
- Save normalized images to a new directory.
- Log mapping of original to new filenames and applied transformations.
- Optionally, generate a report summarizing the normalization process and statistics.

---

## Next Steps
- Implement metadata extraction and summary.
- Prepare LLM prompt and integrate with Foundry Local.
- Build normalization pipeline.
- Test and validate output quality.

# Phase 2: Mark 2 - Semantic-Aware Normalization

In Mark 2, use image classification or object detection to further enrich the baseline. For example, determine the optimum crop box for each image to maintain maximum object focus, or adapt normalization parameters based on image content.