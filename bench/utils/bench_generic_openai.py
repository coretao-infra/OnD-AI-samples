
import openai
import requests
import re
from urllib.parse import urlparse
import time
from utils.llm_schema import Model, BenchmarkResult
from utils.shared import count_tokens
from utils.display import display_models_with_rich


def get_all_openai_models_with_cache_state(backend_config=None):
    """
    List all available models from a specific OpenAI-compatible backend config, as Model objects.
    """
    if backend_config is None:
        raise ValueError("backend_config must be provided for OpenAI model listing.")
    if not backend_config:
        raise ValueError("OpenAI backend configuration is missing.")
    if "endpoint_management" not in backend_config:
        raise ValueError("OpenAI backend configuration must include 'endpoint_management' as the full model list URL. No fallback or formatting allowed.")
    url = backend_config["endpoint_management"]
    headers = build_openai_auth_headers(backend_config)
    try:
        resp = requests.get(url, headers=headers, timeout=5)
    except Exception as e:
        raise RuntimeError(f"Could not fetch models from {url}: {e}")
    if resp.status_code != 200:
        raise RuntimeError(f"OpenAI backend {url} returned status {resp.status_code}: {resp.text}")
    data = resp.json()
    if "data" not in data:
        raise RuntimeError(f"OpenAI backend {url} response missing 'data' field: {data}")
    model_names = [m["id"] for m in data["data"] if "id" in m]
    # Extract device info from endpoint_management (IP or first two TLDs)
    endpoint = backend_config["endpoint_management"]
    device = "Cloud"
    ip_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", endpoint)
    if ip_match:
        device = ip_match.group(1)
    else:
        parsed = urlparse(endpoint)
        host = parsed.hostname or ""
        tlds = host.split(".")
        if len(tlds) >= 2:
            device = ".".join(tlds[-2:])
        elif host:
            device = host
    backend = backend_config.get("handler", "OpenAI")
    # For LMStudio, all models listed are local and thus 'cached' is True
    is_lmstudio = backend_config.get("endpoint", "").startswith("http://localhost:1234")
    cached_val = True if is_lmstudio else False
    models = []
    for name in model_names:
        model = Model(
            id=name,
            alias=name,
            device=device,
            size=None,  # OpenAI/LMStudio models don't expose size
            cached=cached_val,
            loaded=False,
            backend=backend
        )
        model.backend_config = backend_config  # Attach backend config for inference
        models.append(model)
    return models

def build_openai_auth_headers(backend_config):
    """Return headers dict with Authorization if required by config, else empty dict."""
    auth_required = bool(backend_config.get("auth_required", False))
    headers = {}
    if auth_required:
        api_key = backend_config.get("api_key")
        if not api_key:
            raise ValueError("OpenAI backend requires authentication but no api_key is set in config.")
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


# Streaming inference for OpenAI
def run_openai_inference(model_id: str, messages, max_tokens: int, backend_config=None):
    print("welcome_inference")
    if backend_config is None:
        raise ValueError("backend_config must be provided for OpenAI inference.")

    endpoint = backend_config.get("endpoint")
    auth_required = bool(backend_config.get("auth_required"))
    # Always pass a non-empty api_key; use dummy for LMStudio/local
    if auth_required:
        api_key = backend_config.get("api_key")
        if not api_key:
            raise ValueError("API key required but not provided in backend config.")
    else:
        api_key = "not-needed"

    client = openai.OpenAI(
        api_key=api_key,
        base_url=endpoint
    )
    
    try:
        # Use standard chat completions API which works with LMStudio
        stream = client.chat.completions.create(
            model=model_id,
            messages=messages,
            stream=True
        )
        response_text = ""
        for chunk in stream:
            if hasattr(chunk, 'choices') and chunk.choices:
                content = chunk.choices[0].delta.content if chunk.choices[0].delta.content else ""
                print(content, end="", flush=True)
                response_text += content
        print()
        return response_text
    except Exception as e:
        print(f"[ERROR] OpenAI inference failed: {e}")
        return ""

def openai_bench_inference(models_instance, system_prompt, user_prompt, max_tokens=None, backend_config=None):
    """
    Run benchmark inference using OpenAI backend.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    # backend_config must be passed from the backend object (models_instance)
    if not backend_config and hasattr(models_instance, 'backend_config'):
        backend_config = models_instance.backend_config
    if not backend_config:
        raise ValueError("backend_config must be provided for OpenAI bench inference.")
    return run_openai_inference(models_instance.id, messages, max_tokens, backend_config)
