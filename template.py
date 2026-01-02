import os
from pathlib import Path

# -------------------------
# Define project name (main package)
# -------------------------
project_name = "ml_project" 

# -------------------------
# Define additional folders
# -------------------------
cicd_folder       = ".github"
configs_folder    = "configs"
data_folder       = "data"
artifacts_folder  = "deployment_artifacts"
notebooks_folder  = "notebooks"
static_css_folder = "static/css"
templates_folder  = "templates"
tests_folder      = "tests"
scripts_folder    = "scripts"
docs_folder       = "docs"
logs_folder       = "logs"

# -------------------------
# List of files & folders to create
# -------------------------
list_of_files = [

    # =========================
    # Main package
    # =========================
    f"{project_name}/__init__.py",

    # -------------------------
    # Config
    # -------------------------
    f"{project_name}/config/__init__.py",
    f"{project_name}/config/src_config.yaml",
    f"{project_name}/config/model_architecture.yaml",
    f"{project_name}/config/config.py",

    # -------------------------
    # Integrations
    # -------------------------
    f"{project_name}/integrations/__init__.py",
    f"{project_name}/integrations/aws_integration.py",
    f"{project_name}/integrations/database_integration.py",

    # -------------------------
    # Constants
    # -------------------------
    f"{project_name}/constants/__init__.py",
    f"{project_name}/constants/paths.py",

    # -------------------------
    # Data access
    # -------------------------
    f"{project_name}/data_access/__init__.py",
    f"{project_name}/data_access/data_loader.py",
    f"{project_name}/data_access/data_augmentation.py",

    # -------------------------
    # Entities
    # -------------------------
    f"{project_name}/entities/__init__.py",
    f"{project_name}/entities/artifact_entity.py",
    f"{project_name}/entities/component_config_entity.py",
    f"{project_name}/entities/model_config_entity.py",
    f"{project_name}/entities/pipeline_config_entity.py",

    # -------------------------
    # Components
    # -------------------------
    f"{project_name}/components/__init__.py",
    f"{project_name}/components/data_ingestion.py",
    f"{project_name}/components/data_validation.py",
    f"{project_name}/components/data_preprocessing.py",
    f"{project_name}/components/feature_engineering.py",
    f"{project_name}/components/feature_transformation.py",

    # -------------------------
    # Models
    # -------------------------
    f"{project_name}/models/__init__.py",
    f"{project_name}/models/base.py",
    f"{project_name}/models/trainer.py",
    f"{project_name}/models/predictor.py",
    f"{project_name}/models/evaluator.py",
    f"{project_name}/models/registry.py",
    f"{project_name}/models/factory.py",
    f"{project_name}/models/deployer.py",

    # -------------------------
    # Pipelines
    # -------------------------
    f"{project_name}/pipelines/__init__.py",
    f"{project_name}/pipelines/ingestion_pipeline.py",
    f"{project_name}/pipelines/validation_pipeline.py",
    f"{project_name}/pipelines/preprocessing_pipeline.py",
    f"{project_name}/pipelines/feature_engineering_pipeline.py",
    f"{project_name}/pipelines/feature_transformer_pipeline.py",
    f"{project_name}/pipelines/training_pipeline.py",
    f"{project_name}/pipelines/evaluation_pipeline.py",
    f"{project_name}/pipelines/prediction_pipeline.py",
    f"{project_name}/pipelines/registry_pipeline.py",
    f"{project_name}/pipelines/inference_pipeline.py",
    f"{project_name}/pipelines/deployment_pipeline.py",
    f"{project_name}/pipelines/run_pipeline.py",

    # -------------------------
    # Logger
    # -------------------------
    f"{project_name}/logger/__init__.py",
    f"{project_name}/logger/custom_logger.py",

    # -------------------------
    # Exceptions
    # -------------------------
    f"{project_name}/exceptions/__init__.py",
    f"{project_name}/exceptions/exception.py",

    # -------------------------
    # Utilities (NO API LOGIC)
    # -------------------------
    f"{project_name}/utils/__init__.py",
    f"{project_name}/utils/helper.py",
    f"{project_name}/utils/ingestion_helper.py",
    f"{project_name}/utils/validation_helper.py",
    f"{project_name}/utils/preprocessing_helper.py",
    f"{project_name}/utils/feature_engineering_helper.py",
    f"{project_name}/utils/feature_transformer_helper.py",
    f"{project_name}/utils/training_helper.py",
    f"{project_name}/utils/prediction_helper.py",
    f"{project_name}/utils/registry_helper.py",
    f"{project_name}/utils/evaluation_helper.py",
    f"{project_name}/utils/deployment_helper.py",

    # -------------------------
    # Visualization
    # -------------------------
    f"{project_name}/visualization/__init__.py",
    f"{project_name}/visualization/plots.py",
    f"{project_name}/visualization/dashboard.py",

    # -------------------------
    # Cloud
    # -------------------------
    f"{project_name}/cloud/__init__.py",
    f"{project_name}/cloud/aws_storage.py",

    # -------------------------
    # Frontend API (Streamlit)
    # -------------------------
    f"{project_name}/frontend_api/__init__.py",
    f"{project_name}/frontend_api/streamlit_app.py",

    # -------------------------
    # Backend API (FastAPI / Flask)
    # -------------------------
    f"{project_name}/backend_api/__init__.py",
    f"{project_name}/backend_api/fastapi_router.py",
    f"{project_name}/backend_api/flask_router.py",

    # -------------------------
    # Database
    # -------------------------
    f"{project_name}/database/__init__.py",
    f"{project_name}/database/database.py",

    # -------------------------
    # Monitoring
    # -------------------------
    f"{project_name}/monitoring/__init__.py",
    f"{project_name}/monitoring/drift_detector.py",
    f"{project_name}/monitoring/data_drift.py",
    f"{project_name}/monitoring/model_drift.py",

    # =========================
    # Outside main package
    # =========================
    f"{cicd_folder}/pipeline.yml",

    f"{configs_folder}/project_configs.yaml",
    f"{configs_folder}/model_configs.yaml",

    f"{data_folder}/raw/.gitkeep",

    f"{artifacts_folder}/models/.gitkeep",
    f"{artifacts_folder}/.gitkeep",

    f"{notebooks_folder}/README.md",
    f"{notebooks_folder}/.gitkeep",

    f"{templates_folder}/project.html",
    f"{static_css_folder}/style.css",

    # -------------------------
    # Scripts
    # -------------------------
    f"{scripts_folder}/data_automation.py",
    f"{scripts_folder}/run_pipeline.sh",
    f"{scripts_folder}/run_pipeline.bat",
    f"{scripts_folder}/db_migrations.py",

    # -------------------------
    # Tests
    # -------------------------
    f"{tests_folder}/__init__.py",
    f"{tests_folder}/conftest.py",
    f"{tests_folder}/test_models.py",
    f"{tests_folder}/test_api.py",
    f"{tests_folder}/test_data_pipeline.py",

    # -------------------------
    # Docs
    # -------------------------
    f"{docs_folder}/data_dictionary.md",
    f"{docs_folder}/architecture.md",
    f"{docs_folder}/pipeline_flow.md",

    # -------------------------
    # Logs
    # -------------------------
    f"{logs_folder}/.gitkeep",

    # -------------------------
    # Root files
    # -------------------------
    "requirements.txt",
    "requirements-dev.txt",
    ".env",
#   ".gitignore",
    "pyproject.toml",
    ".dockerignore",
    "Dockerfile",
    "docker-compose.yaml",
    "main.py",
    "app.py",
    "demo.py",
]

# -------------------------
# Create files and directories
# -------------------------
for filepath in list_of_files:
    file_path = Path(filepath)
    os.makedirs(file_path.parent, exist_ok=True)
    if not file_path.exists():
        file_path.touch()
        print(f"Created: {file_path}")
    else:
        print(f"Already exists: {file_path}")