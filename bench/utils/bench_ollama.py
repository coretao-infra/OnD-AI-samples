import requests
from utils.llm_schema import Model

def get_all_ollama_models_with_cache_state():
    """
    Query Ollama for available local models and return them as Model objects.
    """
    try:
        response = requests.get("http://localhost:11434/v1/models", timeout=2)
        response.raise_for_status()
        data = response.json().get("data", [])
    except Exception:
        data = []
    models = []
    for m in data:
        models.append(Model(
            id=m.get("id", ""),
            alias=m.get("id", ""),
            device="Local",
            size=None,  # Ollama does not provide size in API
            cached=True,
            loaded=True,
            backend="Ollama"
        ))
    return models
