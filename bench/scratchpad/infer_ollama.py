from ollama import chat

stream = chat(
    model='qwen3:4b',
    messages=[
        {'role': 'system', 'content': 'You are a text generator. Your responses should be repeatable and utilize *all* the remaining word count budget effectively. Your response should be approximately 714 words long.'},
        {'role': 'user', 'content': 'Explain why the number 42 is the answer to life, the universe, and everything, but also why it might not be the right question. Provide examples of how this concept has been interpreted in literature, philosophy, and pop culture. Include a brief discussion on the significance of asking the right questions in problem-solving and decision-making.'},
    ],
    stream=True
)

current_mode = None  # 'thinking' or 'responding'
for chunk in stream:
    msg = getattr(chunk, 'message', None)
    if not msg:
        continue
    content = getattr(msg, 'content', '')
    thinking = getattr(msg, 'thinking', '')
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
print()