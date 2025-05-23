import logging
import yaml
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

def validate_and_save_yaml(client, yaml_content: str) -> None:
    """
    Validate YAML content and save to file.

    Args:
        client: Hugging Face InferenceClient instance.
        yaml_content: YAML content to validate.

    Raises:
        ValueError: If validation or saving fails.
    """
    prompt_template = load_prompt("config/correction_prompt.txt")
    
    try:
        prompt = prompt_template.format(yaml_content=yaml_content)
    except KeyError as e:
        logging.warning(f"Prompt placeholder {e} not provided, assuming only yaml_content needed")
        if 'errors' in prompt_template:
            logging.info("Prompt contains {errors} placeholder, but no errors provided; using yaml_content only")
        prompt = prompt_template.replace("{errors}", "")

    logging.info(f"Using InferenceClient with model: {client.model}, provider: novita")

    try:
        logging.info("Validating YAML with model")
        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000
        )
        corrected_yaml = response.choices[0].message.content
        if not corrected_yaml.strip():
            logging.error("Model returned empty corrected YAML")
            raise ValueError("Model returned empty corrected YAML")

        # Strip Markdown code block markers
        corrected_yaml = corrected_yaml.strip()
        if corrected_yaml.startswith("```yaml"):
            corrected_yaml = corrected_yaml.replace("```yaml", "", 1).strip()
        if corrected_yaml.endswith("```"):
            corrected_yaml = corrected_yaml.rsplit("```", 1)[0].strip()
        logging.info(f"Processed YAML content: {corrected_yaml}")

        # Check if YAML contains "Spring Petclinic"
        if "Spring Petclinic" not in corrected_yaml:
            logging.warning("YAML does not contain 'Spring Petclinic'; attempting correction")
            correction_prompt = (
                "Correct the following YAML to describe the Spring Petclinic application. "
                "Set Name to 'Spring Petclinic', Type to 'Web Application', "
                "and ensure components include controllers, services, and database. "
                "Return only the corrected YAML:\n" + corrected_yaml
            )
            response = client.chat_completion(
                messages=[{"role": "user", "content": correction_prompt}],
                max_tokens=4000
            )
            corrected_yaml = response.choices[0].message.content
            logging.info(f"Corrected YAML content: {corrected_yaml}")

        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)

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