import json
import os

def load_config():
    """Load and validate the configuration file."""
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Validate prompt sets
    if 'prompt_sets' not in config:
        raise ValueError("Missing 'prompt_sets' in configuration file.")

    for set_name, prompt_set in config['prompt_sets'].items():
        if 'max_tokens' not in prompt_set:
            raise ValueError(f"Missing 'max_tokens' in prompt set '{set_name}'.")
        if 'system_prompt' not in prompt_set:
            raise ValueError(f"Missing 'system_prompt' in prompt set '{set_name}'.")
        if 'user_prompt' not in prompt_set:
            raise ValueError(f"Missing 'user_prompt' in prompt set '{set_name}'.")

    # Validate backends
    if 'backends' not in config:
        raise ValueError("Missing 'backends' in configuration file.")

    if 'OpenAI' not in config['backends']:
        raise ValueError("Missing 'OpenAI' backend configuration.")

    if 'api_key' not in config['backends']['OpenAI']:
        raise ValueError("Missing 'api_key' in OpenAI backend configuration.")

    if 'FoundryLocal' not in config['backends']:
        raise ValueError("Missing 'FoundryLocal' backend configuration.")

    if 'alias' not in config['backends']['FoundryLocal']:
        raise ValueError("Missing 'alias' in FoundryLocal backend configuration.")

    return config

def get_bench_result_path():
    """Retrieve the path for storing benchmark results."""
    return _CONFIG.get("bench_result_path", "output/bench_result.json")

def get_config_value(key, default=None):
    """
    Retrieve a value from the configuration by key, with optional default.
    Usage: get_config_value('debug', default=False)
    """
    return _CONFIG.get(key, default)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.json')
_CONFIG = load_config()
