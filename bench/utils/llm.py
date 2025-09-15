import wmi

def query_processors_accelerators_gpus():
    """
    Query Windows devices for Processor, Compute Accelerator, and GPU using WMI.
    Returns a dict with lists of device info for each class.
    """
    c = wmi.WMI()
    result = {"Processor": [], "ComputeAccelerator": [], "GPU": []}
    # Query processors
    for cpu in c.Win32_Processor():
        result["Processor"].append({"Name": cpu.Name, "Cores": cpu.NumberOfCores, "Threads": cpu.NumberOfLogicalProcessors})
    # Query compute accelerators (NPU)
    for dev in c.Win32_PnPEntity():
        # Match by PNPClass if available, or by name/description
        pnp_class = getattr(dev, 'PNPClass', None)
        if pnp_class == "ComputeAccelerator" or (
            "Accelerator" in (dev.Name or "") or "Accelerator" in (dev.Description or "") or "NPU" in (dev.Name or "") or "NPU" in (dev.Description or "")
        ):
            result["ComputeAccelerator"].append({
                "Name": dev.Name,
                "Description": dev.Description,
                "Manufacturer": getattr(dev, 'Manufacturer', None),
                "Status": getattr(dev, 'Status', None),
                "DeviceID": getattr(dev, 'DeviceID', None)
            })
    # Query GPUs (Video Controllers)
    for gpu in c.Win32_VideoController():
        gpu_info = {
            "Name": gpu.Name,
            "Description": gpu.Description,
            "AdapterRAM_MB": int(gpu.AdapterRAM) // (1024*1024) if gpu.AdapterRAM else None,
            "VideoProcessor": gpu.VideoProcessor,
            "DriverVersion": gpu.DriverVersion
        }
        result["GPU"].append(gpu_info)
    return result
from datetime import datetime
from utils.config import load_config, get_bench_result_path
from utils.bench_generic_openai import list_openai_models
from utils.bench_foundrylocal import get_all_models_with_cache_state, foundry_bench_inference
from utils.llm_schema import Model, BenchmarkResult
from utils.display import display_models_with_rich
from rich.console import Console
from rich.table import Table
from utils.shared import count_tokens
import json
import os

def discover_backends():
    """Discover all available backends dynamically."""
    config = load_config()
    return list(config.get("backends", {}).keys())

def consolidated_model_list():
    """Return a consolidated list of models from all available backends."""
    backends = discover_backends()
    models = []

    for backend in backends:
        if backend == "OpenAI":
            models.extend(list_openai_models())
        elif backend == "FoundryLocal":
            models.extend(get_all_models_with_cache_state())

    return models

def run_model_selection():
    """Display cached models and prompt the user to select one for benchmarking."""
    models = consolidated_model_list()
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

def list_backends():
    """Display the available backends."""
    console = Console()
    backends = discover_backends()
    if not backends:
        console.print("[bold red]No backends available.[/bold red]")
    else:
        console.print("[bold blue]Available Backends:[/bold blue]")
        for idx, backend in enumerate(backends, start=1):
            console.print(f"{idx}. {backend}")

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

    # Call the backend-specific function
    response_text = foundry_bench_inference(models_instance, system_prompt, user_prompt)

    # End timing the inference
    end_time = datetime.utcnow()
    latency_ms = int((end_time - start_time).total_seconds() * 1000)

    # Collect stats
    input_tokens = count_tokens(user_prompt)
    output_tokens = count_tokens(response_text)
    total_tokens = input_tokens + output_tokens

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
        system_memory_gb=system_memory_gb
    )

    # Append the result to the file
    append_benchmark_result(benchmark_result.to_dict())

    print("\n[INFO] Inference completed.")

    return benchmark_result

def query_system_ram():
    """
    Query the total system RAM using WMI.
    Returns the total RAM in GB.
    """
    c = wmi.WMI()
    for comp in c.Win32_ComputerSystem():
        total_ram_bytes = getattr(comp, 'TotalPhysicalMemory', None)
        if total_ram_bytes:
            return round(int(total_ram_bytes) / (1024 ** 3), 2)  # Convert bytes to GB
    return None