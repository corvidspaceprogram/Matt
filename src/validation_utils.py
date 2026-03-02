"""
API Response validation utilities.

This module provides functions to validate API responses before accessing
nested data, helping prevent runtime errors from malformed responses.
"""

import json
from bot_exceptions import APIResponseError


def validate_json_response(response_text, context=""):
    """
    Validate that response text is valid JSON.
    
    Args:
        response_text: The text to parse as JSON
        context: Optional context string for error messages
    
    Returns:
        Parsed JSON object
    
    Raises:
        APIResponseError: If JSON is invalid
    """
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        raise APIResponseError(f"Invalid JSON response{context}: {e}")


def validate_response_keys(response_json, required_keys, context=""):
    """
    Validate that response JSON contains required keys.
    
    Args:
        response_json: Parsed JSON response
        required_keys: List of required key names
        context: Optional context string for error messages
    
    Returns:
        True if valid
    
    Raises:
        APIResponseError: If any required keys are missing
    """
    if not isinstance(response_json, dict):
        raise APIResponseError(f"Response is not a JSON object{context}")
    
    missing_keys = [key for key in required_keys if key not in response_json]
    
    if missing_keys:
        raise APIResponseError(
            f"Missing required keys in response{context}: {', '.join(missing_keys)}"
        )
    
    return True


def validate_llm_response(response_json, context=""):
    """
    Validate LLM API chat completion response.
    
    Args:
        response_json: Parsed JSON response from LLM API
        context: Optional context string for error messages
    
    Returns:
        The content string from the response
    
    Raises:
        APIResponseError: If response is malformed
    """
    validate_response_keys(response_json, ['choices'], context)
    
    choices = response_json['choices']
    if not choices or len(choices) == 0:
        raise APIResponseError(f"LLM response has no choices{context}")
    
    validate_response_keys(choices[0], ['message'], context)
    
    message = choices[0]['message']
    validate_response_keys(message, ['content'], context)
    
    return message['content']


def validate_file_upload_response(response_json, context=""):
    """
    Validate file upload API response.
    
    Args:
        response_json: Parsed JSON response from file upload API
        context: Optional context string for error messages
    
    Returns:
        The file ID from the response
    
    Raises:
        APIResponseError: If response is malformed
    """
    validate_response_keys(response_json, ['id'], context)
    
    return response_json['id']


def validate_list_files_response(response_json, context=""):
    """
    Validate list files API response.
    
    Args:
        response_json: Parsed JSON response from files list API
        context: Optional context string for error messages
    
    Returns:
        The files list from the response
    
    Raises:
        APIResponseError: If response is malformed
    """
    if not isinstance(response_json, list):
        raise APIResponseError(f"Expected file list but got {type(response_json).__name__}{context}")
    
    return response_json


def safe_get(data, key_path, default=None):
    """
    Safely get nested data from dictionary without raising KeyError.
    
    Args:
        data: Dictionary to search
        key_path: Dot-separated path (e.g., 'choices.0.message.content')
        default: Default value if key not found
    
    Returns:
        The found value or default
    """
    keys = key_path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        elif isinstance(current, list):
            try:
                index = int(key)
                current = current[index] if index < len(current) else default
            except (ValueError, IndexError):
                return default
        else:
            return default
        
        if current is default:
            return default
    
    return current
