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
- [ ] Implement the main logic in `app.py`.
- [ ] Populate `config.py` to handle configuration loading and validation.
- [ ] Develop the canonical helper in `llm.py` for model invocation.
- [ ] Build the menu-driven UI in `menu.py`.
- [ ] Set up logging in `logging.py` for standardized log formatting and levels.
- [ ] Validate and utilize `config.json` for backend and model configurations.
- [ ] Add unit tests in a `tests` folder.
- [ ] Write detailed documentation in this `README.md` for contributing and advanced usage.

## Notes
- Ensure the virtual environment is activated before running any scripts.
- Use the `logging` module for debugging and tracking execution flow.