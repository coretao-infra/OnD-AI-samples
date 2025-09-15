# Bench Project

## Overview
This project is designed to benchmark different LLM models using a menu-driven UI. It allows users to compare models based on various metrics such as token counts, response time, and more. The project is modular and extensible, making it easy to add new features and models.

## Instructions to Run
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd OnD-AI-samples/bench
   ```

2. Set up the virtual environment:
   ```bash
   .\.venv\Scripts\Activate.ps1  # For Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

## TODO
- [x] Implement the main logic in `app.py`.
- [x] Populate `config.py` to handle configuration loading and validation.
- [x] Develop the canonical helper in `llm.py` for model invocation.
- [x] Build the menu-driven UI in `menu.py`.
- [ ] Set up logging in `logging.py` for standardized log formatting and levels.
- [x] Validate and utilize `config.json` for backend and model configurations.
- [ ] Write detailed documentation in this `README.md` for contributing and advanced usage.
- [ ] Add progress indicator for caching models.
  - Implement a proper progress indicator to show the status of caching a model in the Foundry Local Model Manager.
- [x] Ensure viewing the configuration uses a canonical parse via `config.py` instead of a raw dump.
- [x] Create a real-time `display_inference` function that uses `rich` to display the prompt with stats asynchronously.
  - Clear the screen and split it into a larger top inference box and a bottom stats details box.
  - Display information such as:
    - Token window size.
    - Token size of user and system prompts.
    - Number of tokens generated so far.
    - Tokens per second so far.
- [ ] Save whether the model was loaded or not as part of the benchmark result, so it is captured in the output.
- [ ] Add functionality to query shared and dedicated VRAM accurately.
- [ ] Fix system RAM detection logic to ensure proper reporting.

## FUTURE
- [ ] Implement queuing for benchmarking tasks.

## Notes
- Ensure the virtual environment is activated before running any scripts.
- Use the `logging` module for debugging and tracking execution flow.