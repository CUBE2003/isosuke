

import logging
import yaml
import os

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

def validate_and_save_yaml(client, yaml_content: str) -> None:
    """
    Validate YAML content and save to file.

    Args:
        client: OpenAI client instance (configured for OpenRouter API).
        yaml_content: YAML content to validate.

    Raises:
        ValueError: If validation or saving fails.
    """
    # Strip Markdown markers from input YAML
    yaml_content = yaml_content.strip()
    if yaml_content.startswith("```yaml"):
        yaml_content = yaml_content.replace("```yaml", "", 1).strip()
    if yaml_content.endswith("```"):
        yaml_content = yaml_content.rsplit("```", 1)[0].strip()
    logging.info(f"Cleaned input YAML content: {yaml_content}")

    prompt_template = load_prompt("config/correction_prompt.txt")
    errors = ""  # Placeholder for errors; will be populated if parsing fails
    
    try:
        yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        errors = str(e)
        logging.warning(f"Initial YAML parsing failed: {errors}")

    try:
        prompt = prompt_template.format(yaml_content=yaml_content, errors=errors)
    except KeyError as e:
        logging.warning(f"Prompt placeholder {e} not provided; using yaml_content only")
        prompt = prompt_template.replace("{errors}", errors).replace("{yaml_content}", yaml_content)

    logging.info("Using OpenAI client with OpenRouter API, model: deepseek/deepseek-chat-v3-0324:free")

    try:
        logging.info("Validating YAML with model")
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3-0324:free",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            extra_headers={
                "HTTP-Referer": "your-site-url",  # Optional: replace with your site URL
                "X-Title": "your-site-name"       # Optional: replace with your site name
            }
        )
        corrected_yaml = response.choices[0].message.content
        if not corrected_yaml.strip():
            logging.error("Model returned empty corrected YAML")
            raise ValueError("Model returned empty corrected YAML")

        # Save raw corrected response
        os.makedirs("output", exist_ok=True)
        with open("output/corrected_yaml_response.yaml", "w", encoding="utf-8") as f:
            f.write(corrected_yaml)
        logging.info("Saved corrected YAML model response to output/corrected_yaml_response.yaml")

        # Strip Markdown code block markers
        corrected_yaml = corrected_yaml.strip()
        if corrected_yaml.startswith("```yaml") or corrected_yaml.startswith("```"):
            corrected_yaml = corrected_yaml.lstrip("```yaml").lstrip("```").strip()
        if corrected_yaml.endswith("```"):
            corrected_yaml = corrected_yaml.rsplit("```", 1)[0].strip()
        logging.info(f"Processed YAML content: {corrected_yaml}")

        # Generic validation: check for non-empty project name
        try:
            parsed_yaml = yaml.safe_load(corrected_yaml)
            project_name = parsed_yaml.get("Description", {}).get("Name", "")
            if not project_name or project_name in ["Example System", ""]:
                logging.warning("Invalid or generic project name detected; attempting correction")
                correction_prompt = (
                    "Correct the following YAML to describe a software application. "
                    "Ensure Description.Name is a non-empty, specific project name derived from the repository context, "
                    "Type is appropriate (e.g., 'Web Application', 'API'), "
                    "and components reflect the application structure. "
                    "Avoid generic terms like 'Example System'. "
                    "Return only the corrected YAML:\n" + corrected_yaml
                )
                response = client.chat.completions.create(
                    model="deepseek/deepseek-chat-v3-0324:free",
                    messages=[{"role": "user", "content": correction_prompt}],
                    max_tokens=4000,
                    extra_headers={
                        "HTTP-Referer": "your-site-url",  # Optional: replace with your site URL
                        "X-Title": "your-site-name"       # Optional: replace with your site name
                    }
                )
                corrected_yaml = response.choices[0].message.content
                logging.info(f"Corrected YAML content: {corrected_yaml}")
                
                # Save final corrected response
                with open("output/corrected_yaml_response.yaml", "a", encoding="utf-8") as f:
                    f.write("\n---\n" + corrected_yaml)
                logging.info("Appended final corrected YAML to output/corrected_yaml_response.yaml")
        except yaml.YAMLError:
            pass  # Handled below

        # Validate YAML syntax
        try:
            yaml.safe_load(corrected_yaml)
        except yaml.YAMLError as e:
            logging.warning(f"YAML validation failed: {str(e)}. Saving raw yaml_content as fallback")
            with open("output/architecture.yaml", "w") as f:
                f.write(yaml_content)
            logging.info("Raw YAML saved to output/architecture.yaml as fallback")
            return

        # Save to file
        with open("output/architecture.yaml", "w") as f:
            f.write(corrected_yaml)
        logging.info("YAML validated and saved to output/architecture.yaml")

    except Exception as e:
        logging.error(f"Failed to validate or save YAML: {str(e)}")
        raise ValueError(f"Failed to validate or save YAML: {str(e)}")