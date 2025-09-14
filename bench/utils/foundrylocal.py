import logging
from .foundrylocal import FoundryLocalManagerWrapper
from .config import load_config
import argparse
from rich.console import Console
from rich.table import Table

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_service_running():
    """Check if the Foundry Local service is running."""
    manager = FoundryLocalManagerWrapper()
    return manager.manager.is_service_running()

def start_service():
    """Start the Foundry Local service."""
    manager = FoundryLocalManagerWrapper()
    manager.manager.start_service()
    logging.info("Foundry Local service started.")

def list_catalog_models():
    """List all available models in the catalog."""
    manager = FoundryLocalManagerWrapper()
    catalog = manager.manager.list_catalog_models()
    return catalog

def list_cached_models():
    """List all models in the local cache."""
    manager = FoundryLocalManagerWrapper()
    cached_models = manager.manager.list_cached_models()
    return cached_models

def get_model_info(alias_or_model_id):
    """Get detailed information about a specific model."""
    manager = FoundryLocalManagerWrapper()
    return manager.manager.get_model_info(alias_or_model_id)

def get_all_models_with_cache_state():
    """Get all available models with their alias, device, size, cached state, and loaded state."""
    manager = FoundryLocalManagerWrapper()

    # Fetch all models from the catalog
    catalog = manager.manager.list_catalog_models()

    # Fetch cached models
    cached_models = {model.id for model in manager.manager.list_cached_models()}

    # Fetch loaded models
    loaded_models = {model.id for model in manager.manager.list_loaded_models()}

    # Build the list of models with their states
    models_with_cache_state = []
    for model in catalog:
        models_with_cache_state.append({
            "id": model.id,
            "alias": model.alias,
            "device": "GPU" if "gpu" in model.id.lower() else "CPU" if "cpu" in model.id.lower() else "Unknown",
            "size": model.file_size_mb,
            "cached": model.id in cached_models,
            "loaded": model.id in loaded_models  # Check if the model is loaded
        })

    return models_with_cache_state

def manage_model_cache(action, alias_or_model_id):
    """Add or remove models to/from cache.

    Args:
        action (str): Either 'add' or 'remove'.
        alias_or_model_id (str): The alias or model ID to manage.

    Returns:
        str: Success message or error message.
    """
    manager = FoundryLocalManagerWrapper()

    if action == 'add':
        try:
            manager.manager.download_model(alias_or_model_id)
            return f"Model {alias_or_model_id} added to cache."
        except Exception as e:
            return f"Failed to add model {alias_or_model_id} to cache: {e}"

    elif action == 'remove':
        try:
            manager.manager.unload_model(alias_or_model_id, force=True)
            return f"Model {alias_or_model_id} removed from cache."
        except Exception as e:
            return f"Failed to remove model {alias_or_model_id} from cache: {e}"

    else:
        return "Invalid action. Use 'add' or 'remove'."

def display_raw_catalog():
    """Display all raw information from the SDK's catalog models."""
    manager = FoundryLocalManagerWrapper()
    catalog = manager.manager.list_catalog_models()
    print("\nRaw Catalog Models:")
    for model in catalog:
        print(model)

def display_raw_cache():
    """Display all raw information from the SDK's cached models."""
    manager = FoundryLocalManagerWrapper()
    cached_models = manager.manager.list_cached_models()
    print("\nRaw Cached Models:")
    for model in cached_models:
        print(model)

def display_raw_loaded_models():
    """Display raw output of all loaded models."""
    manager = FoundryLocalManagerWrapper()
    loaded_models = manager.manager.list_loaded_models()
    print("\nRaw Loaded Models:")
    for model in loaded_models:
        print(model)
    print()

def display_menu():
    """Display the main menu for user interaction."""
    print("\nFoundry Local Model Manager")
    print("1. List all models with cache state")
    print("2. Add a model to cache")
    print("3. Remove a model from cache")
    print("4. Display raw catalog models")
    print("5. Display raw cached models")
    print("6. Display raw loaded models")
    print("7. Exit")

