import argparse
import logging
import os
from pathlib import Path
from src.structure_generator import generate_file_structure
from src.file_selector import select_relevant_files
from src.content_processor import process_file_contents
from src.yaml_generator import generate_yaml
from src.yaml_validator import validate_and_save_yaml
from huggingface_hub import InferenceClient

def setup_logging():
    """Set up logging to file and console."""
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/pipeline.log"),
            logging.StreamHandler()
        ]
    )

def main():
    """Main function to run the YAML generator pipeline."""
    setup_logging()
    parser = argparse.ArgumentParser(description="Generate network architecture YAML from codebase")
    parser.add_argument("codebase_path", help="Path to the codebase directory")
    parser.add_argument("--api-key", required=True, help="Hugging Face or Novita API key")
    args = parser.parse_args()

    codebase_path = Path(args.codebase_path)
    if not codebase_path.is_dir():
        logging.error(f"Invalid codebase path: {codebase_path}")
        raise ValueError(f"Invalid codebase path: {codebase_path}")

    # Initialize InferenceClient with Novita provider
    client = InferenceClient(
        model="deepseek-ai/DeepSeek-V3",
        token=args.api_key,
        provider="novita"
    )
    logging.info("Initialized InferenceClient with model: deepseek-ai/DeepSeek-V3, provider: novita")

    try:
        # Step 1: Generate file structure
        logging.info("Generating file structure")
        file_paths = generate_file_structure(codebase_path)

        # Step 2: Select relevant files
        logging.info("Selecting relevant files")
        selected_files = select_relevant_files(client, file_paths, codebase_path)
        if not selected_files:
            logging.warning("No relevant files selected")
            return

        # Step 3: Process file contents
        logging.info("Processing file contents")
        summaries = process_file_contents(client, selected_files, codebase_path)
        if not summaries:
            logging.warning("No summaries generated")
            return

        # Step 4: Generate YAML
        logging.info("Generating YAML")
        yaml_content = generate_yaml(client, summaries)

        # Step 5: Validate and save YAML
        logging.info("Validating and saving YAML")
        validate_and_save_yaml(client, yaml_content)

    except Exception as e:
        logging.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()