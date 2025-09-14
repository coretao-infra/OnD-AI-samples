import tiktoken
from utils.config import load_config
from utils.bench_generic_openai import list_openai_models
from utils.bench_foundrylocal import get_all_models_with_cache_state
from utils.llm_schema import Model
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