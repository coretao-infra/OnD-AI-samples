import ollama
import json
from utils.llm_schema import Model
from utils.config import get_config_value

_DEBUG = get_config_value('debug')

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
            backend='ollama'
        )
        models.append(model_obj)
    return models

def run_inference(model_id: str, messages, max_tokens: int):
    """Run inference using Ollama chat API with streaming."""
    # Format messages for Ollama
    formatted_messages = []
    for msg in messages:
        formatted_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    if _DEBUG:
        print(f"[DEBUG] Ollama chat request:")
        print(f"[DEBUG] Model: {model_id}")
        print(f"[DEBUG] Messages: {json.dumps(formatted_messages, indent=2)}")
        print(f"[DEBUG] Max tokens: {max_tokens}")
    
    response_text = ""
    chunk_count = 0
    final_stats = None
    
    try:
        # Stream response from Ollama
        stream = ollama.chat(
            model=model_id,
            messages=formatted_messages,
            stream=True,
            options={
                "num_predict": max_tokens,
            }
        )
        
        for chunk in stream:
            chunk_count += 1
            if _DEBUG:
                print(f"[DEBUG] Raw chunk: {json.dumps(chunk, indent=2)}")
            
            if chunk.get('message', {}).get('content'):
                response_text += chunk['message']['content']
            if chunk.get('done'):
                final_stats = chunk
                
        if _DEBUG:
            print(f"\n[DEBUG] Response stats:")
            print(f"  Chunks received: {chunk_count}")
            print(f"  Response length: {len(response_text)}")
            if final_stats:
                print(f"  Final chunk: {json.dumps(final_stats, indent=2)}")
                if final_stats.get('eval_count', 0) < max_tokens * 0.5:
                    print("\n[DEBUG] Response may be truncated:")
                    print("  - Model may have reached a natural stop")
                    print("  - Context length limit may be reached")
                    print("  - System prompt may be consuming context")
                    print("  - num_predict may not be fully honored")
    
    except Exception as e:
        if _DEBUG:
            print(f"[DEBUG] Error during inference: {str(e)}")
        return ""
    
    return response_text

def ollama_bench_inference(models_instance, system_prompt, user_prompt, max_tokens):
    """Run benchmark inference using Ollama."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    return run_inference(models_instance.id, messages, max_tokens)
