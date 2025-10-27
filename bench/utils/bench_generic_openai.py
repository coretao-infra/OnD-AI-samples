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
def list_openai_models(backend_config):
    """List all available models from a specific OpenAI-compatible backend config."""
    if not backend_config:
        raise ValueError("OpenAI backend configuration is missing.")

    # Example: Replace with actual OpenAI API call logic, using backend_config for endpoint/key
    # For now, just return a static list as before
    model_names = ["gpt-3.5-turbo", "gpt-4"]

    return [
        Model(
            id=name,
            alias=name,
            device="Cloud",
            size=None,  # OpenAI models don't expose size
            cached=False,
            loaded=False,
            backend=backend_config.get("name", "OpenAI")
        )
        for name in model_names
    ]
