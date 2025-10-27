import ollama
import json
import traceback
from utils.llm_schema import Model
from utils.config import get_config_value

_DEBUG = get_config_value('debug')
if _DEBUG:
    print("[DEBUG] Ollama module loaded")

def get_all_ollama_models_with_cache_state():
    """
    Query Ollama for available local models and return them as Model objects.
    Adds cache state if available.
    """
    client = ollama.Client()
    result = client.list()
    models = []
    for m in result.models:
        details = m.details
        # Try to discover if cached/loaded are boolean, else set to 'Unknown'
        cached = getattr(m, 'cached', None)
        loaded = getattr(m, 'loaded', None)
        cached_val = cached if isinstance(cached, bool) else 'Unknown'
        loaded_val = loaded if isinstance(loaded, bool) else 'Unknown'
        model_obj = Model(
            id=m.model,
            alias=details.family,
            device=getattr(details, 'device', ''),
            size=int(m.size / (1024 * 1024)),
            cached=cached_val,
            loaded=loaded_val,
            backend='Ollama'
        )
        models.append(model_obj)
    return models

def run_inference(model_id: str, messages, max_tokens: int):
    """Streaming inference using Ollama. Returns final concatenated text only."""
    try:
        client = ollama.Client()
        if _DEBUG:
            print(f"[DEBUG] Starting stream model={model_id} tokens={max_tokens}")
        stream = client.chat(
            model=model_id,
            #options={"num_predict": max_tokens},
            messages=messages,
            stream=True
        )
        parts = []
        current_mode = None  # 'thinking' or 'responding'
        for chunk in stream:
            msg = chunk.get('message') if isinstance(chunk, dict) else getattr(chunk, 'message', None)
            if not msg:
                continue
            content = msg.get('content') if isinstance(msg, dict) else getattr(msg, 'content', '')
            thinking = msg.get('thinking') if isinstance(msg, dict) else getattr(msg, 'thinking', '')
            if content:
                mode = 'responding'
                token = content
            elif thinking:
                mode = 'thinking'
                token = thinking
            else:
                continue
            if mode != current_mode:
                print(f"\n[{mode}]", end='')
                current_mode = mode
            print(token, end='', flush=True)
            if mode == 'responding':
                parts.append(token)
        print()  # newline after stream
        return ''.join(parts)
    except Exception as e:
        if _DEBUG:
            print(f"[DEBUG] Ollama error: {e}")
            traceback.print_exc()
        return ""

def ollama_bench_inference(models_instance, system_prompt, user_prompt, max_tokens):
    """Run benchmark inference using Ollama."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    return run_inference(models_instance.id, messages, max_tokens)
