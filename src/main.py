import env_loader
import glob
import mastodon_client
import os
import random
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

        latest_ment = mastodon_client.fetch_latest_mention(self.mastodon_api)
        if latest_ment is None:
            logger.info("[NotificationPolling] No prior mentions found — starting fresh")
            latest_mention_id = 0
        else:
            latest_mention_id = latest_ment['status']['id']
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

                    if int(mention['status']['id']) > int(latest_mention_id):
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

# New GreatReactor background thread
class GreatReactor(ImageBotBase):
    def __init__(self, mastodon_api):
        ImageBotBase.__init__(self, mastodon_api)
        self.mastodon_api = mastodon_api
        # Cache bot's own account ID once at startup
        try:
            self.my_account_id = self.mastodon_api.me()['id']
            logger.info(f"[GreatReactor] Bot account ID: {self.my_account_id}")
        except Exception as e:
            logger.warning(f"[GreatReactor] Failed to fetch own account ID: {e}")
            self.my_account_id = None

    def start_loop(self):
        logger.info("[GreatReactor] Starting timeline reactor loop")

        while not SHUTDOWN_EVENT.is_set():
            try:
                self.process_timeline()
            except Exception as e:
                logger.warning(f"[GreatReactor] Loop error: {e}")
                traceback.print_exc()

            terminated = refresh_schedule.sleep_until_shutdown(3600, SHUTDOWN_EVENT)
            if terminated:
                break

        logger.info("[GreatReactor] Ending loop")

    def process_timeline(self):
        """Poll local timeline in reverse-chronological order and reply to ':great:' reactions."""
        logger.info("[GreatReactor] Starting timeline scan")

        max_id = None

        while not SHUTDOWN_EVENT.is_set():
            batch = self.mastodon_api.timeline('local', local=True, max_id=max_id)
            if not batch:
                break

            for status in batch:
                # Skip bot's own posts (never reply to self)
                if self._is_own_post(status):
                    continue

                # Filter 1: must have at least one custom reaction
                reactions = status.get('reactions', [])
                if not reactions:
                    continue

                # Filter 2: must have a 'great' custom reaction
                has_great = any(r.get('name') == 'great' for r in reactions)
                if not has_great:
                    continue

                # Deduplication: skip if bot already replied to this exact status
                if mastodon_client.bot_already_replied(status, self.mastodon_api, self.my_account_id):
                    continue

                # All filters passed — reply with image
                logger.info(f"[GreatReactor] Replying to {status['id']}")
                self.respond_with_image(status)

            # Continue pagination backward (oldest first)
            if batch:
                max_id = int(min(batch, key=lambda s: int(s['id']))['id']) - 1

        logger.info("[GreatReactor] Timeline scan complete.")

    def _is_own_post(self, status):
        """Return True if this status was posted by the bot itself."""
        return status['account']['id'] == self.my_account_id

    def respond_with_image(self, status):
        """Select a random image and reply to the given status with it."""
        if self.shutdown_event.is_set():
            return

        # --- Image selection (same logic as ImageBotBase.respond_to_mention) ---
        valid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
        matches = glob.glob(os.path.join(os.getcwd(), 'images', '*'))
        image_files = [f for f in matches if os.path.isfile(f) and os.path.splitext(f)[1].lower() in valid_extensions]

        if not image_files:
            logger.warning("[GreatReactor] No image files found in /images/ folder")
            return

        selected_image = random.choice(image_files)
        logger.info(f"[GreatReactor] Selected: {selected_image}")
        media_id = self.mastodon_api.media_post(selected_image)
        logger.info(f"[GreatReactor] Uploaded image, media_id: {media_id}")

        # --- Dev vs Prod behavior ---
        if self.run_mode == "dev":
            # DM the image to admin with URL of the reacted-to post
            post_url = status.get('url', '')
            if not post_url and status['account'].get('username'):
                instance_url = env_loader.get_env_variable("MASTODON_BASE_URL")
                post_url = f"{instance_url}/@{status['account']['username']}/{status['id']}"
            dm_msg = f"Great reaction found on: {post_url}\nImage attached below."
            try:
                mastodon_client.post_dm_with_media(
                    self.mastodon_api, media_id=media_id,
                    target_account=self.admin_account
                )
                logger.info(f"[GreatReactor] Dev DM sent to {self.admin_account} for post URL: {post_url}")
            except Exception as e:
                logger.warning(f"[GreatReactor] Failed to send dev DM: {e}")
        else:
            # Public reply with image attachment
            mastodon_client.post_reply_with_media(
                self.mastodon_api,
                text="",
                status=status,
                media_id=media_id,
                char_limit=500
            )
            logger.info(f"[GreatReactor] Reply posted for {status['id']}")


# Single polling thread
poller = NotificationPolling(mastodon_api)
t = threading.Thread(target=poller.start_loop)
reactor = GreatReactor(mastodon_api)
r_thread = threading.Thread(target=reactor.start_loop)

try:
    logger.info("[Main] Starting background threads")

    t.start()
    time.sleep(2)  # Brief stagger to avoid startup race conditions
    r_thread.start()

    t.join(); r_thread.join()

except KeyboardInterrupt:
    # Only really matters for debugging
    logger.info("[Main] Shutting down gracefully")
    SHUTDOWN_EVENT.set()
    time.sleep(5) # Allow threads time to notice shutdown and exit loops
    t.join(); r_thread.join()
    exit()

except Exception as e:
    logger.error(f"[Main] CRITICAL ERROR (Thread initialization): {e}")
    traceback.print_exc()
    raise


