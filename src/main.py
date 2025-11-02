from mastodon import StreamListener
from llm_poster import LlmPoster
import warning_manager
import env_loader
import mastodon_client
import refresh_schedule
import os
from datetime import datetime
import threading

# Class for responding to mentions
class Stream(StreamListener, LlmPoster):
    def __init__(self, mastodon_api): #Inheritance
        LlmPoster.__init__(self, mastodon_api)
        StreamListener.__init__(self)

        if self.run_mode == "dev": print("Initializing notification listener")

    def on_notification(self,notif): #Called when a notification comes
        if notif['type'] == 'mention': #Check if the content of the notification is a mention

            try:
                st = notif['status']
                context = mastodon_client.fetch_context(self.mastodon_api, st)
                user = st['account']['username']

                query = self.llm_prompt
                query += "\n- your post must be in response to the following" + \
                    " conversation: \n\n "
                query += context

                if self.run_mode == "dev": print(query)

                file_id = self.prepare_context()

                generated_text = self.llm_chat(file_id, query)

                if self.run_mode == "prod":
                    mastodon_client.post_reply(self.mastodon_api, generated_text, self.char_limit, st)
                elif self.run_mode == "dev":
                    print(generated_text)
                    if self.admin_account is not None:
                        mastodon_client.post_dm(self.mastodon_api, \
                            generated_text, self.char_limit, self.admin_account)
            except:
                self.handle_error()

# Class for random posts
class RandomLlmPoster(LlmPoster):
    def __init__(self, mastodon_api):
        LlmPoster.__init__(self, mastodon_api)

    def start_loop(self):
        if self.run_mode == "dev": print("Starting random post schedule loop.")

        while True:
            """
            Raise errors within any function that could fail i.e. interacting 
            with internet - LLM calls and mastodon API stuff.

            Handle these errors in the try/catch block here.
            """
            try:
                current_time = datetime.now()
                refresh_interval = refresh_schedule.calculate_refresh_interval()
                next_refresh = refresh_schedule.calculate_next_refresh(\
                    current_time, refresh_interval)

                file_id = self.prepare_context()

                generated_text = self.llm_chat(file_id, self.llm_prompt)

                if self.run_mode == "prod":
                    mastodon_client.post_public(self.mastodon_api, generated_text,\
                        self.char_limit)
                elif self.run_mode == "dev":
                    print(generated_text)
                    if self.admin_account is not None:
                        mastodon_client.post_dm(self.mastodon_api, \
                            generated_text, self.char_limit, self.admin_account)

            except:
                self.handle_error()

            # Sleep until next refresh
            refresh_schedule.sleep_until_next_refresh(next_refresh)

# Ignore warnings
warning_manager.ignore_future_warnings()

# Load environment variables
env_loader.load_environment_variables()

# Source Mastodon API - can't change this, as we do need an account to interact with the API
mastodon_base_url = env_loader.get_env_variable("MASTODON_BASE_URL", "Enter your Mastodon base URL: ")
mastodon_access_token = env_loader.get_env_variable("MASTODON_ACCESS_TOKEN", "Enter your Mastodon access token: ")
mastodon_api = mastodon_client.init_mastodon(mastodon_base_url, mastodon_access_token)

rlp = RandomLlmPoster(mastodon_api)


r = threading.Thread(target=rlp.start_loop)

r.start()

mastodon_api.stream_user(Stream(mastodon_api)) #Launch stream

# TODO - move updating context file and updating file into a separate script file, so it can be called on notification as well. 



# except KeyboardInterrupt:
#     print("\nExiting...")

