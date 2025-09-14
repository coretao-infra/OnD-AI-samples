import openai
from utils.config import load_config

# this is a placeholder function, we dont need to hit generic openai backends yet, because foundrylocal has its own SDK
def list_openai_models():
    """List all available models from OpenAI-compatible backends."""
    config = load_config()
    backend_config = config.get("backends", {}).get("OpenAI", {})

    if not backend_config:
        raise ValueError("OpenAI backend configuration is missing.")

    # Example: Replace with actual OpenAI API call logic
    return ["gpt-3.5-turbo", "gpt-4"]
