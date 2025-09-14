import tiktoken
from utils.config import load_config
from utils.bench_generic_openai import list_openai_models
from utils.bench_foundrylocal import get_all_models_with_cache_state
from utils.llm_schema import Model

def count_tokens(text, model):
    """Count tokens in a given text using tiktoken."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def discover_backends():
    """Discover all available backends dynamically."""
    config = load_config()
    return list(config.get("backends", {}).keys())

def consolidated_model_list():
    """Return a consolidated list of models from all available backends."""
    backends = discover_backends()
    models = []

    for backend in backends:
        if backend == "OpenAI":
            models.extend(list_openai_models())
        elif backend == "FoundryLocal":
            models.extend(get_all_models_with_cache_state())

    return models