from dotenv import load_dotenv
import os
from logger import logger
from bot_exceptions import FileOperationError, ConfigurationError

def load_environment_variables():
    try:
        load_dotenv()
        logger.info("[EnvLoader] Environment variables loaded successfully")
    except FileNotFoundError:
        logger.warning("[EnvLoader] .env file not found. Please create one with required environment variables.")
        raise FileOperationError(".env file not found. Please create one with required environment variables.")
    except Exception as e:
        logger.warning(f"[EnvLoader] Failed to load environment variables: {e}")
        raise FileOperationError(f"Failed to load environment variables: {e}")

def get_env_variable(key, prompt_message=None):
    value = os.getenv(key)
    if not value and prompt_message:
        try:
            value = input(prompt_message)
            save_env_variable(key, value)
            logger.info(f"[EnvLoader] Environment variable {key} set to: {value[:20]}...")
        except (EOFError, KeyboardInterrupt):
            logger.warning(f"[EnvLoader] User input cancelled for environment variable: {key}")
            raise ConfigurationError(f"User input cancelled for environment variable: {key}")
    elif not value and not prompt_message:
        logger.warning(f"[EnvLoader] Value not defined for .env variable {key}")
        raise ConfigurationError("Value not defined for .env variable " + key)
    return value

def save_env_variable(key, value):
    try:
        with open('.env', 'a') as env_file:
            env_file.write(f"\n{key}={value}")
            logger.debug(f"[EnvLoader] Saved {key} to .env file")
    except PermissionError:
        logger.warning(f"[EnvLoader] Permission denied writing to .env file for variable: {key}")
        raise FileOperationError(f"Permission denied writing to .env file for variable: {key}")
    except OSError as e:
        logger.warning(f"[EnvLoader] Failed to write to .env file for variable {key}: {e}")
        raise FileOperationError(f"Failed to write to .env file for variable {key}: {e}")
    except Exception as e:
        logger.warning(f"[EnvLoader] Unexpected error writing .env file for variable {key}: {e}")
        raise FileOperationError(f"Unexpected error writing .env file for variable {key}: {e}")