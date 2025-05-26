# import logging
# from typing import Dict

# def load_prompt(template_path: str) -> str:
#     """
#     Load a prompt template from a file.
#     """
#     try:
#         with open(template_path, 'r') as file:
#             return file.read()
#     except FileNotFoundError:
#         logging.error(f"Prompt file {template_path} not found")
#         raise

# def generate_yaml(client, summaries: Dict[str, str]) -> str:
#     """
#     Generate YAML content from file summaries.

#     Args:
#         client: Hugging Face InferenceClient instance.
#         summaries: Dict mapping file paths to summaries.

#     Returns:
#         YAML content as a string.
#     """
#     prompt_template = load_prompt("config/yaml_generation_prompt.txt")
#     summary_text = "\n".join(f"{path}: {summary}" for path, summary in summaries.items())
    
#     try:
#         prompt = prompt_template.format(summaries=summary_text)
#     except KeyError as e:
#         logging.error(f"Prompt formatting failed: missing placeholder {e}")
#         raise ValueError(f"Prompt formatting failed: missing placeholder {e}")

#     logging.info(f"Using InferenceClient with model: {client.model}, provider: novita")

#     try:
#         logging.info("Generating YAML with model")
#         response = client.chat_completion(
#             messages=[{"role": "user", "content": prompt}],
#             max_tokens=2000
#         )
#         yaml_content = response.choices[0].message.content
#         if not yaml_content.strip():
#             logging.error("Model returned empty YAML content")
#             raise ValueError("Model returned empty YAML content")
#         return yaml_content
#     except Exception as e:
#         logging.error(f"Failed to generate YAML: {str(e)}")
#         raise ValueError(f"Failed to generate YAML: {str(e)}")


import logging
from typing import Dict
import os

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

def generate_yaml(client, summaries: Dict[str, str]) -> str:
    """
    Generate YAML content from file summaries.

    Args:
        client: Hugging Face InferenceClient instance.
        summaries: Dict mapping file paths to summaries.

    Returns:
        YAML content as a string.
    """
    prompt_template = load_prompt("config/yaml_generation_prompt.txt")
    summary_text = "\n".join(f"{path}: {summary}" for path, summary in summaries.items())
    logging.info(f"File summaries: {summary_text}")
    
    try:
        prompt = prompt_template.format(summaries=summary_text)
        logging.info(f"Model prompt: {prompt[:1000]}...")
    except KeyError as e:
        logging.error(f"Prompt formatting failed: missing placeholder {e}")
        raise ValueError(f"Prompt formatting failed: missing placeholder {e}")

    logging.info(f"Using InferenceClient with model: {client.model}, provider: novita")

    try:
        logging.info("Generating YAML with model")
        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000
        )
        yaml_content = response.choices[0].message.content
        if not yaml_content.strip():
            logging.error("Model returned empty YAML content")
            raise ValueError("Model returned empty YAML content")

        # Strip Markdown code block markers
        yaml_content = yaml_content.strip()
        if yaml_content.startswith("```yaml"):
            yaml_content = yaml_content.replace("```yaml", "", 1).strip()
        if yaml_content.endswith("```"):
            yaml_content = yaml_content.rsplit("```", 1)[0].strip()
        logging.info(f"Cleaned YAML content: {yaml_content}")

        # Save raw model response
        os.makedirs("output", exist_ok=True)
        with open("output/raw_yaml_response.yaml", "w", encoding="utf-8") as f:
            f.write(yaml_content)
        logging.info("Saved raw YAML model response to output/raw_yaml_response.yaml")
        
        # Check for generic YAML
        if "Example System" in yaml_content:
            logging.warning("Generic YAML detected; saving summaries as fallback")
            fallback_yaml = f"Description:\n  Summaries:\n    {summary_text.replace('\n', '\n    ')}"
            return fallback_yaml
        
        return yaml_content
    except Exception as e:
        logging.error(f"Failed to generate YAML: {str(e)}")
        raise ValueError(f"Failed to generate YAML: {str(e)}")