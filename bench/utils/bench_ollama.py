import requests
import os
from utils.llm_schema import Model
import openai

DEBUG = os.getenv("OLLAMA_DEBUG", "0") == "1"

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
    if DEBUG:
        print(f"[DEBUG] Retrieved {len(data)} Ollama models from API")
    return models

def run_inference(model_id: str, messages, max_tokens: int):
    client = openai.OpenAI(base_url="http://localhost:11434/v1", api_key="")
    return client.chat.completions.create(
        model=model_id,
        messages=messages,
        stream=True,
        max_tokens=max_tokens
    )

def ollama_bench_inference(models_instance, system_prompt, user_prompt, max_tokens):
    """Stream inference using Ollama local server via OpenAI client."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    print("[INFO] Streaming response:")
    response_text = ""
    for chunk in run_inference(models_instance.id, messages, max_tokens=max_tokens):
        if hasattr(chunk, 'choices') and chunk.choices:
            content = chunk.choices[0].delta.content if chunk.choices[0].delta.content else ""
            print(content, end="", flush=True)
            response_text += content
        else:
            if DEBUG:
                print("[DEBUG] Invalid chunk format", flush=True)
    return response_text
