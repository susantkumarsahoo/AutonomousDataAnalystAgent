from langchain_classic.chains import ConversationChain
from langchain_openai import ChatOpenAI


def get_chat_chain(
                prompt, 
                memory, 
                model_name: str = "gpt-4o-mini", 
                temperature: float = 0.7,
                max_tokens: int = 500):
    """
    Creates and returns a ConversationChain using:
    - ChatPromptTemplate
    - Memory (ConversationBufferMemory)
    - ChatOpenAI model

    Args:
        prompt: ChatPromptTemplate instance.
        memory: Memory instance (buffer, window, summary, etc.)
        model_name (str): OpenAI model to use.
        temperature (float): Response creativity level.
        max_tokens (int): Maximum tokens in response.

    Returns:
        ConversationChain: Fully configured chain.
    """

    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens
    )

    chain = ConversationChain(
        llm=llm,
        memory=memory,
        prompt=prompt,
        verbose=True
    )

    return chain