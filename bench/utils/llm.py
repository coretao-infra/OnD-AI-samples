def select_backend(config, backends):
    """Allow the user to select a backend from the list."""
    from rich.console import Console
    console = Console()
    if not backends:
        console.print("[red]No backends available to select.[/red]")
        return
    # The table is already shown by display_backends_with_rich; just prompt for selection
    try:
        choice = int(input("Enter the number of the backend: "))
        if 1 <= choice <= len(backends):
            selected_backend = backends[choice - 1]
            config["selected_backend"] = selected_backend
            name = selected_backend.get("name", "?")
            handler = selected_backend.get("handler", "?")
            endpoint = selected_backend.get("endpoint_management", selected_backend.get("endpoint", ""))
            console.print(f"[green]Selected Backend:[/green] [bold]{name}[/bold] | [magenta]{handler}[/magenta] | [green]{endpoint}[/green]")
        else:
            console.print("[red]Invalid choice. Please try again.[/red]")
    except ValueError:
        console.print("[red]Invalid input. Please enter a number.[/red]")
from datetime import datetime
from utils.config import load_config, get_bench_result_path
from utils.bench_generic_openai import list_openai_models
from utils.bench_foundrylocal import get_all_models_with_cache_state, foundry_bench_inference
from utils.bench_ollama import get_all_ollama_models_with_cache_state, ollama_bench_inference
from utils.llm_schema import Model, BenchmarkResult
from utils.display import display_models_with_rich
from rich.console import Console
from rich.table import Table
from utils.shared import count_tokens
import json
import os
import platform
import requests

def discover_backends():
    """Discover all available backends dynamically, filtering by platform and runtime availability."""    
    config = load_config()
    backends = config.get("backends", {})
    filtered = []
    sys = platform.system()
    for backend, backend_cfg in backends.items():
        if not backend_cfg.get("active", False):
            print(f"[INFO] Skipping backend '{backend}' (handler={backend_cfg.get('handler')}) because it is not active.")
            continue
        handler = backend_cfg.get("handler")
        if handler == "FoundryLocal" and sys != "Windows":
            print(f"[INFO] Skipping backend '{backend}' (handler=FoundryLocal) because platform is not Windows.")
            continue
        if handler == "Ollama":
            endpoint = backend_cfg.get("endpoint_management")
            if not endpoint:
                print(f"[INFO] Skipping backend '{backend}' (handler=Ollama) because endpoint_management is missing.")
                continue  # Require endpoint_management to be present
            try:
                resp = requests.get(endpoint, timeout=1)
                if resp.status_code != 200:
                    print(f"[INFO] Skipping backend '{backend}' (handler=Ollama) because endpoint_management returned status {resp.status_code}.")
                    continue
            except Exception as e:
                print(f"[INFO] Skipping backend '{backend}' (handler=Ollama) due to connection error: {e}")
                continue
        if handler == "OpenAI":
            endpoint = backend_cfg.get("endpoint_management")
            if not endpoint:
                print(f"[INFO] Skipping backend '{backend}' (handler=OpenAI) because endpoint_management is missing.")
                continue
            try:
                resp = requests.get(endpoint, timeout=1)
                if resp.status_code != 200:
                    print(f"[INFO] Skipping backend '{backend}' (handler=OpenAI) because endpoint_management returned status {resp.status_code}.")
                    continue
            except Exception as e:
                print(f"[INFO] Skipping backend '{backend}' (handler=OpenAI) due to connection error: {e}")
                continue
        backend_cfg_with_name = dict(backend_cfg)
        backend_cfg_with_name["name"] = backend
        filtered.append(backend_cfg_with_name)
    return filtered

def consolidated_model_list(backends):
    """Return a consolidated list of models from all available backends (passed in)."""
    models = []
    for backend_cfg in backends:
        handler = backend_cfg.get("handler")
        name = backend_cfg.get("name")
        if handler == "OpenAI":
            models.extend(list_openai_models(backend_cfg))
        elif handler == "FoundryLocal":
            models.extend(get_all_models_with_cache_state())
        elif handler == "Ollama":
            models.extend(get_all_ollama_models_with_cache_state())
    return models

def run_model_selection():
    """Display cached models and prompt the user to select one for benchmarking."""
    backends = discover_backends()
    models = consolidated_model_list(backends)
    cached_models = [model for model in models if model.cached]

    if not cached_models:
        print("No cached models available.")
        return

    # Display only cached models
    display_models_with_rich(cached_models)

    # Prompt user for selection
    try:
        choice = int(input("Enter the number of the model to benchmark: "))
        if 1 <= choice <= len(cached_models):
            selected_model = cached_models[choice - 1]
            print(f"Selected model: {selected_model.alias} (ID: {selected_model.id})")
            # Add benchmarking logic here
        else:
            print("Invalid selection. Please try again.")
    except ValueError:
        print("Invalid input. Please enter a number.")

