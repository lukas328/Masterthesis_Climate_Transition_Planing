import logging
import json
import os
import pathlib
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential


from helper_functions.utilites import call_gpt_api, read_yaml_from_blob, save_data_to_blob, STORAGE_ACCOUNT_NAME, API_KEY_OPEN_AI, OPEN_AI_URL, MODEL_NAME, API_VERSION

STORAGE_ACCOUNT_NAME = os.environ.get("StorageAccountName")
API_KEY_OPEN_AI = os.environ.get("OpenAIApiKey")
OPEN_AI_URL = os.environ.get("OpenAIUrl")
MODEL_NAME = "gpt-4o"
API_VERSION = "2024-08-01-preview"



PROMPT_FILE_PATH = pathlib.Path(__file__).parent.parent / "prompts_transitionsplaning" / "writing_transitionplan_txt.txt"

def read_blob_content_str(container_name: str, blob_name: str, storage_account_name: str = STORAGE_ACCOUNT_NAME) -> str:
    """
    Reads content of a text blob from Azure Blob Storage.
    """
    try:
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=credential
        )
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        downloader = blob_client.download_blob(max_concurrency=1, encoding='UTF-8')
        blob_text = downloader.readall()
        return blob_text
    except Exception as e:
        logging.error(f"Failed to read blob {container_name}/{blob_name}: {e}")
        raise

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function `azfunc_writing_transition_plan` started processing a request.')

    try:
        req_body = req.get_json()
    except ValueError:
        logging.error("Request body is not valid JSON.")
        return func.HttpResponse("Please pass a valid JSON request body", status_code=400)

    input_container_co_profile = req_body.get('input_container_company_profile')
    input_blob_co_profile = req_body.get('input_blob_company_profile')
    input_container_portfolio = req_body.get('input_container_portfolio_analyses')
    input_blob_portfolio = req_body.get('input_blob_portfolio_analyses')
    input_container_action_plan = req_body.get('input_container_action_plan')
    input_blob_action_plan = req_body.get('input_blob_action_plan')
    output_container = req_body.get('output_container')
    output_blob_transition_plan = req_body.get('output_blob_transition_plan')

    if not all([input_container_co_profile, input_blob_co_profile,
                  input_container_portfolio, input_blob_portfolio,
                  input_container_action_plan, input_blob_action_plan,
                  output_container, output_blob_transition_plan]):
        return func.HttpResponse(
             "Missing required JSON parameters. Please include all input containers/blobs for company profile, portfolio analyses, action plan, and output container/blob for the transition plan.",
             status_code=400)

    try:
        company_profile_content = read_blob_content_str(input_container_co_profile, input_blob_co_profile)
        portfolio_analyses_content = read_blob_content_str(input_container_portfolio, input_blob_portfolio)
        action_plan_content = read_blob_content_str(input_container_action_plan, input_blob_action_plan)

        with open(PROMPT_FILE_PATH, 'r', encoding='utf-8') as f:
            writing_plan_prompt_template = f.read()
        
        
        combined_input_context = f"Company Profile:\n{company_profile_content}\n\nPortfolio Analysis:\n{portfolio_analyses_content}"
        
        # Construct messages for OpenAI API
        messages = [
            {"role": "system", "content": "You are an expert assistant helping to draft ESG transition plans for financial institutions."},
            {"role": "user", "content": f"Context:\n{combined_input_context}\n\nIdentified Actions:\n{action_plan_content}\n\nTask:\n{writing_plan_prompt_template}"}
        ]
        
        logging.info(f"Sending request to OpenAI API. Model: {MODEL_NAME}")
        gpt_response = call_gpt_api(
            messages=messages,
            api_key=API_KEY_OPEN_AI,
            url=OPEN_AI_URL,
            model_name=MODEL_NAME,
            api_version=API_VERSION
        )
        
        transition_plan_text = gpt_response.choices[0].message.content.strip()
        
        save_data_to_blob(
            data=transition_plan_text,
            container_name=output_container,
            blob_name=output_blob_transition_plan,
            storage_account_name=STORAGE_ACCOUNT_NAME
        )

        return func.HttpResponse(
            json.dumps({
                "message": "Successfully generated transition plan section.",
                "output_blob": f"{output_container}/{output_blob_transition_plan}"
            }),
            status_code=200,
            mimetype="application/json"
        )

    except FileNotFoundError:
        logging.error(f"Prompt file not found at {PROMPT_FILE_PATH}")
        return func.HttpResponse("Writing transition plan prompt file not found.", status_code=500)
    except NotImplementedError as nie:
        logging.error(f"A required helper function is not implemented: {nie}")
        return func.HttpResponse("Internal configuration error: helper function missing.", status_code=500)
    except Exception as e:
        logging.error(f"Error in `azfunc_writing_transition_plan`: {e}")
        return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)