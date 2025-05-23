import logging
from typing import List, Set
from pathlib import Path

def load_prompt(template_path: str) -> str:
    """
    Load a prompt template from a file.

    Args:
        template_path (str): Path to the prompt template file.

    Returns:
        str: Content of the prompt template.

    Raises:
        FileNotFoundError: If the prompt file is not found.
    """
    try:
        with open(template_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        logging.error(f"Prompt file {template_path} not found")
        raise

def select_relevant_files(client, file_paths: List[str], codebase_path: Path) -> Set[str]:
    """
    Select relevant files from the codebase using the model.

    Args:
        client: Hugging Face InferenceClient instance.
        file_paths (List[str]): List of file paths in the codebase.
        codebase_path (Path): Root path of the codebase.

    Returns:
        Set[str]: Set of selected file paths.

    Raises:
        ValueError: If model response is invalid or file selection fails.
    """
    # Load file selection prompt
    prompt_template = load_prompt("config/file_selection_prompt.txt")

    # Format file paths into a string
    file_list = "\n".join(file_paths)
    try:
        prompt = prompt_template.format(file_list=file_list)
    except KeyError as e:
        logging.error(f"Prompt formatting failed: missing placeholder {e}")
        raise ValueError(f"Prompt formatting failed: missing placeholder {e}")

    # Log client configuration for debugging
    logging.info(f"Using InferenceClient with model: {client.model}, provider: novita")

    # Send to model for file selection using conversational task
    try:
        logging.info("Selecting relevant files with model")
        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000
        )
        response_text = response.choices[0].message.content
        if not response_text.strip():
            logging.error("Model returned empty response for file selection")
            raise ValueError("Model returned empty response for file selection")

        # Parse response (expecting newline-separated file paths)
        selected_files = {line.strip() for line in response_text.splitlines() if line.strip() in file_paths}
        if not selected_files:
            logging.warning("No valid files selected by model")
        else:
            logging.info(f"Selected {len(selected_files)} files: {selected_files}")
        return selected_files

    except Exception as e:
        logging.error(f"Model inference failed for file selection: {str(e)}")
        raise ValueError(f"Model inference failed for file selection: {str(e)}")