from dotenv import load_dotenv
import os
from bot_exceptions import FileOperationError, ConfigurationError

def load_environment_variables():
    try:
        load_dotenv()
    except FileNotFoundError:
        raise FileOperationError(".env file not found. Please create one with required environment variables.")
    except Exception as e:
        raise FileOperationError(f"Failed to load environment variables: {e}")

def get_env_variable(key, prompt_message=None):
    value = os.getenv(key)
    if not value and prompt_message:
        try:
            value = input(prompt_message)
            save_env_variable(key, value)
        except (EOFError, KeyboardInterrupt):
            raise ConfigurationError(f"User input cancelled for environment variable: {key}")
    elif not value and not prompt_message:
        raise ConfigurationError("Value not defined for .env variable " + key)
    return value

def save_env_variable(key, value):
    try:
        with open('.env', 'a') as env_file:
            env_file.write(f"\n{key}={value}")
    except PermissionError:
        raise FileOperationError(f"Permission denied writing to .env file for variable: {key}")
    except OSError as e:
        raise FileOperationError(f"Failed to write to .env file for variable {key}: {e}")
    except Exception as e:
        raise FileOperationError(f"Unexpected error writing .env file for variable {key}: {e}")