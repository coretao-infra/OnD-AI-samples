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

def get_user_choice():
    return input("Enter your choice: ")