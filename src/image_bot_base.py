import env_loader
import glob
import mastodon_client
import os
import random
import sys
import traceback
from datetime import datetime
from bot_exceptions import ConfigurationError, FileOperationError
from logger import logger


class ImageBotBase():
    def __init__(self, mastodon_api):
        self.mastodon_api = mastodon_api

        # Reference to shutdown event for graceful termination
        from main import SHUTDOWN_EVENT
        self.shutdown_event = SHUTDOWN_EVENT

        # Admin account is optional
        try:
            self.admin_account = env_loader.get_env_variable("ADMIN_MASTODON_ACCOUNT")
        except ConfigurationError:
            self.admin_account = None

        # Run mode is optional, defaults to dev
        try:
            self.run_mode = env_loader.get_env_variable("RUN_MODE")
        except ConfigurationError:
            self.run_mode = "dev"



    def respond_to_mention(self, mention):
        """
        Respond to an @mention by randomly selecting and posting an image.

        Args:
            mention: Mastodon notification dict with a 'status' key

        Returns:
            False (completed normally)
        """
        # Check if shutdown requested
        if self.shutdown_event.is_set():
            return True

        st = mention['status']

        # List available image files from repo root /images/
        repo_images = os.path.join(os.getcwd(), '..', 'images', '*')
        possible_paths = [
            repo_images,
            '/Users/luke/Desktop/Matt/images/*',
        ]
        image_files = []
        valid_extensions = ('.jpg', '.jpeg', '.png', '.gif')

        for path_template in possible_paths:
            matches = glob.glob(path_template)
            for f in matches:
                if os.path.isfile(f) and os.path.splitext(f)[1].lower() in valid_extensions:
                    image_files.append(f)
            # If we found files, stop searching
            if image_files:
                break

        if not image_files:
            logger.warning("[ImageBot] No image files found in /images/ folder")
            return False

        # Randomly select one image
        selected_image = random.choice(image_files)
        logger.info(f"[ImageBot] Selected: {selected_image}")

        # Upload the image
        media_id = self.mastodon_api.media_post(selected_image)
        logger.info(f"[ImageBot] Uploaded image, media_id: {media_id}")

        # In dev mode, send image as DM to admin instead of replying publicly
        if self.run_mode == "dev":
            mastodon_client.post_dm_with_media(
                self.mastodon_api,
                media_id=media_id,
                selected_image=selected_image,
                target_account=self.admin_account
            )
            logger.info(f"[ImageBot] Dev DM sent to {self.admin_account}")
        else:
            # Post reply with media attachment (prod mode)
            mastodon_client.post_reply_with_media(
                self.mastodon_api,
                text="",
                status=st,
                media_id=media_id,
                char_limit=500
            )
            logger.info(f"[ImageBot] Reply posted successfully for mention")

        # Check for shutdown after completion
        if self.shutdown_event.is_set():
            return True

        return False

    def handle_error(self, context=""):
        """
        Handle errors with logging and optional admin notification.

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

        logger.warning(" > ERROR:")
        logger.warning(error_msg)
        logger.warning(full_msg)

        # Log to file with timestamp
        with open('errorlog.txt', "a") as f:
            f.write(log_entry)

        # DM admin account with error details
        if self.admin_account is not None:
            admin_msg = f"Error: {error_type}{context_str}\n{str(error)[:200]}"
            try:
                mastodon_client.post_dm(self.mastodon_api, admin_msg, self.admin_account)
            except:
                pass  # Don't fail if admin notification fails
