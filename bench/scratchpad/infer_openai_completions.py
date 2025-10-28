from openai import OpenAI

client = OpenAI(
    api_key="no-key",
    base_url="http://localhost:1234/v1"
)

print("Starting completions inference...")

# Create parameter object for traceability
completion_params = {
    "model": 'microsoft/phi-4',
    "prompt": "Explain why the number 42 is the answer to life, the universe, and everything, but also why it might not be the right question.",
    "stream": True,
    "max_tokens": 1000
}

print(f"DEBUG: Completion request parameters: {completion_params}")

try:
    stream = client.completions.create(**completion_params)

    for chunk in stream:
        print(f"DEBUG: Received chunk: {chunk}")
        # Extract the content from completions stream
        if chunk.choices and len(chunk.choices) > 0:
            choice = chunk.choices[0]
            if hasattr(choice, 'text') and choice.text is not None:
                print(choice.text, end="", flush=True)
            elif hasattr(choice, 'finish_reason') and choice.finish_reason:
                print(f"\nDEBUG: Stream finished with reason: {choice.finish_reason}")
    
    print()  # Ensure newline at the end
except Exception as e:
    print(f"Inference failed: {e}")