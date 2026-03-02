import requests
import json
from bot_exceptions import NetworkError, FileOperationError, APIResponseError
from retry_utils import retry_with_backoff
from validation_utils import validate_llm_response, validate_file_upload_response, validate_json_response

@retry_with_backoff()
def upload_file(url, api_key, file_path):
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json'
        }
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url + "v1/files/", headers=headers, files=files)
            response.raise_for_status()
            return response.json()
    except FileNotFoundError:
        raise FileOperationError(f"File not found: {file_path}")
    except PermissionError:
        raise FileOperationError(f"Permission denied accessing file: {file_path}")
    except requests.exceptions.Timeout:
        raise NetworkError(f"Upload timeout for file: {file_path}")
    except requests.exceptions.ConnectionError:
        raise NetworkError(f"Connection failed during file upload: {file_path}")
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"Upload failed for file {file_path}: {e}")
    except json.JSONDecodeError as e:
        raise APIResponseError(f"Invalid JSON response from upload API: {e}")
    except Exception as e:
        raise NetworkError(f"Unexpected error uploading file {file_path}: {e}")

@retry_with_backoff()
def chat_with_file(url, api_key, model, messages, file_id):
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': model,
            'messages': messages,
            'files': [{'type': 'file', 'id': file_id}]
        }
        print(payload)
        response = requests.post(url + "chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response
    except requests.exceptions.Timeout:
        raise NetworkError(f"LLM chat timeout with file {file_id}")
    except requests.exceptions.ConnectionError:
        raise NetworkError(f"Connection failed during LLM chat with file {file_id}")
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"LLM chat failed with file {file_id}: {e}")
    except Exception as e:
        raise NetworkError(f"Unexpected error in LLM chat with file {file_id}: {e}")

@retry_with_backoff()
def chat_with_model(url, api_key, model, messages):
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        data = {
          "model": model,
          "messages": messages
        }
        response = requests.post(url + "chat/completions", headers=headers, json=data)
        response.raise_for_status()
        return response
    except requests.exceptions.Timeout:
        raise NetworkError("LLM chat timeout")
    except requests.exceptions.ConnectionError:
        raise NetworkError("Connection failed during LLM chat")
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"LLM chat failed: {e}")
    except Exception as e:
        raise NetworkError(f"Unexpected error in LLM chat: {e}")

# Deletes all files called "file_name"
@retry_with_backoff()
def delete_files(url, api_key, file_name):
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json'
        }
        files_list = requests.get(url + 'v1/files/', headers=headers)
        files_list.raise_for_status()
        
        for file in files_list.json():
            if file['filename'] == file_name:
                delete_response = requests.delete(url + 'v1/files/' + file['id'], headers=headers)
                delete_response.raise_for_status()
                
    except requests.exceptions.Timeout:
        raise NetworkError(f"Timeout deleting files: {file_name}")
    except requests.exceptions.ConnectionError:
        raise NetworkError(f"Connection failed deleting files: {file_name}")
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"Failed to delete files {file_name}: {e}")
    except json.JSONDecodeError as e:
        raise APIResponseError(f"Invalid JSON response while deleting files: {e}")
    except Exception as e:
        raise NetworkError(f"Unexpected error deleting files {file_name}: {e}")

# Obtains id for first file with given name
@retry_with_backoff()
def get_file_id(url, api_key, file_name):
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json'
        }
        files_list = requests.get(url + 'v1/files/', headers=headers)
        files_list.raise_for_status()
        
        for file in files_list.json():
            if file['filename'] == file_name:
                return file['id']
                
    except requests.exceptions.Timeout:
        raise NetworkError(f"Timeout getting file ID for: {file_name}")
    except requests.exceptions.ConnectionError:
        raise NetworkError(f"Connection failed getting file ID for: {file_name}")
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"Failed to get file ID for {file_name}: {e}")
    except json.JSONDecodeError as e:
        raise APIResponseError(f"Invalid JSON response while getting file ID: {e}")
    except Exception as e:
        raise NetworkError(f"Unexpected error getting file ID for {file_name}: {e}")
            
    return None

def evaluate_response(text):
    """ 
    We're expecting the text to contain a JSON object in the format
    { 
        "post_content": "CONTENT"
    }

    To evaluate, we search for "{" then find the next "}". Then parse this
    using JSON library. 

    Any errors thrown during this (i.e. incorrect json format, no
    "post_context" name) should be caught outside this function. 

    """    
    start_index = text.find("{")
    end_index = text[start_index:].find("}") + start_index

    # sub_length = end_index - (start_index + 1)
    post_json = json.loads(text[start_index:end_index+1])

    post_content = post_json["post_content"]

    return post_content


def chat_with_model_validated(url, api_key, model, messages):
    response = chat_with_model(url, api_key, model, messages)
    response_json = validate_json_response(response.text, " in chat_with_model")
    return validate_llm_response(response_json)


def chat_with_file_validated(url, api_key, model, messages, file_id):
    response = chat_with_file(url, api_key, model, messages, file_id)
    response_json = validate_json_response(response.text, " in chat_with_file")
    return validate_llm_response(response_json)


def upload_file_validated(url, api_key, file_path):
    response = upload_file(url, api_key, file_path)
    return validate_file_upload_response(response, f" uploading {file_path}")