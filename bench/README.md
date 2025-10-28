# LLM Benchmarking Scripts
![Repo Banner](../assets/CoryLabScene-Small.png)

## Overview
This project is designed to benchmark different LLM models using a menu-driven UI. It allows users to compare models based on various metrics such as token counts, response time, and more. The project is modular and extensible, making it easy to add new features and models.

The project supports multiple AI backends including **Azure Foundry Local**, **Ollama**, **OpenAI API**, and **LMStudio**, allowing comprehensive benchmarking across local and cloud-based models.

## Requisites

### Software Requirements
- Python 3.10 or newer
   https://www.python.org/downloads/windows/
- Foundry Local AI:
   https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/get-started#option-1-quick-cli-setup
- Git for cloning the repository
   https://git-scm.com/downloads/win
- **Optional**: Ollama for local model inference
   https://ollama.ai/
- **Optional**: LMStudio for local OpenAI-compatible API
   https://lmstudio.ai/

### Hardware Requirements
- At least 32+ GB RAM
- GPU with DirectML support (optional but recommended)
- NPU/dedicated AI accelerator (optional)

### Python Packages
The following key packages are referenced within the codebase.
- `rich`: For enhanced console output
- `wmi`: For querying system hardware information
- `tiktoken`: For token counting
- `requests`: For API interactions
- `openai`: For OpenAI API and LMStudio compatibility

## How to Run Benchmarks
1. **Clone the repository:**
   ```powershell
   git clone <repository-url>
   cd <repo-clone-path>/bench
   ```

2. **Create a Python virtual environment:**
   ```powershell
   python -m venv .venv
   ```

3. **Activate the Python virtual environment:**
   ```powershell
   .\.venv\Scripts\Activate.ps1  # For Windows
   ```

4. **Install dependencies:**
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

### Backend Selection
The tool supports multiple backends:
- **FoundryLocal**: Azure Foundry Local models running locally
- **Ollama**: Local Ollama server models
- **OpenAI**: OpenAI-compatible APIs (including LMStudio)

Use option `2` to select your preferred backend before running benchmarks.

### To run a benchmark:
1. Select option `2` to choose your backend (FoundryLocal, Ollama, or OpenAI).
2. Select option `4` (Run Benchmark).
3. Choose a model from the displayed list by entering its number.
4. The benchmark will run and stream the model's response and stats to the console.

### To view hardware info:
Select option `6` to display details about your CPU, NPU, GPU, and system RAM.

## Managing Foundry Models

The benchmark tool uses Foundry Local models. You can manage these models directly using the built-in utility:

```powershell
python -m utils.bench_foundrylocal
```

This launches the Foundry Local Model Manager:

```
Foundry Local Model Manager
1. List all models with cache state
2. Add a model to cache
3. Remove a model from cache
4. Display raw catalog models
5. Display raw cached models
6. Display raw loaded models
7. Exit
8. Test inference with model selection
Enter your choice: 1
```

When you select option `1`, you'll see all available models with their details:

```
                                                 Foundry Local Models                                                  
┏━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┓
┃ No. ┃ ID                                ┃ Alias                ┃ Device ┃ Backend      ┃ Size (MB) ┃ Cached ┃ Loaded ┃
┡━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━┩
│   1 │ Phi-3.5-mini-instruct-generic-gpu │ phi-3.5-mini         │ GPU    │ FoundryLocal │     2,211 │ Yes    │ No     │
│   2 │ Phi-3.5-mini-instruct-generic-cpu │ phi-3.5-mini         │ CPU    │ FoundryLocal │     2,590 │ Yes    │ No     │
│   3 │ Phi-4-generic-gpu                 │ phi-4                │ GPU    │ FoundryLocal │     8,570 │ Yes    │ No     │
│   4 │ Phi-4-generic-cpu                 │ phi-4                │ CPU    │ FoundryLocal │    10,403 │ Yes    │ No     │
│   5 │ Phi-4-mini-reasoning-generic-gpu  │ phi-4-mini-reasoning │ GPU    │ FoundryLocal │     3,225 │ Yes    │ No     │
│  ... │ ...                              │ ...                  │ ...    │ ...          │       ... │ ...    │ ...    │
└─────┴───────────────────────────────────┴──────────────────────┴────────┴──────────────┴───────────┴────────┴────────┘
```

### Understanding the Model List

- **ID**: The unique identifier for the model
- **Alias**: A shorter, user-friendly name
- **Device**: Whether the model runs on GPU or CPU
- **Size**: Size in MB (larger models require more RAM)
- **Cached**: Whether the model is already downloaded to your device
- **Loaded**: Whether the model is currently loaded in memory

### Working with Models

1. **Before benchmarking**, you should cache the models you want to test:
   - Choose option `2` from the menu
   - Enter the number of the model to cache
   - Wait for the download to complete (larger models take longer)

2. **To free up space**, you can remove models from cache:
   - Choose option `3` from the menu
   - Enter the number of the model to remove

3. **For quick testing**, use option `8` to test a model before full benchmarking

For more detailed information on Foundry Local, refer to the [official documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/get-started).

## Working with Other Backends

### Ollama Setup
If using Ollama:
1. Install Ollama from https://ollama.ai/
2. Start the Ollama service
3. Pull models using `ollama pull <model-name>`
4. Select "Ollama" backend in the benchmark menu

### LMStudio/OpenAI Setup
If using LMStudio or OpenAI API:
1. For LMStudio: Start the local server on http://localhost:1234
2. For OpenAI: Ensure you have API access and credentials
3. Select "OpenAI" backend in the benchmark menu
4. Models will be automatically discovered and listed

**Note**: LMStudio compatibility includes both `chat/completions` and `completions` endpoints with streaming support.

For more information on Foundry Local and managing models, see the [official documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/get-started).

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
- Latency (time it took to run test inference)
- Hardware details 
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
- [X] Write detailed documentation in this `README.md` for contributing and advanced usage.
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
- [x] Add support for Ollama framework integration
- [x] Add support for OpenAI-compatible APIs (including LMStudio)
- [x] Implement OpenAI streaming inference with proper content extraction
- [ ] Resolve LMStudio API compatibility issues (stateful behavior, inconsistent responses)

## FUTURE
- [ ] Implement queuing for benchmarking tasks.
- [ ] Add support for additional backend engines:
  - [ ] llama.cpp 
  - [ ] vLLM 
- [ ] Add Cloud-based AI endpoints for comparison benchmarking:
  - [ ] Azure OpenAI Service
  - [ ] Azure AI Foundry APIs
  - [ ] OpenAI API (cloud)
  - [ ] Anthropic Claude
  - [ ] Google Gemini
- [ ] Enhanced streaming diagnostics and performance monitoring
- [ ] Multi-backend benchmark comparison reports
- [ ] Model performance regression testing

## Notes
- Ensure the virtual environment is activated before running any scripts.
- Use the `logging` module for debugging and tracking execution flow.