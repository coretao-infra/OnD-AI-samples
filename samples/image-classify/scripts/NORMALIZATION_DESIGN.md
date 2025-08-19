#
# Using .vscode/mcp.json to Start the MCP Server in VS Code

To start the Image Metadata MCP server for local testing in VS Code:

1. Ensure your Python virtual environment is set up and dependencies are installed.
2. Open the Command Palette (`Ctrl+Shift+P`) in VS Code.
3. Run the command: `MCP: Start Server` (or similar, depending on your MCP extension).
4. Select the `ImageMetadata` server defined in `.vscode/mcp.json`.
  - This will launch the server using the specified Python environment and arguments.
5. The server will run in the background and can be used for metadata extraction and testing.

You can edit `.vscode/mcp.json` to add or modify MCP server definitions as needed for your project.

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

#### MCP-based Metadata Extraction (Alternative/Upgrade)
- Use the Model Context Protocol (MCP) image metadata extraction endpoint to extract rich metadata for each image.
- The MCP tool can provide structured metadata including dimensions, color mode, DPI, file size, compression, EXIF, and more, in a single call.
- Example workflow:
  1. Call the MCP endpoint with the input directory and desired profile (e.g., "rich").
  2. Receive a structured list of metadata for all images.
  3. Store or process as needed for downstream analysis.
- **TODO:** The call to list available profiles is probably unnecessary for most MCP tooling, as the required profile is usually known in advance or can be set as a default.

### 2. Metadata Analysis & Baseline Discovery (Mark 1)
- Summarize the distribution of key properties (e.g., histograms of width, height, file size).
- Identify outliers and clusters (e.g., most common resolutions, file sizes).
- Prepare a summary for LLM input (e.g., "Most images are 3000x2000, file sizes range 1-4MB, 90% are JPEG, ...").

### 3. LLM-Assisted Baseline Selection (Mark 1)
- Use a self-initializing, config-driven LLM module (see `llm.py`) that:
  - Reads all LLM connection/model details from `config.ini` ([llm] section).
  - Initializes with a default meta prompt (`default_meta_prompt` in `[llm]`), which can be overridden at runtime.
  - The LLM module generically manages and prepends a meta/system prompt as configured or set at runtime, for any context or use case.
  - Prepends the meta/system prompt to all LLM chat requests for context control.
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


## Configuration Structure (as of Mark 1)

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

# Phase 2: Mark 2 - Semantic-Aware Normalization

In Mark 2, use image classification or object detection to further enrich the baseline. For example, determine the optimum crop box for each image to maintain maximum object focus, or adapt normalization parameters based on image content.