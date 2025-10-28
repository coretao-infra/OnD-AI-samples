from openai import OpenAI

client = OpenAI(
    api_key="no-key",
    base_url="http://localhost:1234/v1"
)

print("Starting inference...")

# Create parameter object for traceability
completion_params = {
    "model": 'microsoft/phi-4',
    "messages": [
        {
            "role": "user", 
            "content": "Hello! What is your name?"
        },
                {
            "role": "system", 
            "content": "Your name is Assi"
        }
    ],
    "stream": True,
    "max_tokens": 1000,
    "temperature": 0.8
}

print(f"DEBUG: Completion request parameters: {completion_params}")

try:
    stream = client.chat.completions.create(**completion_params)

    for chunk in stream:        
        # Extract the content delta from chat completions stream
        if chunk.choices and len(chunk.choices) > 0:
            choice = chunk.choices[0]
            if choice.delta and choice.delta.content is not None:
                print(choice.delta.content, end="", flush=True)
            elif choice.finish_reason:
                print(f"\nDEBUG: Stream finished with reason: {choice.finish_reason}")
    
    print()  # Ensure newline at the end
except Exception as e:
    print(f"Inference failed: {e}")
