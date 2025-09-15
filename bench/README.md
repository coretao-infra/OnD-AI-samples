# Bench Project

## Overview
This project is designed to benchmark different LLM models using a menu-driven UI. It allows users to compare models based on various metrics such as token counts, response time, and more. The project is modular and extensible, making it easy to add new features and models.


## How to Run Benchmarks
1. **Clone the repository:**
   ```powershell
   git clone <repository-url>
   cd OnD-AI-samples/bench
   ```

2. **Set up the virtual environment:**
   ```powershell
   .\.venv\Scripts\Activate.ps1  # For Windows
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Run the benchmark menu:**
   ```powershell
   python -m app
   ```

## Using the Benchmark Menu
When you run `python -m app`, you'll see a menu like this:

```
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Option ┃ Description               ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│   1    │ List Backends             │
│   2    │ Select Backend            │
│   3    │ List Models               │
│   4    │ Run Benchmark             │
│   5    │ List All Available Models │
│   6    │ Display CPU/NPU/GPU Info  │
│   9    │ Exit                      │
└────────┴───────────────────────────┘
```

### To run a benchmark:
1. Select option `4` (Run Benchmark).
2. Choose a model from the displayed list by entering its number.
3. The benchmark will run and stream the model's response and stats to the console.

### To view hardware info:
Select option `6` to display details about your CPU, NPU, GPU, and system RAM.

## Where is Benchmark Output Saved?
Benchmark results are automatically saved to:

```
bench/output/bench_result.json
```

This file contains a list of all benchmark runs, including:
- Model ID and alias
- Device type (CPU, GPU, NPU, etc.)
- Backend used
- Token counts
- Latency
- Hardware details (CPU, GPU, NPU names, system RAM)
- Silicon type (CPU, GPU, NPU, Remote, Cloud)
- Timestamp

## Example Benchmark Output
```json
[
  {
    "input_tokens": 67,
    "output_tokens": 987,
    "total_tokens": 1054,
    "latency_ms": 106173,
    "model": "Phi-4-mini-reasoning-qnn-npu",
    "backend": "FoundryLocal",
    "timestamp": "2025-09-15T14:04:15.308802Z",
    "is_model_loaded": false,
    "gpu_name": "Qualcomm(R) Adreno(TM) X1-45 GPU",
    "cpu_name": "Snapdragon(R) X Plus - X1P42100 - Qualcomm(R) Oryon(TM) CPU",
    "npu_name": "Snapdragon(R) X Plus - X1P42100 - Qualcomm(R) Hexagon(TM) NPU",
    "system_memory_gb": 31.57,
    "silicon": "NPU"
  }
]
```

## Tips
- Always activate your virtual environment before running benchmarks.
- You can view and analyze all previous benchmark runs in `bench/output/bench_result.json`.
- For best results, ensure your hardware drivers and Python dependencies are up to date.

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