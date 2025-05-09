import logging
import json
import os
import yaml         # For reading prompt files
import openai       # For GPT API calls
import pathlib      # For robust path handling
import azure.functions as func

# Import shared helpers
from helper_functions import blob_helpers, config

# --- Configuration ---

OPENAI_API_KEY = config.get_setting(config.OPENAI_API_KEY_NAME, required=True)
OPENAI_MODEL = config.get_setting(config.OPENAI_MODEL_NAME, default_value="gpt-4o") 
STORAGE_CONN_STR_NAME = config.STORAGE_CONNECTION_STRING_NAME #
PROMPT_BASE_DIR = pathlib.Path(__file__).parent.parent / config.DEFAULT_PROMPT_DIR # 

#python body to call
"""
{
    "input_container": "01raw",
    "input_blob": "company_data.txt",
    "output_container": "02cleansed",
    "output_blob": "company_summary.txt",
    "prompt_name": "profiling.yaml"
}
"""




if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
else:
    logging.error("OpenAI API Key is not configured. Function cannot proceed.")
  

# --- Main Function Logic ---
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function `ProcessBlobWithGPT` started processing a request.')

    # --- 1. Get Parameters from Request ---
    try:
        req_body = req.get_json()
    except ValueError:
        logging.error("Request body is not valid JSON.")
        return func.HttpResponse("Please pass a valid JSON request body", status_code=400)

    input_container = req_body.get('input_container')
    input_blob = req_body.get('input_blob')
    output_container = req_body.get('output_container')
    output_blob = req_body.get('output_blob') 
    prompt_name = req_body.get('prompt_name') 

    if not all([input_container, input_blob, output_container, output_blob, prompt_name]):
        missing_params = [k for k, v in req_body.items() if not v]
        logging.error(f"Missing required parameters in request body: {missing_params}")
        return func.HttpResponse(
             "Missing required JSON parameters: input_container, input_blob, output_container, output_blob, prompt_name",
             status_code=400
        )

    logging.info(f"Processing request for: \n Input: {input_container}/{input_blob} \n Output: {output_container}/{output_blob} \n Prompt: {prompt_name}.yaml")

    # --- 2. Read Input Blob ---
    try:
        input_content = blob_helpers.read_blob_content(
            container_name=input_container,
            blob_name=input_blob,
            connection_string_env_var=STORAGE_CONN_STR_NAME
        )
        if input_content is None:
            # Error already logged by helper
             return func.HttpResponse(f"Failed to read input blob: {input_container}/{input_blob}", status_code=404) # Or 500 if it wasn't 'not found'
    except Exception as e:
         logging.exception(f"Unexpected error reading blob: {e}") # Log full traceback
         return func.HttpResponse("An error occurred while reading the input file.", status_code=500)


    # --- 3. Load Prompt from YAML ---
    prompt_file_path = PROMPT_BASE_DIR / f"{prompt_name}.yaml"
    logging.info(f"Attempting to load prompt from: {prompt_file_path}")

    try:
        
        if not prompt_file_path.is_file():
             logging.error(f"Prompt file not found at path: {prompt_file_path}")
             return func.HttpResponse(f"Prompt file '{prompt_name}.yaml' not found.", status_code=400)

        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompt_data = yaml.safe_load(f)

        if not prompt_data or 'prompt_template' not in prompt_data:
            logging.error(f"Invalid YAML structure or missing 'prompt_template' key in {prompt_file_path}")
            return func.HttpResponse(f"Invalid prompt file format for '{prompt_name}.yaml'.", status_code=500)

        prompt_template = prompt_data['prompt_template']
        logging.info(f"Successfully loaded prompt template: {prompt_name}")

    except yaml.YAMLError as ye:
        logging.error(f"Error parsing YAML prompt file {prompt_file_path}: {ye}")
        return func.HttpResponse("Error processing prompt file.", status_code=500)
    except IOError as ioe:
         logging.error(f"Error reading prompt file {prompt_file_path}: {ioe}")
         return func.HttpResponse("Could not read prompt file.", status_code=500)
    except Exception as e:
         logging.exception(f"Unexpected error loading prompt: {e}")
         return func.HttpResponse("An error occurred while loading the prompt.", status_code=500)

    # --- 4. Prepare and Call GPT API ---
    if not OPENAI_API_KEY:
         # Check again in case it failed to load initially
         logging.error("OpenAI API Key is not configured. Cannot call API.")
         return func.HttpResponse("OpenAI API Key not configured on the server.", status_code=500)

    try:
        
        formatted_prompt = prompt_template.format(document_content=input_content)

        logging.info(f"Sending request to OpenAI API. Model: {OPENAI_MODEL}")
        
        response = openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                
                {"role": "user", "content": formatted_prompt}
            ],
            
        )

        # Extract the response text
        gpt_response_text = response.choices[0].message.content.strip()
        logging.info("Received response from OpenAI API.")

    except openai.APIError as api_err:
        logging.error(f"OpenAI API Error: {api_err}. Status={api_err.status_code}, Message={api_err.message}")
        return func.HttpResponse(f"OpenAI API returned an error: {api_err.message}", status_code=api_err.status_code or 502) # 502 Bad Gateway often appropriate
    except Exception as e:
        logging.exception(f"Unexpected error calling OpenAI API: {e}")
        return func.HttpResponse("An error occurred while communicating with the GPT API.", status_code=500)

    # --- 5. Write Output Blob ---
    try:
        success = blob_helpers.write_blob_content(
            container_name=output_container,
            blob_name=output_blob,
            content=gpt_response_text, #
            connection_string_env_var=STORAGE_CONN_STR_NAME,
            overwrite=True # Overwrite if it exists
        )

        if not success:
            # Error already logged by helper
            return func.HttpResponse(f"Failed to write output blob: {output_container}/{output_blob}", status_code=500)

    except Exception as e:
         logging.exception(f"Unexpected error writing output blob: {e}")
         return func.HttpResponse("An error occurred while writing the output file.", status_code=500)

    # --- 6. Return Success Response ---
    logging.info(f"Successfully processed and saved result to: {output_container}/{output_blob}")
    return func.HttpResponse(
        json.dumps({
            "message": "Successfully processed blob content with GPT.",
            "input_blob": f"{input_container}/{input_blob}",
            "output_blob": f"{output_container}/{output_blob}",
            "prompt_used": f"{prompt_name}.yaml"
        }),
        status_code=200,
        mimetype="application/json"
    )