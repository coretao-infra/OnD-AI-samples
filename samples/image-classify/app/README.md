
# Image Classify App – Developer & Internal Notes

This document covers the internal structure, advanced configuration, and developer workflow for the `app/` package. For project-wide usage, normalization pipeline, and setup, see the main [README](../README.md).

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
