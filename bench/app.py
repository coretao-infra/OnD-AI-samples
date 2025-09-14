from utils.config import load_config
from utils.llm import discover_backends, consolidated_model_list, list_backends
from utils.menu import display_main_menu, get_main_menu_choice, handle_main_menu_choice
from utils.display import display_models_with_rich
from rich.console import Console
from rich.table import Table
from utils.llm_schema import Model


def run_benchmark(config, model=None):
    console = Console()
    console.print("[bold blue]Running Benchmark...[/bold blue]")

    if model:
        console.print(f"[yellow]Benchmarking model:[/yellow] {model.alias} (ID: {model.id})")
        # Simulate benchmarking logic for the selected model
        console.print(f"[green]Model {model.alias} benchmark completed successfully![/green]")
    else:
        for model in config.get("models", []):
            console.print(f"[yellow]Benchmarking model:[/yellow] {model}")
            # Simulate benchmarking logic
            console.print(f"[green]Model {model} benchmark completed successfully![/green]")


def list_all_models():
    console = Console()
    console.print("[bold blue]Available Models:[/bold blue]")
    models = consolidated_model_list()  # Fetch raw model data
    display_models_with_rich(models)  # Pass models directly without rewrapping


def select_backend(config):
    """Allow the user to select a backend from the list."""
    console = Console()
    backends = discover_backends()

    if not backends:
        console.print("[red]No backends available to select.[/red]")
        return

    console.print("[bold blue]Select a Backend:[/bold blue]")
    for i, backend in enumerate(backends, start=1):
        console.print(f"[cyan]{i}.[/cyan] {backend}")

    try:
        choice = int(input("Enter the number of the backend: "))
        if 1 <= choice <= len(backends):
            selected_backend = backends[choice - 1]
            config["selected_backend"] = selected_backend
            console.print(f"[green]Selected Backend:[/green] {selected_backend}")
        else:
            console.print("[red]Invalid choice. Please try again.[/red]")
    except ValueError:
        console.print("[red]Invalid input. Please enter a number.[/red]")


def main():
    config = load_config()
    while True:
        display_main_menu()
        choice = get_main_menu_choice()
        if not handle_main_menu_choice(
            choice,
            config,
            consolidated_model_list,
            list_backends,  # Use the moved `list_backends` function
            select_backend,
            list_all_models,
            lambda cfg, model: print(f"Run benchmark for {model.alias} not implemented")
        ):
            break


if __name__ == "__main__":
    main()