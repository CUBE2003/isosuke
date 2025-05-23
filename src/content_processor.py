import logging
from typing import Dict, Set
from pathlib import Path

def load_prompt(template_path: str) -> str:
    """
    Load a prompt template from a file.
    """
    try:
        with open(template_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        logging.error(f"Prompt file {template_path} not found")
        raise

def process_file_contents(client, file_paths: Set[str], codebase_path: Path) -> Dict[str, str]:
    """
    Process the contents of selected files to generate summaries.

    Args:
        client: Hugging Face InferenceClient instance.
        file_paths: Set of file paths to process.
        codebase_path: Root path of the codebase.

    Returns:
        Dict mapping file paths to their summaries.
    """
    summaries = {}
    prompt_template = load_prompt("config/content_summary_prompt.txt")

    logging.info(f"Using InferenceClient with model: {client.model}, provider: novita")

    for file_path in file_paths:
        try:
            # Resolve full path
            full_path = codebase_path / file_path
            with open(full_path, 'r', encoding='utf-8') as file:
                content = file.read()
            prompt = prompt_template.format(file_content=content, file_path=file_path)
            logging.info(f"Processing file: {file_path}")
            response = client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            summary = response.choices[0].message.content
            if not summary.strip():
                logging.warning(f"No summary generated for {file_path}")
                continue
            summaries[file_path] = summary
        except Exception as e:
            logging.error(f"Failed to process {file_path}: {str(e)}")
            continue

    return summaries