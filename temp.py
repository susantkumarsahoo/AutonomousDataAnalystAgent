import os

BASE_PATH = r"C:\Users\TPWODL\New folder_Content\AutonomousDataAnalystAgent\ml_project"

PROJECT_STRUCTURE = {
    "enterprise-chatbot": {
        "frontend": {
            "__init__.py": "",
            "app.py": "",
            "components": {
                "__init__.py": "",
                "chat_interface.py": "",
                "sidebar.py": ""
            }
        },
        "backend": {
            "__init__.py": "",
            "main.py": "",
            "api": {
                "__init__.py": "",
                "chat.py": "",
                "sessions.py": "",
                "health.py": ""
            },
            "models": {
                "__init__.py": "",
                "requests.py": "",
                "responses.py": ""
            },
            "middleware": {
                "__init__.py": "",
                "logging_middleware.py": ""
            }
        },
        "ai_orchestration": {
            "__init__.py": "",
            "graph": {
                "__init__.py": "",
                "chatbot_graph.py": "",
                "nodes.py": ""
            },
            "chains": {
                "__init__.py": "",
                "conversation_chain.py": "",
                "reasoning_chain.py": ""
            },
            "prompts": {
                "__init__.py": "",
                "system_prompts.py": "",
                "user_prompts.py": ""
            },
            "memory": {
                "__init__.py": "",
                "conversation_memory.py": ""
            }
        },
        "database": {
            "__init__.py": "",
            "models.py": "",
            "session.py": "",
            "repository.py": ""
        },
        "config": {
            "__init__.py": "",
            "settings.py": "",
            "logging_config.py": ""
        },
        "tests": {
            "__init__.py": "",
            "test_api.py": "",
            "test_graph.py": "",
            "test_database.py": ""
        },
        "docs": {
            "architecture.md": "",
            "api_reference.md": "",
            "deployment.md": ""
        },
        "logs": {},
        ".env.example": "",
        ".gitignore": "",
        "requirements.txt": "",
        "docker-compose.yml": "",
        "Dockerfile": "",
        "README.md": ""
    }
}


def create_structure(base_path: str, structure: dict):
    for name, content in structure.items():
        path = os.path.join(base_path, name)

        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)


if __name__ == "__main__":
    os.makedirs(BASE_PATH, exist_ok=True)
    create_structure(BASE_PATH, PROJECT_STRUCTURE)
    print("Project structure successfully created at:")
    print(BASE_PATH)
