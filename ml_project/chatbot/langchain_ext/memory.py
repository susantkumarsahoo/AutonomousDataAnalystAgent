from langchain_classic.memory import ConversationBufferMemory


def get_memory():
    """
    Returns a ConversationBufferMemory instance.
    Use this function anywhere in your project to get memory.
    """
    memory = ConversationBufferMemory(
        memory_key="history",
        return_messages=True
    )
    return memory
