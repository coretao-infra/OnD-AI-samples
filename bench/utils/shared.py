import tiktoken

def count_tokens(text):
    """
    Count the number of tokens in a given text using the cl100k_base encoding.

    Args:
        text (str): The input text to tokenize.

    Returns:
        int: The number of tokens in the text.
    """
    # Use the cl100k_base encoding, which is compatible with GPT models
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))
