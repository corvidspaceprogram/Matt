import requests
import json
from logger import logger
from bot_exceptions import NetworkError, APIResponseError
from retry_utils import retry_with_backoff
from validation_utils import validate_llm_response, validate_json_response



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


