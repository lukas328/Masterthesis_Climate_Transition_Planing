from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import logging
from azure.core.exceptions import AzureError

import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient
import logging
from azure.core.exceptions import AzureError

# Read CSV
from io import StringIO
import pandas as pd
import chardet

# Read YAML
import yaml
from azure.search.documents.models import VectorizableTextQuery, QueryType, QueryAnswerType, QueryCaptionType
from azure.search.documents import SearchClient
from openai import AzureOpenAI

try:

    credential = DefaultAzureCredential()
    #### IMPORTANT IF KEY VAULT IS CHANGED ADJUST URL ###
    key_vault_url = "https://kv-genai-playground.vault.azure.net/"
    client = SecretClient(vault_url=key_vault_url, credential=credential)
    API_KEY_AI_SEARCH = client.get_secret('ApiKeyAISearch').value
    ApiKeyAIStudio = client.get_secret('ApiKeyAIStudio').value
    STORAGE_CONNECTION_STRING = client.get_secret('storage-account-key').value
except Exception as e:
    logging.error(f"Failed to retrieve secrets: {e}")

STORAGE_ACCOUNT_NAME = "sagenaiplayground"
API_KEY_OPEN_AI = ApiKeyAIStudio
OPEN_AI_URL = "https://ai-models-genai-playground.openai.azure.com"
MODEL_NAME = "gpt-4o"
API_VERSION = "2024-08-01-preview"
SERVICE_NAME_AI_SEARCH = ""
AI_SEARCH_URL  =""
INDEX_NAME = ""

session = requests.Session()
retry_strategy = Retry(
    total=5,
    backoff_factor=0.3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount('http://', adapter)
session.mount('https://', adapter)


def call_gpt_api(
    messages,
    api_key = API_KEY_OPEN_AI,
    url = OPEN_AI_URL,
    model_name = MODEL_NAME,
    api_version =API_VERSION,
    temperature = 0.7,
    top_p= 0.95):
    """
    Calls the Azure OpenAI Chat Completion API.

    Parameters:
        messages (List[Dict[str, str]]): The message flow as a list of dictionaries with 'role' and 'content'.
        api_key (str): Azure OpenAI API key.
        endpoint (str): The base URL of your Azure OpenAI resource 
        deployment_name (str): The name of your model deployment in Azure OpenAI.
        api_version (str, optional): The API version to use. 
        temperature (float, optional): Sampling temperature. Defaults to 0.7.
        top_p (float, optional): Nucleus sampling probability. Defaults to 0.95.
        n (int, optional): Number of completions to generate. Defaults to 1.


    Returns:
    - A JSON object containing the response from the GPT API.
    """
    # Validate input parameters
    if not messages:
        raise ValueError("The 'messages' parameter must not be empty.")
    if not api_key:
        raise ValueError("The 'api_key' parameter must not be empty.")
    if not url:
        raise ValueError("The 'endpoint' parameter must not be empty.")

    # Initialize the client
    try:
        client = AzureOpenAI(
            azure_endpoint =url,
            api_key=api_key,
            api_version= api_version
        )
        logging.debug("OpenAI client initialized.")
    except Exception as e:
        logging.exception("Failed to initialize OpenAI client.")
        raise e
    # Prepare the request parameters
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            response_format={ "type": "json_object" },
           # temperature=temperature,
            #top_p=top_p,
        )
        logging.info("GPT API call successful.")
        #logging.info(f"repsonse = {response}")
        return response
    except Exception as e:
        logging.exception("Failed to call GPT API.")
        raise e


def initialize_search_client(ai_search_url = f"https://{SERVICE_NAME_AI_SEARCH}.search.windows.net",index_name = INDEX_NAME, ai_search_key = API_KEY_AI_SEARCH):

    logging.info("Initalize Search Client.")
    # Initialize the Azure Key Credential
    credential = AzureKeyCredential(ai_search_key)

    # Create the SearchClient instance
    search_client = SearchClient(endpoint=ai_search_url, index_name=index_name, credential=credential)

    return search_client


def call_ai_search(query, ai_search_url = AI_SEARCH_URL, ai_search_key = API_KEY_AI_SEARCH):
    """
    Calls the AI Search service with the provided query.

    Parameters:
    - query: A dictionary containing the search query.

    Returns:
    - The JSON response from the AI Search service.

    Raises:
    - AISearchError: If there is an error calling the AI Search service.
    """
    logging.info(f"Try to call ai search with url {ai_search_url}  and key {ai_search_key}")
    
    logging.debug("call_ai_search function called.")

    # Retrieve AI Search configuration from environment variables
    if not ai_search_url or not ai_search_key:
        raise ValueError("AI_SEARCH_URL or AI_SEARCH_KEY environment variable is not set.")

    ai_search_headers = {
        'Content-Type': 'application/json',
        'api-key': ai_search_key
    }

    response = session.post(ai_search_url, headers=ai_search_headers, json=query)
    logging.info(f"repsonse: {response}")
    response.raise_for_status()
    logging.debug("AI Search service call successful.")
    return response.json()


class BlobReadError(Exception):
    """Custom exception for blob reading errors."""
    pass

