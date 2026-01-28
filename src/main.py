from mastodon import StreamListener
from llm_poster import LlmPoster
import llm_manager
import warning_manager
import env_loader
import mastodon_client
import refresh_schedule
import os
from datetime import datetime
import threading
import time
from bot_exceptions import NetworkError, FileOperationError, APIResponseError, ConfigurationError, LLMError

# Class for responding to mentions
class Stream(StreamListener, LlmPoster):
    def __init__(self, mastodon_api): #Inheritance
        LlmPoster.__init__(self, mastodon_api)
        StreamListener.__init__(self)

        if self.run_mode == "dev": print("Initializing notification listener")

    def on_notification(self,notif): #Called when a notification comes
        if notif['type'] == 'mention': #Check if the content of the notification is a mention

            try:
                self.respond_to_mention(notif)

            except (NetworkError, FileOperationError, APIResponseError, ConfigurationError, LLMError) as e:
                self.handle_error()
            except KeyboardInterrupt:
                print("\nShutting down gracefully...")
                raise

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

                file_id = llm_manager.get_file_id(self.llm_api_url, self.llm_api_key, "posts_summary.txt")

                while file_id is None:
                    print("No post summary found. Trying again in 30 seconds.")
                    time.sleep(30)
                    file_id = llm_manager.get_file_id(self.llm_api_url, self.llm_api_key, "posts_summary.txt")

                # This is necessary to allow the text embedding model enough time to load before the embeddings are needed. 
                time.sleep(5)

                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": "Write a message for the platform, picking a topic from the attached context."}
                ]

                generated_text = self.llm_chat(messages, file_id=file_id)

                if self.run_mode == "prod":
                    mastodon_client.post_public(self.mastodon_api, generated_text,\
                        self.char_limit)
                elif self.run_mode == "dev":
                    print(generated_text)
                    if self.admin_account is not None:
                        mastodon_client.post_dm(self.mastodon_api, \
                            generated_text, self.char_limit, self.admin_account)

            except (NetworkError, FileOperationError, APIResponseError, ConfigurationError, LLMError) as e:
                self.handle_error()
            except KeyboardInterrupt:
                print("\nShutting down gracefully...")
                raise

            # Sleep until next refresh
            refresh_schedule.sleep_until_next_refresh(next_refresh)

class PostsSummaryRefresher(LlmPoster):
    def __init__(self, mastodon_api):
        LlmPoster.__init__(self, mastodon_api)
        self.llm_model = 'google/gemma-3-1b'

    def start_loop(self):
        if self.run_mode == "dev": print("Starting context refresh loop")

        while True:

            # First delete existing summary file (this blocks any other requests)
            llm_manager.delete_files(self.llm_api_url, \
                self.llm_api_key, 'posts_summary.txt')

            file_id = self.prepare_context()

            time.sleep(5)

            messages = [
                {"role": "user", 
                "content": "Summarize the main topics and themes discussed in the attached file."}]

            llm_response = llm_manager.chat_with_file(self.llm_api_url,\
                    self.llm_api_key, self.llm_model, messages, file_id)

            response_json = llm_response.json()
            if self.run_mode == "dev":
                print(response_json)

            generated_text = response_json['choices'][0]['message']['content']

            #generated_text = self.llm_chat(messages, file_id=file_id)

            with open('posts_summary.txt', 'w', encoding='utf-8') as f:
                f.write(generated_text)

            llm_manager.upload_file(self.llm_api_url, self.llm_api_key, 'posts_summary.txt')

            # Wait for an hour
            time.sleep(3600)


# Class to regularly refresh follows
class FollowsRefresher(LlmPoster):
    def __init__(self, mastodon_api):
        LlmPoster.__init__(self, mastodon_api)

    def start_loop(self):
        if self.run_mode == "dev": print("Starting follower refresh loop")

        while True:
            mastodon_client.refresh_follows(self.mastodon_api)

            # Sleep 5 minutes
            time.sleep(300)

class FallbackNotificationCheck(LlmPoster):
    def __init__(self, mastodon_api):
        LlmPoster.__init__(self, mastodon_api)

    def start_loop(self):
        if self.run_mode == "dev": print("Mastodon API streaming failed, began fallback notification loop")

        latest_mention_id = mastodon_client.fetch_latest_mention(self.mastodon_api)['status']['id']

        if self.run_mode == "dev": print("Latest mention: " + latest_mention_id)

        while True:
            mentions = mastodon_client.fetch_new_mentions(self.mastodon_api, latest_mention_id) 

            if mentions:
                if self.run_mode == "dev":
                    print("New mentions found!")

                for mention in mentions:
                    if self.run_mode == "dev":
                        print(mention['status']['content'])

                    try:
                        self.respond_to_mention(mention)
                    except (NetworkError, FileOperationError, APIResponseError, ConfigurationError, LLMError) as e:
                        self.handle_error()
                    except KeyboardInterrupt:
                        print("\nShutting down gracefully...")
                        raise

                    if mention['status']['id'] > latest_mention_id:
                        latest_mention_id = mention['status']['id']

            # I want this to be reasonably responsive so wait only 10 seconds.
            time.sleep(10)



# Ignore warnings
warning_manager.ignore_future_warnings()

# Load environment variables
env_loader.load_environment_variables()

# Source Mastodon API - can't change this, as we do need an account to interact with the API
mastodon_base_url = env_loader.get_env_variable("MASTODON_BASE_URL", "Enter your Mastodon base URL: ")
mastodon_access_token = env_loader.get_env_variable("MASTODON_ACCESS_TOKEN", "Enter your Mastodon access token: ")
mastodon_api = mastodon_client.init_mastodon(mastodon_base_url, mastodon_access_token)

psr = PostsSummaryRefresher(mastodon_api)

p = threading.Thread(target=psr.start_loop)

p.start()

rlp = RandomLlmPoster(mastodon_api)
flr = FollowsRefresher(mastodon_api)

r = threading.Thread(target=rlp.start_loop)
f = threading.Thread(target=flr.start_loop)

f.start()

# wait a little bit
time.sleep(5)

r.start()

try:
    # Listen for notifications using streaming API
    mastodon_api.stream_user(Stream(mastodon_api)) #Launch stream
except (NetworkError, FileOperationError, APIResponseError, ConfigurationError, LLMError, ConnectionError, TimeoutError) as e:
    print(f"Streaming API failed: {e}")
    # streaming API fails, start fallback
    fnc = FallbackNotificationCheck(mastodon_api)

    n = threading.Thread(target=fnc.start_loop)

    n.start()
except KeyboardInterrupt:
    print("\nShutting down gracefully...")
    raise

# TODO - move updating context file and updating file into a separate script file, so it can be called on notification as well. 



# except KeyboardInterrupt:
#     print("\nExiting...")

