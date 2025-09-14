import openai
import tiktoken
from .foundrylocal import FoundryLocalManagerWrapper  # Abstracted Foundry Local wrapper
from utils.config import load_config

def count_tokens(text, model):
    """Count tokens in a given text using tiktoken."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def generate_response(system_prompt, user_prompt, model):
    """Generate a response using the OpenAI API."""
    config = load_config()
    backend_config = config["backends"].get("OpenAI")
    if not backend_config:
        raise ValueError("OpenAI backend configuration is missing.")

    # Configure OpenAI client
    openai.api_base = backend_config["endpoint"]
    openai.api_key = backend_config["api_key"]

    # Count tokens and calculate max tokens
    total_limit = 4096  # Example for GPT-3.5-turbo
    system_tokens = count_tokens(system_prompt, model)
    user_tokens = count_tokens(user_prompt, model)
    max_tokens = total_limit - (system_tokens + user_tokens)

    # Generate response
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content

def list_backends():
    """List all configured LLM backends."""
    config = load_config()
    return list(config.get("backends", {}).keys())

def list_models(backend=None):
    """List the consolidated model inventory.

    Args:
        backend (str, optional): Specify a backend to filter models. Defaults to None.

    Returns:
        list: A list of models available in the specified backend or all backends.
    """
    if backend == "OpenAI":
        # Example: Replace with actual OpenAI SDK logic
        return ["gpt-3.5-turbo", "gpt-4"]
    elif backend == "FoundryLocal":
        # Example: Replace with actual FoundryLocal SDK logic
        manager = FoundryLocalManagerWrapper()
        return manager.list_available_models()
    else:
        # Consolidate models from all backends dynamically
        models = []
        models.extend(list_models("OpenAI"))
        models.extend(list_models("FoundryLocal"))
        return models