def append_benchmark_result(result):
    """Append a benchmark result to the results file."""
    result_path = get_bench_result_path()

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(result_path), exist_ok=True)

    # Load existing results or initialize an empty list
    if os.path.exists(result_path):
        with open(result_path, "r") as file:
            results = json.load(file)
    else:
        results = []

    # Append the new result
    results.append(result)

    # Write back to the file
    with open(result_path, "w") as file:
        json.dump(results, file, indent=4)

def bench_inference(models_instance, prompt_set_name):
    """
    Perform inference using a specified prompt set and backend.

    Args:
        models_instance: Instance of the Models object.
        prompt_set_name: Name of the desired prompt set (e.g., "light", "medium").

    Returns:
        BenchmarkResult object containing stats and metadata.
    """
    # Load configuration
    config = load_config()

    # Retrieve the prompt set
    prompt_sets = config.get("prompt_sets", {})
    prompt_set = prompt_sets.get(prompt_set_name)
    if not prompt_set:
        raise ValueError(f"Prompt set '{prompt_set_name}' not found in configuration.")

    # Calculate remaining tokens
    max_tokens = prompt_set["max_tokens"]
    user_prompt = prompt_set["user_prompt"]
    system_prompt = prompt_set["system_prompt"]
    user_prompt_tokens = count_tokens(user_prompt)
    system_prompt_tokens = count_tokens(system_prompt)
    remaining_tokens = max_tokens - (user_prompt_tokens + system_prompt_tokens)

    # Calculate average words per token based on the prompts
    total_words = len(user_prompt.split()) + len(system_prompt.split())
    total_tokens = user_prompt_tokens + system_prompt_tokens
    avg_words_per_token = total_words / total_tokens if total_tokens > 0 else 1

    # Calculate remaining words
    remaining_words = int(remaining_tokens * avg_words_per_token)

    # Populate the system prompt with remaining words
    system_prompt = system_prompt.replace("{{remaining_words}}", str(remaining_words))

    # Query hardware details
    hardware_info = query_processors_accelerators_gpus()
    gpu_name = hardware_info["GPU"][0]["Name"] if hardware_info["GPU"] else "Unknown GPU"
    cpu_name = hardware_info["Processor"][0]["Name"] if hardware_info["Processor"] else "Unknown CPU"
    npu_name = hardware_info["ComputeAccelerator"][0]["Name"] if hardware_info["ComputeAccelerator"] else "Unknown NPU"
    system_memory_gb = query_system_ram() or "Unknown RAM"

    # Print summary to the console
    print("[INFO] Starting inference with the following details:")
    print(f"       Prompt Set: {prompt_set_name}")
    print(f"       Max Tokens: {max_tokens}")
    print(f"       Remaining Tokens: {remaining_tokens}")
    print(f"       System Prompt: {system_prompt}")
    print(f"       User Prompt: {user_prompt}")

    # Start timing the inference
    start_time = datetime.utcnow()

    # Dispatch to correct inference function
    backend = getattr(models_instance, 'backend', None)
    if backend == "FoundryLocal":
        response_text = foundry_bench_inference(models_instance, system_prompt, user_prompt)
    elif backend == "Ollama":
        response_text = ollama_bench_inference(models_instance, system_prompt, user_prompt, max_tokens=max_tokens)
    else:
        response_text = f"Backend {backend} not supported for inference."

    # End timing the inference
    end_time = datetime.utcnow()
    latency_ms = int((end_time - start_time).total_seconds() * 1000)

    # Collect stats
    input_tokens = count_tokens(user_prompt)
    output_tokens = count_tokens(response_text)
    total_tokens = input_tokens + output_tokens

    # Determine silicon type
    device_type = getattr(models_instance, 'device', None)
    if device_type == "NPU":
        silicon = "NPU"
    elif device_type == "GPU":
        silicon = "GPU"
    elif device_type == "CPU":
        silicon = "CPU"
    elif device_type == "Remote":
        silicon = "Remote"
    elif device_type == "Cloud":
        silicon = "Cloud"
    else:
        silicon = "Unknown"

    # Create the BenchmarkResult object
    benchmark_result = BenchmarkResult(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
        model=models_instance.id,
        backend=models_instance.backend,
        timestamp=start_time.isoformat() + "Z",
        is_model_loaded=models_instance.loaded,
        gpu_name=gpu_name,
        cpu_name=cpu_name,
        npu_name=npu_name,
        system_memory_gb=system_memory_gb,
        silicon=silicon
    )

    # Append the result to the file
    append_benchmark_result(benchmark_result.to_dict())

    print("\n[INFO] Inference completed.")

    return benchmark_result

if platform.system() == "Windows":
    from utils.hwinfo_win import query_processors_accelerators_gpus, query_system_ram
elif platform.system() == "Darwin":
    from utils.hwinfo_mac import query_processors_accelerators_gpus, query_system_ram
else:
    def query_processors_accelerators_gpus():
        return {"Processor": [], "ComputeAccelerator": [], "GPU": []}
    def query_system_ram():
        return None