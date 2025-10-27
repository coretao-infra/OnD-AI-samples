import openai
from utils.llm_schema import Model
import requests
import re
from urllib.parse import urlparse

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

# this is a placeholder function, we dont need to hit generic openai backends yet, because foundrylocal has its own SDK
def list_openai_models(backend_config):
    """List all available models from a specific OpenAI-compatible backend config."""
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
    if not model_names:
        raise RuntimeError(f"OpenAI backend {url} returned no models.")
    # Extract device info from endpoint_management (IP or first two TLDs)
    
    endpoint = backend_config["endpoint_management"]
    device = "Cloud"
    # Try to extract IP address
    ip_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", endpoint)
    if ip_match:
        device = ip_match.group(1)
    else:
        # Extract first two TLDs from hostname
        
        parsed = urlparse(endpoint)
        host = parsed.hostname or ""
        tlds = host.split(".")
        if len(tlds) >= 2:
            device = ".".join(tlds[-2:])
        elif host:
            device = host
    return [
        Model(
            id=name,
            alias=name,
            device=device,
            size=None,  # OpenAI models don't expose size
            cached=False,
            loaded=False,
            backend=backend_config.get("name")
        )
        for name in model_names
    ]
