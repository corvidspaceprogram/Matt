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


def post_dm(api, text, char_limit, target_account):
    post_text = target_account + " \n\n" + text
    if len(post_text) > char_limit:
        post_text = post_text[:char_limit]
    response = api.status_post(status=post_text, language="EN", visibility="direct")
    logger.info(f"[Mastodon] DM Posted successfully: {response['url'][:80]}")


# Use regularly to check follows and make sure following is matched.
def refresh_follows(api):

    # Follow anyone who follows me that I don't follow yet
    for account in api.account_followers(api.me()):
        if account not in api.account_following(api.me()):
            api.account_follow(account)

    # Unfollow anyone I follow who no longer follows me
    for account in api.account_following(api.me()):
        if account not in api.account_followers(api.me()):
            api.account_unfollow(account)

    # Follow is a weird word

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
                    if notif['status']['id'] <= min_id:
                        return mentions
                    else:
                        mentions.append(notif)

            # No new mentions found so grab a new batch until min_id
            max_id = batch[-1]["id"]

    except Exception as e:
        logger.warning(f"[Mastodon] Error fetching notifications: {e}")
        return []
