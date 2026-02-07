from langchain_openai import ChatOpenAI


def get_chat_model(
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 500):
    """
    Returns a ChatOpenAI model instance.

    Args:
        api_key (str): Your OpenAI API key.
        model (str): Model to use (gpt-3.5-turbo, gpt-4, gpt-4o-mini, etc.)
        temperature (float): Creativity level (0.0 to 1.0)
        max_tokens (int): Token limit.

    Returns:
        ChatOpenAI: Configured LLM instance.
    """

    llm = ChatOpenAI(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return llm