def display_models_with_rich(models):
    """Display models in a nicely formatted table using Rich."""
    console = Console()
    table = Table(title="Foundry Local Models")

    table.add_column("No.", style="bold white", justify="right")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Alias", style="magenta")
    table.add_column("Device", style="green")
    table.add_column("Size (MB)", style="blue", justify="right")
    table.add_column("Cached", style="bold yellow")
    table.add_column("Loaded", style="bold yellow")

    # Sort models: prioritize cached state, then alias groups, then device type
    models.sort(key=lambda m: (not m["cached"], m["alias"], m["device"] != "GPU"))

    # Assign alternating colors for alias groups
    alias_colors = ["white", "bright_white"]
    alias_to_color = {}
    current_color_index = 0

    for index, model in enumerate(models, start=1):
        if model["alias"] not in alias_to_color:
            alias_to_color[model["alias"]] = alias_colors[current_color_index]
            current_color_index = (current_color_index + 1) % len(alias_colors)

        base_color = alias_to_color[model["alias"]]

        # Adjust color based on cached state and device type
        if model["cached"]:
            row_style = f"bold {base_color}"
        else:
            row_style = f"dim {base_color}"

        if model["device"] == "GPU":
            row_style = f"bright_green" if model["cached"] else f"green"

        table.add_row(
            str(index),
            model["id"],
            model["alias"],
            model["device"],
            f"{model['size']:,}" if model['size'] else "Unknown",
            "Yes" if model["cached"] else "No",
            "Yes" if model["loaded"] else "No",
            style=row_style
        )

    console.print(table)

def main_ui_loop():
    """Main UI loop for interacting with Foundry Local."""
    while True:
        display_menu()
        choice = input("Enter your choice: ")

        if choice == "1":
            models = get_all_models_with_cache_state()
            display_models_with_rich(models)

        elif choice == "2":
            models = get_all_models_with_cache_state()
            display_models_with_rich(models)
            try:
                model_number = int(input("Enter the number of the model to add to cache: "))
                if 1 <= model_number <= len(models):
                    alias_or_model_id = models[model_number - 1]["id"]
                    result = manage_model_cache("add", alias_or_model_id)
                    print(result)
                else:
                    print("Invalid model number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        elif choice == "3":
            models = get_all_models_with_cache_state()
            display_models_with_rich(models)
            try:
                model_number = int(input("Enter the number of the model to remove from cache: "))
                if 1 <= model_number <= len(models):
                    alias_or_model_id = models[model_number - 1]["id"]
                    result = manage_model_cache("remove", alias_or_model_id)
                    print(result)
                else:
                    print("Invalid model number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        elif choice == "4":
            display_raw_catalog()

        elif choice == "5":
            display_raw_cache()

        elif choice == "6":
            display_raw_loaded_models()

        elif choice == "7":
            print("Exiting Foundry Local Model Manager.")
            break

        else:
            print("Invalid choice. Please try again.")

def main():
    setup_logging()

    parser = argparse.ArgumentParser(description="Foundry Local Discovery and Config Script")
    parser.add_argument("--list-catalog", action="store_true", help="List all models in the catalog")
    parser.add_argument("--list-cache", action="store_true", help="List all models in the local cache")
    parser.add_argument("--start-service", action="store_true", help="Start the Foundry Local service")
    parser.add_argument("--model-info", type=str, help="Get detailed information about a specific model")

    args = parser.parse_args()

    config = load_config()
    logging.info("Loaded configuration: %s", config)

    if args.start_service:
        if not is_service_running():
            start_service()
        else:
            logging.info("Foundry Local service is already running.")

    if args.list_catalog:
        logging.info("Available models in the catalog:")
        for model in list_catalog_models():
            logging.info(model)

    if args.list_cache:
        logging.info("Models in cache:")
        for model in list_cached_models():
            logging.info(model)

    if args.model_info:
        model_info = get_model_info(args.model_info)
        if model_info:
            logging.info("Model info: %s", model_info)
        else:
            logging.warning("Model not found: %s", args.model_info)

if __name__ == "__main__":
    main_ui_loop()