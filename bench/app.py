from utils.config import load_config
from rich.console import Console
from rich.table import Table


def display_menu():
    console = Console()
    table = Table(title="Benchmark Menu")
    table.add_column("Option", justify="center", style="cyan")
    table.add_column("Description", style="magenta")

    table.add_row("1", "Run Benchmark")
    table.add_row("2", "View Configuration")
    table.add_row("3", "Exit")

    console.print(table)


def run_benchmark(config):
    console = Console()
    console.print("[bold blue]Running Benchmark...[/bold blue]")
    for model in config.get("models", []):
        console.print(f"[yellow]Benchmarking model:[/yellow] {model}")
        # Simulate benchmarking logic
        console.print(f"[green]Model {model} benchmark completed successfully![/green]")


if __name__ == "__main__":
    try:
        config = load_config()
        while True:
            display_menu()
            choice = input("Enter your choice: ")
            if choice == "1":
                run_benchmark(config)
            elif choice == "2":
                console = Console()
                console.print("[bold green]Loaded Configuration:[/bold green]")
                console.print(config)
            elif choice == "3":
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")
    except Exception as e:
        print("Error:", e)