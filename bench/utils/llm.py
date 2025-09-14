import tiktoken
from datetime import datetime
from utils.config import load_config
from utils.bench_generic_openai import list_openai_models
from utils.bench_foundrylocal import get_all_models_with_cache_state
from utils.llm_schema import Model, BenchmarkResult
from utils.display import display_models_with_rich
from rich.console import Console

def count_tokens(text, model):
    """Count tokens in a given text using tiktoken."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

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
    remaining_tokens = max_tokens - count_tokens(user_prompt, models_instance.active_model)

    # Populate the system prompt with remaining tokens
    system_prompt = prompt_set["system_prompt"].replace("{{remaining_tokens}}", str(remaining_tokens))

    # Print summary to the console
    print("[INFO] Starting inference with the following details:")
    print(f"       Prompt Set: {prompt_set_name}")
    print(f"       Max Tokens: {max_tokens}")
    print(f"       Remaining Tokens: {remaining_tokens}")
    print(f"       System Prompt: {system_prompt}")
    print(f"       User Prompt: {user_prompt}")

    # Delegate message mapping to the backend-specific method
    messages = models_instance.map_messages(system_prompt, user_prompt)

    # Start timing the inference
    start_time = datetime.utcnow()

    # Submit the request to the backend and stream the text
    print("[INFO] Streaming response:")
    response_text = ""
    for chunk in models_instance.stream_request(messages):
        print(chunk, end="", flush=True)  # Stream to console
        response_text += chunk

    # End timing the inference
    end_time = datetime.utcnow()
    latency_ms = int((end_time - start_time).total_seconds() * 1000)

    # Collect stats
    input_tokens = count_tokens(user_prompt, models_instance.active_model)
    output_tokens = count_tokens(response_text, models_instance.active_model)
    total_tokens = input_tokens + output_tokens

    # Create the BenchmarkResult object
    benchmark_result = BenchmarkResult(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
        model=models_instance.active_model,
        backend=models_instance.backend_name,
        timestamp=start_time.isoformat() + "Z"
    )

    print("\n[INFO] Inference completed.")

    return benchmark_result