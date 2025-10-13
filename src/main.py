import warning_manager
import env_loader
import mastodon_client
import text_cleaner
import llm_manager
import post_manager
import refresh_schedule
import reply_manager
import os
from datetime import datetime
import threading

# Ignore warnings
warning_manager.ignore_future_warnings()

# Load environment variables
env_loader.load_environment_variables()

# Source Mastodon API - can't change this, as we do need an account to interact with the API
mastodon_base_url = env_loader.get_env_variable("MASTODON_BASE_URL", "Enter your Mastodon base URL: ")
mastodon_access_token = env_loader.get_env_variable("MASTODON_ACCESS_TOKEN", "Enter your Mastodon access token: ")
mastodon_api = mastodon_client.init_mastodon(mastodon_base_url, mastodon_access_token)

char_limit = int(env_loader.get_env_variable("DESTINATION_MASTODON_CHAR_LIMIT", "Enter the Mastodon post character limit: "))

context_limit = int(env_loader.get_env_variable("MAX_CONTEXT_LENGTH", "Enter the maximum character length for context file: "))
llm_api_url = env_loader.get_env_variable("LLM_API_URL", "Enter your LLM API URL: ")
#llm_jwt_token = env_loader.get_env_variable("LLM_JWT_TOKEN", "Enter your LLM's JWT token: ")
llm_api_key = env_loader.get_env_variable("LLM_API_KEY", "Enter your LLM's API key: ")
llm_model = env_loader.get_env_variable("LLM_MODEL", "Enter your desired chat completion model: ")
llm_prompt = env_loader.get_env_variable("LLM_PROMPT", "Enter your desired prompt to provide the LLM: ")


#n = threading.Thread(target=mastodon_api.stream_user, args=(reply_manager.Stream(mastodon_api, llm_api_url, llm_api_key, llm_model, context_limit)))

r = threading.Thread(target=post_manager.random_post_schedule_loop, args=(mastodon_api, context_limit, llm_api_url, llm_api_key, llm_model, llm_prompt, char_limit))

#n.start()
r.start()

mastodon_api.stream_user(reply_manager.Stream(mastodon_api, llm_api_url, llm_api_key, llm_model, context_limit)) #Launch stream

# TODO - move updating context file and updating file into a separate script file, so it can be called on notification as well. 



# except KeyboardInterrupt:
#     print("\nExiting...")

