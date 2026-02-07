import os
from pathlib import Path

# -------------------------
# Configuration
# -------------------------
project_folder_name = "ml_project"   # Existing root project
package_name = "chatbot"             # Main Python package name

# -------------------------
# Validate base project folder
# -------------------------
project_root = Path(project_folder_name)

if not project_root.exists():
    raise FileNotFoundError(
        f"Base project folder '{project_folder_name}' does not exist. "
        f"Please create it first."
    )

# -------------------------
# Define chatbot root
# -------------------------
chatbot_root = project_root / package_name


# -------------------------
# Files & folders to create
# -------------------------
list_of_files = [

    # Main package
    f"{chatbot_root}/__init__.py",

    # Models
    f"{chatbot_root}/llm_models/__init__.py",
    f"{chatbot_root}/llm_models/base_model.py",
    f"{chatbot_root}/llm_models/openai_model.py",

    # Services
    f"{chatbot_root}/services/__init__.py",
    f"{chatbot_root}/services/llm_service.py",
    f"{chatbot_root}/services/embedding_service.py",
    f"{chatbot_root}/services/retriever_service.py",

    # LangChain Extensions
    f"{chatbot_root}/langchain_ext/__init__.py",
    f"{chatbot_root}/langchain_ext/llms_chat_model.py",
    f"{chatbot_root}/langchain_ext/prompts.py",
    f"{chatbot_root}/langchain_ext/output_parsers.py",
    f"{chatbot_root}/langchain_ext/memory.py",
    f"{chatbot_root}/langchain_ext/chains.py",
    f"{chatbot_root}/langchain_ext/messages.py",
    f"{chatbot_root}/langchain_ext/rag_retrievers.py",
    f"{chatbot_root}/langchain_ext/embedding.py",
    f"{chatbot_root}/langchain_ext/retrievers.py",
    f"{chatbot_root}/langchain_ext/runnables.py",
    f"{chatbot_root}/langchain_ext/callbacks.py",
    f"{chatbot_root}/langchain_ext/text_splitter.py",
    f"{chatbot_root}/langchain_ext/tools_toolkits.py",
    f"{chatbot_root}/langchain_ext/document_loader.py",
    f"{chatbot_root}/langchain_ext/streaming.py",
    f"{chatbot_root}/langchain_ext/mcp_client.py",

    # LangGraph Extensions
    f"{chatbot_root}/langgraph_ext/__init__.py",
    f"{chatbot_root}/langgraph_ext/state.py",
    f"{chatbot_root}/langgraph_ext/nodes.py",
    f"{chatbot_root}/langgraph_ext/edges.py",
    f"{chatbot_root}/langgraph_ext/checkpointer.py",
    f"{chatbot_root}/langgraph_ext/persistence.py",
    f"{chatbot_root}/langgraph_ext/workflows.py",

    # Agents
    f"{chatbot_root}/agents/__init__.py",
    f"{chatbot_root}/agents/base_agent.py",
    f"{chatbot_root}/agents/planner_agent.py",
    f"{chatbot_root}/agents/agent_executor.py",
    f"{chatbot_root}/agents/conversational_agent.py",
    f"{chatbot_root}/agents/tool_agent.py",
    f"{chatbot_root}/agents/rag_agent.py",
    f"{chatbot_root}/agents/multi_agent.py",


]

# -------------------------
# Create structure
# -------------------------
for filepath in list_of_files:
    file_path = Path(filepath)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if not file_path.exists():
        file_path.touch()
        print(f"Created: {file_path}")
    else:
        print(f"Already exists: {file_path}")


