# Major Improvements (2025-08)

## Config-Driven Pipeline
- All normalization, prompt structure, and allowed values are controlled via `app/config/config.ini`.
- Prompts use placeholders for schema, metadata summary, and one-shot examples.
- To change allowed color modes, edit `allowed_color_modes` in the `[normalize]` section.
- Validation logic enforces all config constraints, including allowed color modes and value ranges.
- The pipeline is robust to LLM quirks (e.g., outputting the actual most common color mode instead of the literal string "commonest").

## Example: Allowed Color Modes
```ini
[normalize]
allowed_color_modes = RGB, L, CMYK
```

## Extending the Pipeline
- Add new allowed_* entries in config and update the schema to extend validation to other fields.

# Image Classify App

## How to Run the App and Scripts

### 1. Environment Setup

- From the project root (`samples/image-classify`), run the setup script:
  ```powershell
  .\scripts\setup.ps1
  ```
- This will create a `.venv` and install dependencies from `requirements.txt`.

### 2. Running the Normalization Script

- From the project root (`samples/image-classify`), run:
  ```powershell
  python -m scripts.normalize
  ```
- This will use the configuration in `app/config/config.ini` and process images in `assets/input/img`.
- Output will be written to `assets/output/normalize-mk1/meta/metadata.csv`.

### 3. Notes
- All paths in the config are relative to the project root.
- You can edit `app/config/config.ini` to change input/output locations or schema.
- The project uses package-style imports for maintainability.

---

For more details, see the main project README or the design docs in `scripts/NORMALIZATION_DESIGN.md`.
