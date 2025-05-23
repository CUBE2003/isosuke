import os
import logging
from pathlib import Path

def generate_file_structure(codebase_path):
    """
    Generate a list of file paths from the codebase directory.

    Args:
        codebase_path (str): Path to the codebase directory.

    Returns:
        list: List of file paths relative to the codebase root.

    Raises:
        ValueError: If the codebase path is invalid or not a directory.
    """
    # Validate codebase path
    if not os.path.exists(codebase_path):
        logging.error(f"Codebase path {codebase_path} does not exist")
        raise ValueError(f"Codebase path {codebase_path} does not exist")
    if not os.path.isdir(codebase_path):
        logging.error(f"Codebase path {codebase_path} is not a directory")
        raise ValueError(f"Codebase path {codebase_path} is not a directory")

    # Convert to Path object for consistent handling
    codebase_root = Path(codebase_path).resolve()
    file_paths = []

    # Walk the directory tree
    for root, _, files in os.walk(codebase_root):
        for file in files:
            # Get full path and convert to relative path
            full_path = Path(root) / file
            relative_path = str(full_path.relative_to(codebase_root))
            file_paths.append(relative_path)

    # Log the number of files found
    logging.info(f"Generated file structure with {len(file_paths)} files")
    return file_paths