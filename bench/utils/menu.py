from typing import List
from rich.console import Console
from rich.table import Table
from utils.llm_schema import Model

def display_models_with_rich(models: List[Model]):
    """Display models in a nicely formatted table using Rich."""
    console = Console()
    table = Table(title="Foundry Local Models")

    table.add_column("No.", style="bold white", justify="right")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Alias", style="magenta")
    table.add_column("Device", style="green")
    table.add_column("Backend", style="bold blue")
    table.add_column("Size (MB)", style="blue", justify="right")
    table.add_column("Cached", style="bold yellow")
    table.add_column("Loaded", style="bold yellow")

    # Sort models: prioritize backend, cached state, alias groups, then device type
    models.sort(key=lambda m: (m.backend, not m.cached, m.alias, m.device != "GPU"))

    # Assign alternating colors for alias groups
    alias_colors = ["white", "bright_white"]
    alias_to_color = {}
    current_color_index = 0

    for index, model in enumerate(models, start=1):
        if model.alias not in alias_to_color:
            alias_to_color[model.alias] = alias_colors[current_color_index]
            current_color_index = (current_color_index + 1) % len(alias_colors)

        base_color = alias_to_color[model.alias]

        # Adjust color based on cached state and device type
        if model.cached:
            row_style = f"bold {base_color}"
        else:
            row_style = f"dim {base_color}"

        if model.device == "GPU":
            row_style = f"bright_green" if model.cached else f"green"

        table.add_row(
            str(index),
            model.id,
            model.alias,
            model.device,
            model.backend,
            f"{model.size:,}" if model.size else "Unknown",
            "Yes" if model.cached else "No",
            "Yes" if model.loaded else "No",
            style=row_style
        )

    console.print(table)

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