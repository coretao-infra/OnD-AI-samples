import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.json')

def load_config():
    """Load and validate the configuration file."""
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")

    with open(CONFIG_PATH, 'r') as file:
        config = json.load(file)

    if 'default_model_alias' not in config:
        raise ValueError("Missing 'default_model_alias' in configuration file.")

    return config