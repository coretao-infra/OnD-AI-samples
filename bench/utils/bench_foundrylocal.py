import logging
from foundry_local import FoundryLocalManager
from .config import load_config
import argparse
from rich.console import Console
from rich.table import Table
from utils.llm_schema import Model
from utils.menu import display_models_with_rich, display_main_menu, get_main_menu_choice
from utils.display import display_models_with_rich
from typing import List
import openai

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_service_running():
    """Check if the Foundry Local service is running."""
    manager = FoundryLocalManager()
    return manager.is_service_running()

def start_service():
    """Start the Foundry Local service."""
    manager = FoundryLocalManager()
    manager.start_service()
    logging.info("Foundry Local service started.")

def list_catalog_models():
    """List all available models in the catalog."""
    manager = FoundryLocalManager()
    catalog = manager.list_catalog_models()
    return catalog

def list_cached_models():
    """List all models in the local cache."""
    manager = FoundryLocalManager()
    cached_models = manager.list_cached_models()
    return cached_models

def get_model_info(alias_or_model_id):
    """Get detailed information about a specific model."""
    manager = FoundryLocalManager()
    return manager.get_model_info(alias_or_model_id)

def create_model_object(model, cached_models, loaded_models, backend):
    """Helper method to create a Model object with cache and load state."""
    return Model(
        id=model.id,
        alias=model.alias,
        device="GPU" if "gpu" in model.id.lower() else "CPU" if "cpu" in model.id.lower() else "Unknown",
        size=model.file_size_mb,
        cached=model.id in cached_models,
        loaded=model.id in loaded_models,
        backend=backend
    )

def get_all_models_with_cache_state():
    """Get all available models with their alias, device, size, cached state, and loaded state."""
    manager = FoundryLocalManager()

    # Fetch all models from the catalog
    catalog = manager.list_catalog_models()

    # Fetch cached models
    cached_models = {model.id for model in manager.list_cached_models()}

    # Fetch loaded models
    loaded_models = {model.id for model in manager.list_loaded_models()}

    # Build and return a list of Model objects
    return [
        Model(
            id=model.id,
            alias=model.alias,
            device="GPU" if "gpu" in model.id.lower() else "CPU" if "cpu" in model.id.lower() else "Unknown",
            size=model.file_size_mb,
            cached=model.id in cached_models,
            loaded=model.id in loaded_models,
            backend="FoundryLocal"
        )
        for model in catalog
    ]

def manage_model_cache(action, alias_or_model_id):
    """Add or remove models to/from cache.

    Args:
        action (str): Either 'add' or 'remove'.
        alias_or_model_id (str): The alias or model ID to manage.

    Returns:
        str: Success message or error message.
    """
    manager = FoundryLocalManager()

    if action == 'add':
        try:
            manager.download_model(alias_or_model_id)
            return f"Model {alias_or_model_id} added to cache."
        except Exception as e:
            return f"Failed to add model {alias_or_model_id} to cache: {e}"

    elif action == 'remove':
        try:
            manager.unload_model(alias_or_model_id, force=True)
            return f"Model {alias_or_model_id} removed from cache."
        except Exception as e:
            return f"Failed to remove model {alias_or_model_id} from cache: {e}"

    else:
        return "Invalid action. Use 'add' or 'remove'."

def display_raw_catalog():
    """Display all raw information from the SDK's catalog models."""
    manager = FoundryLocalManager()
    catalog = manager.list_catalog_models()
    print("\nRaw Catalog Models:")
    for model in catalog:
        print(model)

def display_raw_cache():
    """Display all raw information from the SDK's cached models."""
    manager = FoundryLocalManager()
    cached_models = manager.list_cached_models()
    print("\nRaw Cached Models:")
    for model in cached_models:
        print(model)

def display_raw_loaded_models():
    """Display raw output of all loaded models."""
    manager = FoundryLocalManager()
    loaded_models = manager.list_loaded_models()
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
    print("8. Test inference with model selection")

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
                    alias_or_model_id = models[model_number - 1].id  # Updated to use dot notation
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
                    alias_or_model_id = models[model_number - 1].id  # Updated to use dot notation
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

        elif choice == "8":
            test_inference_with_model_selection()

        else:
            print("Invalid choice. Please try again.")

def run_inference(alias: str, messages: List[dict]) -> None:
    """Run inference using a specified model alias and input messages.

    Args:
        alias (str): The alias of the model to use for inference.
        messages (List[dict]): A list of messages to send to the model.

    Returns:
        None
    """
    manager = FoundryLocalManager(alias)

    # Configure the client to use the local Foundry service
    client = openai.OpenAI(
        base_url=manager.endpoint,
        api_key=manager.api_key  # API key is not required for local usage
    )

    # Set the model to use and generate a streaming response
    stream = client.chat.completions.create(
        model=manager.get_model_info(alias).id,
        messages=messages,
        stream=True
    )

    # Print the streaming response
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="", flush=True)

def test_inference_with_light_prompt():
    """Test inference using the 'light' prompt from the configuration."""
    # Load the configuration to get the 'light' prompt
    config = load_config()
    light_prompt = config["prompt_sets"]["light"]["user_prompt"]

    # Define the input messages for the model
    messages = [
        {"role": "user", "content": light_prompt}
    ]

    # Use a default alias for testing
    alias = "phi-3.5-mini"

    # Run inference using the public inference function
    run_inference(alias, messages)

def test_inference_with_model_selection():
    """Test inference by selecting a model from the numbered list."""
    # Get all models with their cache state
    models = get_all_models_with_cache_state()

    # Display the models in a numbered list
    display_models_with_rich(models)

    # Prompt the user to select a model by number
    try:
        model_number = int(input("Enter the number of the model to use for inference: "))
        if 1 <= model_number <= len(models):
            alias = models[model_number - 1].id  # Use the selected model's ID
        else:
            print("Invalid model number. Please try again.")
            return
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    # Load the configuration to get the 'light' prompt
    config = load_config()
    light_prompt = config["prompt_sets"]["light"]["user_prompt"]

    # Define the input messages for the model
    messages = [
        {"role": "user", "content": light_prompt}
    ]

    # Run inference using the public inference function
    run_inference(alias, messages)

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