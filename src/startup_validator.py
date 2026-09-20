"""
Startup configuration validation.

This module validates all required environment variables and configuration
at startup, failing fast with clear error messages if something is misconfigured.
"""

import os
from logger import logger
from bot_exceptions import ConfigurationError


def get_required_env_vars():
    """
    Return list of required environment variable names.
    
    Returns:
        List of required environment variable names
    """
    return [
        'MASTODON_BASE_URL',
        'MASTODON_ACCESS_TOKEN',
        'LLM_API_URL',
        'LLM_API_KEY',
        'LLM_MODEL',
        'SYSTEM_PROMPT',
        'POSTS_CONTEXT_LENGTH',
    ]


def get_optional_env_vars():
    """
    Return list of optional environment variable names with defaults.
    
    Returns:
        Dictionary of optional env vars and their defaults
    """
    return {
        'DESTINATION_MASTODON_CHAR_LIMIT': '500',
        'ADMIN_MASTODON_ACCOUNT': None,
        'RUN_MODE': 'dev',
        'MAX_RETRIES': '3',
        'RETRY_INITIAL_DELAY': '1',
        'RETRY_MAX_DELAY': '60',
    }


def validate_required_variables():
    """
    Validate all required environment variables are set.
    
    Raises:
        ConfigurationError: If any required variables are missing or invalid
    """
    errors = []
    
    for var_name in get_required_env_vars():
        value = os.getenv(var_name)
        
        if not value:
            errors.append(f"Missing required environment variable: {var_name}")
            logger.warning(f"[Validator] Missing required environment variable: {var_name}")
            continue
        
        # Validate numeric values
        if var_name == 'POSTS_CONTEXT_LENGTH':
            try:
                int_value = int(value)
                if int_value <= 0:
                    errors.append(f"{var_name} must be a positive integer, got: {value}")
            except ValueError:
                errors.append(f"{var_name} must be a valid integer, got: {value}")
    
    if errors:
        raise ConfigurationError(
            f"Configuration validation failed: {'; '.join(errors)}"
        )


def validate_optional_variables():
    """
    Validate optional environment variables have valid values.
    
    Raises:
        ConfigurationError: If any optional variables have invalid values
    """
    errors = []
    
    # Validate numeric optional variables
    numeric_vars = {
        'DESTINATION_MASTODON_CHAR_LIMIT': ('positive', 1),
        'MAX_RETRIES': ('non-negative', 0),
        'RETRY_INITIAL_DELAY': ('positive', 0),
        'RETRY_MAX_DELAY': ('positive', 0),
    }
    
    for var_name, (validation_type, min_val) in numeric_vars.items():
        value = os.getenv(var_name)
        if value:
            try:
                int_value = int(value)
                if validation_type == 'positive' and int_value <= min_val:
                    errors.append(f"{var_name} must be greater than {min_val}, got: {value}")
                elif validation_type == 'non-negative' and int_value < min_val:
                    errors.append(f"{var_name} must be at least {min_val}, got: {value}")
            except ValueError:
                errors.append(f"{var_name} must be a valid integer, got: {value}")
    
    # Validate RUN_MODE
    run_mode = os.getenv('RUN_MODE')
    if run_mode and run_mode not in ['dev', 'prod']:
        errors.append(f"RUN_MODE must be 'dev' or 'prod', got: {run_mode}")
    
    if errors:
        raise ConfigurationError(
            f"Optional configuration validation failed: {'; '.join(errors)}"
        )


def validate_all():
    """
    Validate all configuration at startup.
    
    This is the main entry point for startup validation.
    Call this early in main.py before starting any other operations.
    
    Raises:
        ConfigurationError: If any configuration is invalid
    """
    validate_required_variables()
    validate_optional_variables()


def print_configuration():
    """
    Print current configuration (with sensitive values redacted).
    Useful for debugging.
    """
    logger.info("[Validator] Configuration (debug info):")
    print("Current Configuration:")
    print("-" * 40)
    
    # Required variables
    for var_name in get_required_env_vars():
        value = os.getenv(var_name, '(not set)')
        if var_name in ['MASTODON_ACCESS_TOKEN', 'LLM_API_KEY']:
            value = value[:10] + '...' if len(value) > 10 else '***'
        print(f"  {var_name}: {value}")
    
    # Optional variables
    print("\nOptional Variables:")
    for var_name, default in get_optional_env_vars().items():
        value = os.getenv(var_name, default)
        print(f"  {var_name}: {value}")
    
    print("-" * 40)
