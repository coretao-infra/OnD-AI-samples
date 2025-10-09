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

def ollama_bench_inference(models_instance, system_prompt, user_prompt, max_tokens=1000):
    """
    Perform inference on Ollama using the OpenAI-compatible local API.
    """
    url = "http://localhost:11434/v1/chat/completions"
    data = {
        "model": models_instance.id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": max_tokens
    }
    try:
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        resp_json = response.json()
        return resp_json["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Ollama inference failed: {e}"
