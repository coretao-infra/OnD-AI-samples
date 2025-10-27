
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

        def bool_to_str(val):
            if isinstance(val, bool):
                return "Yes" if val else "No"
            return "Unknown"

        table.add_row(
            str(index),
            model.id,
            model.alias,
            model.device,
            model.backend,
            f"{model.size:,}" if model.size else "Unknown",
            bool_to_str(model.cached),
            bool_to_str(model.loaded),
            style=row_style
        )

    console.print(table)

def display_benchmark_result_with_rich(benchmark_result):
    """
    Display benchmark results in a nicely formatted table using Rich.
    Accepts a BenchmarkResult object or dict.
    """
    console = Console()
    table = Table(title="Benchmark Results")

    table.add_column("Field", style="bold cyan")
    table.add_column("Value", style="bold yellow")

    # Support both object and dict
    result = benchmark_result.to_dict() if hasattr(benchmark_result, 'to_dict') else benchmark_result

    table.add_row("Input Tokens", str(result.get("input_tokens", "")))
    table.add_row("Output Tokens", str(result.get("output_tokens", "")))
    table.add_row("Total Tokens", str(result.get("total_tokens", "")))
    table.add_row("Latency (ms)", str(result.get("latency_ms", "")))
    tokens_per_second = (result.get("total_tokens", 0) / (result.get("latency_ms", 1) / 1000)) if result.get("latency_ms", 0) > 0 else 0
    table.add_row("Tokens per Second", f"{tokens_per_second:.2f}")
    table.add_row("Model", str(result.get("model", "")))
    table.add_row("Backend", str(result.get("backend", "")))
    table.add_row("GPU Name", str(result.get("gpu_name", "")))
    table.add_row("CPU Name", str(result.get("cpu_name", "")))
    table.add_row("NPU Name", str(result.get("npu_name", "")))
    table.add_row("System Memory (GB)", str(result.get("system_memory_gb", "")))
    table.add_row("Model Loaded", "Yes" if result.get("is_model_loaded", False) else "No")
    table.add_row("Timestamp", str(result.get("timestamp", "")))

    console.print(table)

def display_backends_with_rich(backends):
    """Display backends in a nicely formatted table using Rich."""
    console = Console()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="bold")
    table.add_column("Handler")
    table.add_column("Endpoint", overflow="fold")

    for idx, backend_cfg in enumerate(backends, start=1):
        name = backend_cfg.get("name", "?")
        handler = backend_cfg.get("handler", "?")
        endpoint = backend_cfg.get("endpoint_management", "")
        table.add_row(str(idx), name, handler, endpoint)

    console.print(table)