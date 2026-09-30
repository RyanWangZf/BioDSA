import tiktoken

def truncate_head_tokens(text: str, max_tokens: int, encoding_name: str = "gpt-4o"):
    encoding = tiktoken.encoding_for_model(encoding_name)
    tokens = encoding.encode(text)
    if len(tokens) > max_tokens:
        # truncate the head max_tokens tokens
        return encoding.decode(tokens[-max_tokens:])
    return text

def truncate_middle_tokens(text: str, max_tokens: int, encoding_name: str = "gpt-4o", separator: str = "\n\n[... truncated ...]\n\n"):
    """
    Truncate text by removing tokens from the middle while preserving the beginning and end.
    
    Args:
        text: The text to truncate
        max_tokens: Maximum number of tokens to keep (excluding separator)
        encoding_name: The tokenizer model to use
        separator: Text to insert between beginning and end portions
    
    Returns:
        Truncated text with beginning and end preserved, or original text if under limit
    """
    encoding = tiktoken.encoding_for_model(encoding_name)
    tokens = encoding.encode(text)
    
    if len(tokens) <= max_tokens:
        return text
    
    # Calculate how many tokens to keep from each end
    # Reserve some tokens for the separator
    separator_tokens = encoding.encode(separator)
    available_tokens = max_tokens - len(separator_tokens)
    
    # If we don't have enough space even for the separator, just truncate from the end
    if available_tokens <= 0:
        return encoding.decode(tokens[:max_tokens])
    
    # Keep half from the beginning and half from the end
    tokens_from_start = available_tokens // 2
    tokens_from_end = available_tokens - tokens_from_start
    
    # Combine the parts
    start_part = encoding.decode(tokens[:tokens_from_start])
    end_part = encoding.decode(tokens[-tokens_from_end:])
    
    return start_part + separator + end_part