import openai
from utils.config import load_config
from utils.llm_schema import Model

def _create_model_objects(model_names):
    """Helper function to create Model objects from model names."""
    return [
        Model(
            id=name,
            alias=name,
            device="Cloud",
            size=None,  # OpenAI models don't expose size
            cached=False,
            loaded=False
        )
        for name in model_names
    ]

# this is a placeholder function, we dont need to hit generic openai backends yet, because foundrylocal has its own SDK
def list_openai_models():
    """List all available models from OpenAI-compatible backends."""
    config = load_config()
    backend_config = config.get("backends", {}).get("OpenAI", {})

    if not backend_config:
        raise ValueError("OpenAI backend configuration is missing.")

    # Example: Replace with actual OpenAI API call logic
    model_names = ["gpt-3.5-turbo", "gpt-4"]

    # Return Model objects directly
    return [
        Model(
            id=name,
            alias=name,
            device="Cloud",
            size=None,  # OpenAI models don't expose size
            cached=False,
            loaded=False,
            backend="OpenAI"
        )
        for name in model_names
    ]
