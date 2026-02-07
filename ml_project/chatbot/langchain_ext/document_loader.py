import os
from dotenv import load_dotenv


def get_openai_api_key() -> str:
    """
    Loads the OPENAI_API_KEY from the .env file and returns it.
    Raises ValueError if the key is not found.
    """
    load_dotenv()  # Load environment variables from .env
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found. Please add it to your .env file.")
    return api_key