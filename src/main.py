from mastodon import StreamListener
from mastodon.errors import MastodonMalformedEventError
from llm_poster import LlmPoster
import llm_manager
import warning_manager
import env_loader
import mastodon_client
import refresh_schedule
from startup_validator import validate_all
import os
from datetime import datetime
import threading
import time
from bot_exceptions import NetworkError, FileOperationError, APIResponseError, ConfigurationError, LLMError
from logger import logger, warning_handler

# Class for responding to mentions
class Stream(StreamListener, LlmPoster):
    def __init__(self, mastodon_api): #Inheritance
        LlmPoster.__init__(self, mastodon_api)
        StreamListener.__init__(self)

        logger.info("[Stream] Initializing notification listener")

    def on_notification(self,notif): #Called when a notification comes
        if notif['type'] == 'mention': #Check if the content of the notification is a mention

            try:
                self.respond_to_mention(notif)

            except (NetworkError, FileOperationError, APIResponseError, ConfigurationError, LLMError) as e:
                self.handle_error(context="[Stream] Notification handling")
            except KeyboardInterrupt:
                logger.info("[Stream] Shutting down gracefully")
                raise

# Class for random posts
class RandomLlmPoster(LlmPoster):
    def __init__(self, mastodon_api):
        LlmPoster.__init__(self, mastodon_api)

    def start_loop(self):
        logger.info("[RandomLlmPoster] Starting schedule loop")

        while True:
            """
            Raise errors within any function that could fail i.e. interacting 
            with internet - LLM calls and mastodon API stuff.

            Handle these errors in the try/catch block here.
            """
            try:
                # Read next refresh from file
                next_refresh = refresh_schedule.read_refresh_from_file("next_post_time.txt")

                # Sleep until next refresh
                if next_refresh is not None:
                    refresh_schedule.sleep_until_next_refresh(next_refresh)

                # Schedule next refresh
                current_time = datetime.now()
                refresh_interval = refresh_schedule.calculate_refresh_interval()
                next_refresh = refresh_schedule.calculate_next_refresh(\
                    current_time, refresh_interval)

                # Write to file
                refresh_schedule.write_refresh_to_file(next_refresh, "next_post_time.txt")

                # Prepare context (posts_tmp.txt)
                file_id = self.prepare_context()

                # This is necessary to allow the text embedding model enough time to load before the embeddings are needed. 
                time.sleep(5)

                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": "Write a message for the platform, picking one topic from the attached context."}
                ]

                generated_text = self.llm_chat(messages, file_id=file_id)

                if self.run_mode == "prod":
                    mastodon_client.post_public(self.mastodon_api, generated_text,\
                        self.char_limit)
                elif self.run_mode == "dev":
                    logger.info("[RandomLlmPoster] Generated output: " + generated_text[:100] + "...")
                    print(generated_text, flush=True)
                    if self.admin_account is not None:
                        mastodon_client.post_dm(self.mastodon_api, \
                            generated_text, self.char_limit, self.admin_account)

            except (NetworkError, FileOperationError, APIResponseError, ConfigurationError, LLMError) as e:
                logger.warning("[RandomLlmPoster] Posting loop error: " + str(e))
                self.handle_error(context="[RandomLlmPoster] Posting loop")
            except KeyboardInterrupt:
                logger.info("[RandomLlmPoster] Shutting down gracefully")
                raise




# Class to regularly refresh follows
class FollowsRefresher(LlmPoster):
    def __init__(self, mastodon_api):
        LlmPoster.__init__(self, mastodon_api)

    def start_loop(self):
        logger.info("[FollowsRefresher] Starting loop")

        while True:
            mastodon_client.refresh_follows(self.mastodon_api)

            # Sleep 5 minutes
            time.sleep(300)

class FallbackNotificationCheck(LlmPoster):
    def __init__(self, mastodon_api):
        LlmPoster.__init__(self, mastodon_api)

    def start_loop(self):
        logger.info("[FallbackNotificationCheck] Starting fallback notification loop")

        latest_mention_id = mastodon_client.fetch_latest_mention(self.mastodon_api)['status']['id']
        logger.info(f"[FallbackNotificationCheck] Latest mention: {latest_mention_id}")

        while True:
            mentions = mastodon_client.fetch_new_mentions(self.mastodon_api, latest_mention_id) 

            if mentions:
                logger.debug("[FallbackNotificationCheck] New mentions found")

                for mention in mentions:
                    logger.debug(f"[FallbackNotificationCheck] New mention: {mention['status']['content']}")

                    try:
                        self.respond_to_mention(mention)
                    except (NetworkError, FileOperationError, APIResponseError, ConfigurationError, LLMError) as e:
                        logger.warning("[FallbackNotificationCheck] Mention handling error: " + str(e))
                        self.handle_error(context="[Stream] Mention handling")
                    except KeyboardInterrupt:
                        logger.info("[FallbackNotificationCheck] Shutting down gracefully")
                        raise

                    if mention['status']['id'] > latest_mention_id:
                        latest_mention_id = mention['status']['id']

            # I want this to be reasonably responsive so wait only 10 seconds.
            time.sleep(10)



# Ignore warnings
warning_manager.ignore_future_warnings()

# Load environment variables
env_loader.load_environment_variables()

# Validate all configuration at startup
validate_all()

# Source Mastodon API - can't change this, as we do need an account to interact with the API
mastodon_base_url = env_loader.get_env_variable("MASTODON_BASE_URL", "Enter your Mastodon base URL: ")
mastodon_access_token = env_loader.get_env_variable("MASTODON_ACCESS_TOKEN", "Enter your Mastodon access token: ")
mastodon_api = mastodon_client.init_mastodon(mastodon_base_url, mastodon_access_token)
logger.info("[Main] Mastodon API initialized successfully")

rlp = RandomLlmPoster(mastodon_api)
flr = FollowsRefresher(mastodon_api)
fnc = FallbackNotificationCheck(mastodon_api)

r = threading.Thread(target=rlp.start_loop)
f = threading.Thread(target=flr.start_loop)
n = threading.Thread(target=fnc.start_loop)

try:
    logger.info("[Main] Starting background threads")

    f.start()

    # wait a little bit
    time.sleep(5)

    r.start()
    n.start()

    f.join(); r.join(); n.join()

except KeyboardInterrupt:
    # Only really matters for debugging
    logger.info("[Main] Shutting down gracefully")
    raise
except Exception as e:
    logger.error(f"[Main] CRITICAL ERROR (Thread initialization): {e}")
    logger.error("[Main] Stack trace: " + traceback.format_exc())
    traceback.print_exc()
    
    # Re-raise or log to file. 
    raise 

# TODO - move updating context file and updating file into a separate script file, so it can be called on notification as well. 



# except KeyboardInterrupt:
#     print("\nExiting...")

