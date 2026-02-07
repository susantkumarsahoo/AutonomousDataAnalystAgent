from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def get_chat_prompt(system_message: str) -> ChatPromptTemplate:
    """
    Creates and returns a ChatPromptTemplate with:
    - system message
    - history placeholder
    - user input placeholder

    Args:
        system_message (str): System instructions for the LLM.

    Returns:
        ChatPromptTemplate: Configured prompt ready for chatbot pipeline.
    """

    prompt_messages = [
        ("system", system_message),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ]

    return ChatPromptTemplate.from_messages(prompt_messages)