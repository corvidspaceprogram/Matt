import requests
import json
from bot_exceptions import NetworkError, FileOperationError, APIResponseError

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

def evaluate_response(text, opening_char, closing_char):
    accepted = False

    openings = text.count(opening_char)
    closings = text.count(closing_char)

    # Check the number of opening/closing characters - want exactly 1 of each
    if openings != 1 or closings != 1:
        print("LLM output failed evaluation! Needs exactly one " + opening_char + closing_char + " pair.")
        return accepted
    
    # Check length of substring between characters. Want more than half of total length
    start_index = text.find(opening_char)
    end_index = text.find(closing_char)
    sub_length = end_index - (start_index + 1)

    if sub_length < len(text)/2:
        print("LLM output failed evaluation! Text between " + opening_char + closing_char + " not long enough.")
        return accepted

    accepted = True

    return accepted