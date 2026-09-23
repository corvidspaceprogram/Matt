import env_loader
import mastodon_client
import refresh_schedule
import warning_manager
from image_bot_base import ImageBotBase
from startup_validator import validate_all
import traceback
import threading
import time
from bot_exceptions import NetworkError, FileOperationError, APIResponseError, ConfigurationError
from logger import logger

# Global shutdown event for graceful termination
SHUTDOWN_EVENT = threading.Event()


# Class for responding to mentions via polling
class NotificationPolling(ImageBotBase):
    def __init__(self, mastodon_api):
        ImageBotBase.__init__(self, mastodon_api)
        self.mastodon_api = mastodon_api

        logger.info("[NotificationPolling] Initializing mention poller")

    def start_loop(self):
        logger.info("[NotificationPolling] Starting mention polling loop")

        latest_mention_id = mastodon_client.fetch_latest_mention(self.mastodon_api)['status']['id']
        logger.info(f"[NotificationPolling] Latest mention: {latest_mention_id}")

        while not SHUTDOWN_EVENT.is_set():

            mentions = mastodon_client.fetch_new_mentions(self.mastodon_api, latest_mention_id)

            if mentions:
                logger.debug("[NotificationPolling] New mentions found")

                for mention in mentions:
                    logger.debug(f"[NotificationPolling] New mention: {mention['status']['content']}")

                    try:
                        terminated = self.respond_to_mention(mention)
                        if terminated:
                            break
                    except (NetworkError, FileOperationError, APIResponseError, ConfigurationError) as e:
                        logger.warning("[NotificationPolling] Mention handling error: " + str(e))
                        self.handle_error(context="[NotificationPolling] Mention handling")
                    except KeyboardInterrupt:
                        logger.info("[NotificationPolling] Shutting down gracefully")
                        break

                    if mention['status']['id'] > latest_mention_id:
                        latest_mention_id = mention['status']['id']

                # Check for shutdown after processing all mentions
                if SHUTDOWN_EVENT.is_set():
                    break

            # Poll every 10 seconds
            terminated = refresh_schedule.sleep_until_shutdown(10, SHUTDOWN_EVENT)
            if terminated:
                break

        logger.info("[NotificationPolling] Ending loop")


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

# Single polling thread
poller = NotificationPolling(mastodon_api)
t = threading.Thread(target=poller.start_loop)

try:
    logger.info("[Main] Starting background thread")
    t.start()
    t.join()

except KeyboardInterrupt:
    # Only really matters for debugging
    logger.info("[Main] Shutting down gracefully")
    SHUTDOWN_EVENT.set()
    time.sleep(10)  # Allow threads time to notice shutdown and exit loops
    t.join()
    exit()

except Exception as e:
    logger.error(f"[Main] CRITICAL ERROR (Thread initialization): {e}")
    traceback.print_exc()
    raise
