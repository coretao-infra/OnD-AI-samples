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
