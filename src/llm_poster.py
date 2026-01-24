import env_loader
import mastodon_client
import text_cleaner
import llm_manager
import os
import traceback
import time

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
            self.system_prompt)

        mastodon_client.convert_instance_posts_txt()

        # Delete previous posts_tmp.txt from server
        llm_manager.delete_files(self.llm_api_url, \
            self.llm_api_key, 'posts_tmp.txt')

        file_upload_response = llm_manager.upload_file(\
            self.llm_api_url, self.llm_api_key, 'posts_tmp.txt')
        file_id = file_upload_response['id']

        return file_id

    def llm_chat(self, messages, file_id=None):
        response_accepted = False
            
        while not response_accepted:

            if file_id is not None:
                llm_response = llm_manager.chat_with_file(self.llm_api_url,\
                    self.llm_api_key, self.llm_model, messages, file_id)
            else:
                llm_response = llm_manager.chat_with_model(self.llm_api_url,\
                    self.llm_api_key, self.llm_model, messages)

            if self.run_mode == "dev": print(llm_response)

            response_json = llm_response.json()
            if self.run_mode == "dev":
                print(response_json)

            response_accepted = llm_manager.evaluate_response(response_json['choices'][0]['message']['content'], "¥", "√")

            if self.run_mode == "dev":
                print(response_json['choices'][0]['message']['content'])

        generated_text = text_cleaner.remove_delimiters(\
            response_json['choices'][0]['message']['content'], "¥", "√")

        return generated_text

    def respond_to_mention(self, mention):

        file_id = llm_manager.get_file_id(self.llm_api_url, self.llm_api_key, "posts_summary.txt")

        while file_id is None:
            print("No post summary found. Trying again in 30 seconds.")
            time.sleep(30)
            file_id = llm_manager.get_file_id(self.llm_api_url, self.llm_api_key, "posts_summary.txt")

        time.sleep(5)

        st = mention['status']
        message_history = mastodon_client.fetch_context(self.mastodon_api, st)
        user = st['account']['username']

        messages = [{"role": "system", "content": self.system_prompt}]
        messages += message_history

        # query += "\n- your post must be in response to the following" + \
        #     " conversation: \n\n "
        # query += context

        if self.run_mode == "dev": print(messages)

        generated_text = self.llm_chat(messages, file_id)

        if self.run_mode == "prod":
            mastodon_client.post_reply(self.mastodon_api, generated_text, self.char_limit, st)
        elif self.run_mode == "dev":
            print(generated_text)

            if self.admin_account is not None:
                mastodon_client.post_dm(self.mastodon_api, \
                    generated_text, self.char_limit, self.admin_account)

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