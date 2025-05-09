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


PROMPT_FILE_PATH = pathlib.Path(__file__).parent.parent / "prompts_transitionsplaning" / "action_planing_txt.txt"

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
    logging.info('Python HTTP trigger function `azfunc_action_planning` started processing a request.')

    try:
        req_body = req.get_json()
    except ValueError:
        logging.error("Request body is not valid JSON.")
        return func.HttpResponse("Please pass a valid JSON request body", status_code=400)

    input_container_co_profile = req_body.get('input_container_company_profile')
    input_blob_co_profile = req_body.get('input_blob_company_profile')
    input_container_portfolio = req_body.get('input_container_portfolio_analyses')
    input_blob_portfolio = req_body.get('input_blob_portfolio_analyses')
    output_container = req_body.get('output_container')
    output_blob_action_plan = req_body.get('output_blob_action_plan')

    if not all([input_container_co_profile, input_blob_co_profile, 
                  input_container_portfolio, input_blob_portfolio,
                  output_container, output_blob_action_plan]):
        return func.HttpResponse(
             "Missing required JSON parameters. Please include: input_container_company_profile, input_blob_company_profile, input_container_portfolio_analyses, input_blob_portfolio_analyses, output_container, output_blob_action_plan",
             status_code=400)

    try:
        company_profile_content = read_blob_content_str(input_container_co_profile, input_blob_co_profile)
        portfolio_analyses_content = read_blob_content_str(input_container_portfolio, input_blob_portfolio)

        with open(PROMPT_FILE_PATH, 'r', encoding='utf-8') as f:
            action_planning_prompt_template = f.read()

        # Combine inputs with the prompt template
        # The prompt asks "Based on this context", so we provide the context
        combined_input_context = f"Company Profile:\n{company_profile_content}\n\nPortfolio Analysis:\n{portfolio_analyses_content}"
        
        # Construct messages for OpenAI API
        messages = [
            {"role": "system", "content": "You are an expert assistant helping to generate ESG transition action plans for financial institutions."},
            {"role": "user", "content": f"Context:\n{combined_input_context}\n\nTask:\n{action_planning_prompt_template}"}
        ]
        
        logging.info(f"Sending request to OpenAI API. Model: {MODEL_NAME}")
        gpt_response = call_gpt_api(
            messages=messages,
            api_key=API_KEY_OPEN_AI,
            url=OPEN_AI_URL,
            model_name=MODEL_NAME,
            api_version=API_VERSION
        )

        action_plan_text = gpt_response.choices[0].message.content.strip()
        
        save_data_to_blob(
            data=action_plan_text,
            container_name=output_container,
            blob_name=output_blob_action_plan,
            storage_account_name=STORAGE_ACCOUNT_NAME
        )

        return func.HttpResponse(
            json.dumps({
                "message": "Successfully generated action plan.",
                "output_blob": f"{output_container}/{output_blob_action_plan}"
            }),
            status_code=200,
            mimetype="application/json"
        )

    except FileNotFoundError:
        logging.error(f"Prompt file not found at {PROMPT_FILE_PATH}")
        return func.HttpResponse("Action planning prompt file not found.", status_code=500)
    except NotImplementedError as nie:
        logging.error(f"A required helper function is not implemented: {nie}")
        return func.HttpResponse("Internal configuration error: helper function missing.", status_code=500)
    except Exception as e:
        logging.error(f"Error in `azfunc_action_planning`: {e}")
        return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)