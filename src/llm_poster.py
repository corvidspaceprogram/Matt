import env_loader
import mastodon_client
import text_cleaner
import llm_manager
import os
import traceback

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
            self.llm_prompt = env_loader.get_env_variable("LLM_PROMPT")
            
        except:
            self.handle_error()

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
            self.llm_prompt)

        mastodon_client.convert_instance_posts_txt()

        # Delete previous posts_tmp.txt from server
        llm_manager.delete_files(self.llm_api_url, \
            self.llm_api_key, 'posts_tmp.txt')

        file_upload_response = llm_manager.upload_file(\
            self.llm_api_url, self.llm_api_key, 'posts_tmp.txt')
        file_id = file_upload_response['id']

        return file_id

    def llm_chat(self, file_id, prompt):
        response_accepted = False
            
        while not response_accepted:

            llm_response = llm_manager.chat_with_file(self.llm_api_url,\
                self.llm_api_key, self.llm_model, prompt, file_id)

            if self.run_mode == "dev": print(llm_response)

            response_json = llm_response.json()

            response_accepted = llm_manager.evaluate_response(response_json['choices'][0]['message']['content'], "¥", "√")

            if self.run_mode == "dev":
                print(response_json['choices'][0]['message']['content'])

        generated_text = text_cleaner.remove_delimiters(\
            response_json['choices'][0]['message']['content'], "¥", "√")

        return generated_text

    def handle_error(self):
        msg = traceback.format_exc()
        if self.run_mode == "dev":
            print(" > ERROR:")
            print(msg)

        with open('errorlog.txt', "a") as f:
            f.write(msg)

        # DM admin account that something went wrong.
        if self.admin_account is not None:
            mastodon_client.post_dm(self.mastodon_api, \
                "Something went wrong: " + msg, self.char_limit, \
                self.admin_account)