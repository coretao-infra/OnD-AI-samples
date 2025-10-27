from ollama import chat

stream = chat(
    model='qwen3:4b',
    messages=[
        {'role': 'system', 'content': 'You are a text generator. Your responses should be repeatable and utilize *all* the remaining word count budget effectively. Your response should be approximately 714 words long.'},
        {'role': 'user', 'content': 'Explain why the number 42 is the answer to life, the universe, and everything, but also why it might not be the right question. Provide examples of how this concept has been interpreted in literature, philosophy, and pop culture. Include a brief discussion on the significance of asking the right questions in problem-solving and decision-making.'},
    ],
    stream=True
)

for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)
print()