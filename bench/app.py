from utils.config import load_config
from utils.llm import discover_backends, consolidated_model_list, list_backends
from utils.menu import display_main_menu, get_main_menu_choice, handle_main_menu_choice
from utils.display import display_models_with_rich
from rich.console import Console
from rich.table import Table
from utils.llm_schema import Model


def run_benchmark(config, model):
    """Run a benchmark for the selected model."""
    console = Console()
    console.print(f"[bold blue]Running Benchmark for {model.alias} (ID: {model.id})...[/bold blue]")

    # Simulate benchmarking logic
    import time
    console.print("[yellow]Loading model...[/yellow]")
    time.sleep(2)  # Simulate loading time

    console.print("[yellow]Running inference...[/yellow]")
    time.sleep(3)  # Simulate inference time

    console.print(f"[green]Benchmark completed successfully for {model.alias}![/green]")


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
            run_benchmark  # Pass the implemented `run_benchmark` function
        ):
            break


if __name__ == "__main__":
    main()