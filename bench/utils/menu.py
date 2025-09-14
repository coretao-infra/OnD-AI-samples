from rich.console import Console
from rich.table import Table

def display_main_menu():
    """Display the main menu for the benchmark application."""
    console = Console()
    table = Table(title="Benchmark Menu")
    table.add_column("Option", justify="center", style="cyan")
    table.add_column("Description", style="magenta")

    table.add_row("1", "List Backends")
    table.add_row("2", "Select Backend")
    table.add_row("3", "List Models")
    table.add_row("4", "Run Benchmark")
    table.add_row("5", "List All Available Models")
    table.add_row("9", "Exit")

    console.print(table)

def get_main_menu_choice():
    """Prompt the user for a choice from the main menu."""
    return input("Enter your choice: ")

def handle_main_menu_choice(choice, config):
    """Handle the user's choice from the main menu."""
    from utils.llm import discover_backends, consolidated_model_list
    from app import list_backends, select_backend, list_all_models, run_benchmark

    if choice == "1":
        list_backends()
    elif choice == "2":
        select_backend(config)
    elif choice == "3":
        list_all_models()
    elif choice == "4":
        run_benchmark(config)
    elif choice == "5":
        list_all_models()
    elif choice == "9":
        print("Exiting...")
        return False
    else:
        print("Invalid choice. Please try again.")
    return True