def read_csv_from_blob(container_name, blob_name, storage_account_name = STORAGE_ACCOUNT_NAME):
    """
    Reads a CSV file from Azure Blob Storage and returns its contents as a DataFrame.

    Parameters:
    - container_name: The name of the blob container.
    - blob_name: The name of the CSV file (blob) to read.

    Returns:
    - A pandas DataFrame containing the CSV data.

    Raises:
    - BlobReadError: If there is an error reading the blob.
    """
    try:
        logging.info(f"Attempting to read blob '{blob_name}' from container '{container_name}'.")

        # Retrieve the storage connection string from environment variables
        if not storage_account_name:
            raise ValueError("storage_account_name environment variable is not set.")

        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=credential
        )

        # Create a BlobServiceClient using the connection string
        #blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
        logging.info("Successfully created BlobServiceClient.")

        # Get the container client
        container_client = blob_service_client.get_container_client(container_name)
        logging.debug(f"Retrieved container client for container '{container_name}'.")

        # Get the blob client
        blob_client = container_client.get_blob_client(blob_name)
        logging.debug(f"Retrieved blob client for blob '{blob_name}'.")

        # Download the blob as bytes
        blob_bytes = blob_client.download_blob().readall()
        logging.debug(f"Downloaded blob '{blob_name}' successfully.")

        # Detect encoding
        detected_encoding = chardet.detect(blob_bytes)['encoding']
        if not detected_encoding:
            detected_encoding = 'utf-8'  # Default to 'utf-8' if encoding detection fails
            logging.warning(f"Encoding detection failed for blob '{blob_name}', defaulting to 'utf-8'.")

        logging.debug(f"Detected encoding for blob '{blob_name}': {detected_encoding}")

        # Decode bytes to string
        csv_data = blob_bytes.decode(detected_encoding)
        data_stream = StringIO(csv_data)

        # Load the CSV data into a pandas DataFrame
        df = pd.read_csv(data_stream)
        logging.info(f"Successfully loaded CSV data into DataFrame with {len(df)} rows from blob '{blob_name}'.")
        return df

    except (AzureError, Exception) as e:
        error_msg = f"Error reading CSV from blob '{blob_name}' in container '{container_name}': {e}"
        logging.error(error_msg)
        raise BlobReadError(error_msg)
    

def read_yaml_from_blob(container_name, blob_name, storage_account_name = STORAGE_ACCOUNT_NAME):

    """
    Reads a YAML file from Azure Blob Storage and returns its content as a Python dictionary.

    Parameters:
    - container_name: The name of the blob container.
    - blob_name: The name of the YAML file (blob) to read.

    Returns:
    - A Python dictionary containing the YAML data.

    Raises:
    - BlobReadError: If there is an error reading the blob.
    """
    try:
        logging.info(f"Attempting to read blob '{blob_name}' from container '{container_name}'.")

        # Retrieve the storage connection string from environment variables
        if not storage_account_name:
            raise ValueError("storage_account_name environment variable is not set.")

        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=credential
        )
        logging.debug("Successfully created BlobServiceClient.")

        # Get the container client
        container_client = blob_service_client.get_container_client(container_name)
        logging.debug(f"Retrieved container client for container '{container_name}'.")

        # Get the blob client
        blob_client = container_client.get_blob_client(blob_name)
        logging.debug(f"Retrieved blob client for blob '{blob_name}'.")

        # Download the blob as bytes
        blob_bytes = blob_client.download_blob().readall()
        logging.debug(f"Downloaded blob '{blob_name}' successfully.")

        # Detect encoding
        detected_encoding = chardet.detect(blob_bytes)['encoding']
        if not detected_encoding:
            detected_encoding = 'utf-8'
            logging.warning(f"Encoding detection failed for blob '{blob_name}', defaulting to 'utf-8'.")

        logging.debug(f"Detected encoding for blob '{blob_name}': {detected_encoding}")

        # Decode bytes to string
        yaml_data = blob_bytes.decode(detected_encoding)

        # Replace tabs with spaces to prevent YAML parsing errors
        if '\t' in yaml_data:
            logging.warning("Found tabs in YAML file, replacing with spaces.")
            yaml_data = yaml_data.replace('\t', '    ')

        # Load YAML data
        yaml_dict = yaml.safe_load(yaml_data)
        logging.info(f"Successfully loaded YAML data into dictionary from blob '{blob_name}'.")
        return yaml_dict

    except (AzureError, yaml.YAMLError, Exception) as e:
        error_msg = f"Error reading YAML from blob '{blob_name}' in container '{container_name}': {e}"
        logging.error(error_msg)
        raise BlobReadError(error_msg)
    

def save_data_to_blob(data, container_name, blob_name, storage_account_name = STORAGE_ACCOUNT_NAME):
    """
    Saves data to an Azure Blob Storage container.

    Parameters:
    - data: The data to be saved. This can be a string, bytes, or a file-like object.
    - container_name: The name of the blob container.
    - blob_name: The name of the blob where data will be saved.

    Returns:
    - None

    Raises:
    - Exception: If there is an error saving the data to the blob.
    """
    try:
        logging.info(f"Attempting to upload data to blob '{blob_name}' in container '{container_name}'.")

        if not storage_account_name:
            raise ValueError("storage_account_name environment variable is not set.")

        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=credential
        )
        logging.debug("Successfully created BlobServiceClient.")

        # Get the blob client
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        logging.debug(f"Retrieved blob client for blob '{blob_name}' in container '{container_name}'.")

        # Upload the data
        blob_client.upload_blob(data, overwrite=True)
        logging.info(f"Successfully uploaded data to blob '{blob_name}' in container '{container_name}'.")

    except Exception as e:
        error_msg = f"Error uploading data to blob '{blob_name}' in container '{container_name}': {e}"
        logging.error(error_msg)
        raise Exception(error_msg)