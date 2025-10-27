from rich.console import Console
from rich.table import Table

from utils.display import display_models_with_rich
from utils.display import display_backends_with_rich
from utils.llm import select_backend
import platform


def display_main_menu():
    """Display the main menu for the benchmark application."""
    console = Console()
    table = Table(title="Benchmark Menu")
    table.add_column("Option", justify="center", style="cyan")
    table.add_column("Description", style="magenta")

    table.add_row("1", "Select Backend (Show & Choose)")
    table.add_row("3", "List Models")
    table.add_row("4", "Run Benchmark")
    table.add_row("5", "List All Available Models")
    table.add_row("6", "Display CPU/NPU/GPU Info")
    table.add_row("9", "Exit")

    console.print(table)

def get_main_menu_choice():
    """Prompt the user for a choice from the main menu."""
    return input("Enter your choice: ")

def handle_main_menu_choice(choice, config, consolidated_model_list, backends, list_all_models, run_benchmark):
    """Handle the user's choice from the main menu."""
    if choice == "1":
        display_backends_with_rich(backends)
        select_backend(config, backends)
    elif choice == "3":
        list_all_models()
    elif choice == "4":
        # Run benchmark with cached model selection
        cached_models = [model for model in models if model.cached]

        if not cached_models:
            print("No cached models available.")
            return True

        # Use display_models_with_rich to show cached models
        display_models_with_rich(cached_models)

        try:
            selection = int(input("\nEnter the number of the model to benchmark: "))
            if 1 <= selection <= len(cached_models):
                selected_model = cached_models[selection - 1]
                print(f"\nSelected model: {selected_model.alias} (ID: {selected_model.id})")
                run_benchmark(config, selected_model)
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    elif choice == "5":
        list_all_models()
    elif choice == "6":
        if platform.system() == "Windows":
            from utils.hwinfo_win import query_processors_accelerators_gpus, query_system_ram
        elif platform.system() == "Darwin":
            from utils.hwinfo_mac import query_processors_accelerators_gpus, query_system_ram
        else:
            def query_processors_accelerators_gpus():
                return {"Processor": [], "ComputeAccelerator": [], "GPU": []}
            def query_system_ram():
                return None

        info = query_processors_accelerators_gpus()
        system_ram = query_system_ram()

        from rich.console import Console
        console = Console()

        console.print("[bold blue]CPU Info:[/bold blue]")
        for cpu in info.get("Processor", []):
            console.print(f"[green]Name:[/green] {cpu.get('Name')} | [yellow]Cores:[/yellow] {cpu.get('Cores')} | [yellow]Threads:[/yellow] {cpu.get('Threads')}")

        console.print("[bold blue]NPU/Compute Accelerator Info:[/bold blue]")
        for npu in info.get("ComputeAccelerator", []):
            console.print(f"[green]Name:[/green] {npu.get('Name')} | [yellow]Description:[/yellow] {npu.get('Description')}")

        console.print("[bold blue]GPU Info:[/bold blue]")
        for gpu in info.get("GPU", []):
            console.print(f"[green]Name:[/green] {gpu.get('Name')} | [yellow]VRAM:[/yellow] {gpu.get('DedicatedMemory_MB')} MB | [yellow]VideoProcessor:[/yellow] {gpu.get('VideoProcessor')} | [yellow]DriverVersion:[/yellow] {gpu.get('DriverVersion')}")

        console.print("[bold blue]System RAM:[/bold blue]")
        if system_ram:
            console.print(f"[green]Total RAM:[/green] {system_ram} GB")
        else:
            console.print("[red]System RAM detection failed.[/red]")
    elif choice == "9":
        print("Exiting...")
        return False
    else:
        print("Invalid choice. Please try again.")
    return True