from mastodon import Mastodon
from logger import logger


def init_mastodon(api_base_url, access_token):
    return Mastodon(access_token=access_token, api_base_url=api_base_url)


def post_reply_with_media(api, text, status, media_id, char_limit=500):
    """Post a reply to status with an image attachment."""
    truncated_text = text[:char_limit] if len(text) > char_limit else text
    response = api.status_reply(
        status=truncated_text,
        to_status=status,
        media_ids=[media_id],
        language="EN"
    )
    logger.info(f"[Mastodon] Reply with media posted: {response['url'][:80]}")
    return response


def post_dm(api, text, target_account):
    """Send a plain-text direct message to the admin account."""
    response = api.status_post(status=text, visibility="direct")
    logger.info(f"[Mastodon] DM sent to {target_account}: {text[:80]}")
    return response


def post_dm_with_media(api, media_id, target_account):
    """Send a direct message to the admin account with the given media attachment.

    Args:
        api: Mastodon API instance
        media_id: Pre-resolved media ID from the cache or upload
        target_account: Account name to send the DM to
    """
    response = api.status_post(
        status=f"{target_account}",
        media_ids=[media_id],
        visibility="direct"
    )
    logger.info(f"[Mastodon] DM with media sent to {target_account}: media_id={media_id}")
    return response

def fetch_latest_mention(api):
    try:
        max_id = None
        while True:
            batch = api.notifications(max_id=max_id)
            if not batch:
                break
            for notif in batch:
                # Return first mention we come across
                if notif['type'] == 'mention':
                    return notif

            # No mentions found so grab a new batch
            max_id = batch[-1]["id"]

    except Exception as e:
        logger.warning(f"[Mastodon] Error fetching notifications: {e}")
        return []


def fetch_new_mentions(api, min_id):
    try:
        mentions = []
        max_id = None
        while True:
            batch = api.notifications(max_id=max_id)
            if not batch:
                return mentions

            for notif in batch:
                if notif['type'] == 'mention':
                    if int(notif['status']['id']) <= int(min_id):
                        return mentions
                    else:
                        mentions.append(notif)

            # No new mentions found so grab a new batch until min_id
            max_id = batch[-1]["id"]

    except Exception as e:
        logger.warning(f"[Mastodon] Error fetching notifications: {e}")
        return []



