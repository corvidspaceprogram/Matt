import env_loader
import mastodon_client
import text_cleaner
import llm_manager
import validation_utils
import os
import sys
import json
import traceback
import time
from bot_exceptions import NetworkError, FileOperationError, APIResponseError, ConfigurationError, LLMError
from datetime import datetime

class LlmPoster():
    def __init__(self, mastodon_api):
        self.mastodon_api = mastodon_api

        # Load environment variables
        env_loader.load_environment_variables()

        # Admin account is optional
        try:
            self.admin_account = env_loader.get_env_variable("ADMIN_MASTODON_ACCOUNT")
        except ValueError:
            self.admin_account = None

        # Run mode is optional, defaults to dev
        try:
            self.run_mode = env_loader.get_env_variable("RUN_MODE")
        except ValueError:
            self.run_mode = "dev"

        # Character limit is optional, defaults to 500
        try:
            self.char_limit = int(env_loader.get_env_variable("DESTINATION_MASTODON_CHAR_LIMIT"))
        except ValueError:
            self.char_limit = 500

        try: 

            # Mandatory env variables
            self.context_limit = int(env_loader.get_env_variable("MAX_CONTEXT_LENGTH"))
            self.llm_api_url = env_loader.get_env_variable("LLM_API_URL")
            self.llm_api_key = env_loader.get_env_variable("LLM_API_KEY")
            self.llm_model = env_loader.get_env_variable("LLM_MODEL")
            self.system_prompt = env_loader.get_env_variable("SYSTEM_PROMPT")
            
        except (NetworkError, FileOperationError, APIResponseError, ConfigurationError, LLMError, ValueError) as e:
            self.handle_error()
            raise

    def prepare_context(self):
        if os.path.exists('posts.json'):
            # Refresh post history file
            mastodon_client.update_instance_posts(\
                self.mastodon_api, self.context_limit, \
                text_cleaner.clean_content)
        else: 
            # Create posts.json file
            mastodon_client.store_instance_posts(\
                self.mastodon_api, self.context_limit, \
                text_cleaner.clean_content)
        
        mastodon_client.truncate_post_file(self.context_limit, \
            self.system_prompt)

        mastodon_client.convert_instance_posts_txt()

        file_upload_response = llm_manager.upload_file(\
            self.llm_api_url, self.llm_api_key, 'posts_tmp.txt')
        file_id = file_upload_response['id']

        return file_id

    def llm_chat(self, messages, file_id=None):
        response_accepted = False
            
        while not response_accepted:

            if file_id is not None:
                content = llm_manager.chat_with_file_validated(
                    self.llm_api_url, self.llm_api_key, self.llm_model, messages, file_id)
            else:
                content = llm_manager.chat_with_model_validated(
                    self.llm_api_url, self.llm_api_key, self.llm_model, messages)

            if self.run_mode == "dev": 
                print(content, flush=True)

            try: 
                generated_text = llm_manager.evaluate_response(content)

                response_accepted = True
            except (json.JSONDecodeError, KeyError, ValueError):
                if self.run_mode == "dev": 
                    print("Response does not contain valid post format: \n\n" + content + "\n", flush=True)
                continue

            if self.run_mode == "dev":
                print(content, flush=True)

        return generated_text

    def respond_to_mention(self, mention):

        # Prepare context (posts_tmp.txt)
        file_id = self.prepare_context()

        time.sleep(5)

        st = mention['status']
        message_history = mastodon_client.fetch_context(self.mastodon_api, st)
        user = st['account']['username']

        messages = [{"role": "system", "content": self.system_prompt}]

        # Include a blank message from the user if first post in chain is by assistant. Avoids 400 error for malformed request.
        if message_history[0]["role"] == "assistant":
            messages += [{"role": "user", "content": "Write a message for the platform, picking one topic from the attached context."}]

        messages += message_history

        # query += "\n- your post must be in response to the following" + \
        #     " conversation: \n\n "
        # query += context

        if self.run_mode == "dev": print(messages, flush=True)

        generated_text = self.llm_chat(messages, file_id)

        if self.run_mode == "prod":
            mastodon_client.post_reply(self.mastodon_api, generated_text, self.char_limit, st)
        elif self.run_mode == "dev":
            print(generated_text, flush=True)

            if self.admin_account is not None:
                mastodon_client.post_dm(self.mastodon_api, \
                    generated_text, self.char_limit, self.admin_account)

    def handle_error(self, context=""):
        """
        Handle errors with enhanced error messages and logging.
        
        Args:
            context: Optional context string describing where error occurred
        """
        error = sys.exc_info()[1]
        error_type = type(error).__name__
        timestamp = datetime.now().isoformat()
        
        # Build error message
        context_str = f" in {context}" if context else ""
        error_msg = f"[{error_type}]{context_str}: {str(error)}"
        
        # Full log entry with timestamp
        full_msg = traceback.format_exc()
        log_entry = f"{timestamp} - {error_type}{context_str}: {str(error)}\n{full_msg}\n"
        
        if self.run_mode == "dev":
            print(" > ERROR:", flush=True)
            print(error_msg, flush=True)
            print(full_msg, flush=True)

        # Log to file with timestamp
        with open('errorlog.txt', "a") as f:
            f.write(log_entry)

        # DM admin account with cleaner error message
        if self.admin_account is not None:
            admin_msg = f"Error: {error_type}{context_str}\n{str(error)[:200]}"
            try:
                mastodon_client.post_dm(self.mastodon_api, \
                    admin_msg, self.char_limit, \
                    self.admin_account)
            except:
                pass  # Don't fail if admin notification fails