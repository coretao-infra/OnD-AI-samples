from utils.config import load_config
from utils.llm import consolidated_model_list, bench_inference
from utils.menu import display_main_menu, get_main_menu_choice, handle_main_menu_choice
from utils.display import display_models_with_rich
from utils.llm import discover_backends
from utils.display import display_backends_with_rich
from rich.console import Console
from rich.table import Table
from utils.llm_schema import Model


def run_benchmark(config, model):
    """Run a benchmark for the selected model."""
    console = Console()
    console.print(f"[bold blue]Running Benchmark for {model.alias} (ID: {model.id})...[/bold blue]")

    # Call bench_inference to perform the actual benchmark
    from utils.display import display_benchmark_result_with_rich
    try:
        result = bench_inference(model, "light")  # Assuming "light" prompt set for now
        display_benchmark_result_with_rich(result)
    except Exception as e:
        console.print(f"[red]Benchmark failed: {e}[/red]")


def list_all_models(models):
    console = Console()
    console.print("[bold blue]Available Models:[/bold blue]")
    display_models_with_rich(models)






def main():
    config = load_config()
    _BACKENDS = discover_backends()
    _MODELS = consolidated_model_list(_BACKENDS)
    while True:
        display_main_menu()
        choice = get_main_menu_choice()
        if not handle_main_menu_choice(
            choice,
            config,
            _MODELS,
            _BACKENDS,
            lambda: list_all_models(_MODELS),
            run_benchmark
        ):
            break

if __name__ == "__main__":
    main()