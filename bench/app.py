from utils.config import load_config
from utils.llm import discover_backends, consolidated_model_list
from utils.menu import display_main_menu, get_main_menu_choice, handle_main_menu_choice
from rich.console import Console
from rich.table import Table


def run_benchmark(config):
    console = Console()
    console.print("[bold blue]Running Benchmark...[/bold blue]")
    for model in config.get("models", []):
        console.print(f"[yellow]Benchmarking model:[/yellow] {model}")
        # Simulate benchmarking logic
        console.print(f"[green]Model {model} benchmark completed successfully![/green]")


def list_backends():
    console = Console()
    console.print("[bold blue]Available Backends:[/bold blue]")
    backends = discover_backends()
    for i, backend in enumerate(backends, start=1):
        console.print(f"[cyan]{i}.[/cyan] {backend}")


def list_all_models():
    console = Console()
    console.print("[bold blue]Available Models:[/bold blue]")
    models = consolidated_model_list()
    for i, model in enumerate(models, start=1):
        console.print(f"[cyan]{i}.[/cyan] {model}")


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


if __name__ == "__main__":
    try:
        config = load_config()
        while True:
            display_main_menu()
            choice = get_main_menu_choice()
            if not handle_main_menu_choice(choice, config):
                break
    except Exception as e:
        print("Error:", e)