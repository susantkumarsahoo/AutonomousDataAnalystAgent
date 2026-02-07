from langchain_core.messages import SystemMessage, HumanMessage


def run_chatbot(user_input: str) -> list:
    """
    Creates a basic chatbot conversation using SystemMessage and HumanMessage.
    
    Args:
        user_input (str): The message from the user.
    
    Returns:
        list: A list of messages representing the conversation.
    """

    system_msg = SystemMessage(
        content="You are a helpful AI assistant that answers clearly and politely."
    )
    
    human_msg = HumanMessage(
        content=user_input
    )
    
    conversation = [system_msg, human_msg]

    return conversation