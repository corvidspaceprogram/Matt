from mastodon import Mastodon
from text_cleaner import clean_content, clean_content_keep_usernames
import json
import re
from logger import logger

def init_mastodon(api_base_url, access_token):
    return Mastodon(access_token=access_token, api_base_url=api_base_url)

def contains_keyword(content, keywords):
    """
    Check if content contains any of the specified keywords or key phrases.
    Uses word boundary matching to avoid substring matches within larger words.
    
    Args:
        content: The post content to check
        keywords: Comma-separated string of keywords (can include hashtags and phrases)
    
    Returns:
        True if any keyword/phrase is found with proper boundaries, False otherwise
    """
    if not keywords:
        return False
    
    keyword_list = [k.strip().lower() for k in keywords.split(',')]
    keyword_list = [k for k in keyword_list if k]
    
    content_lower = content.lower()
    
    for keyword in keyword_list:
        # Word boundary regex: not preceded or followed by alphanumeric
        pattern = r'(?<![a-zA-Z0-9])' + re.escape(keyword) + r'(?![a-zA-Z0-9])'
        if re.search(pattern, content_lower):
            return True
    
    return False

def get_account_id(api, username):
    try:
        account = api.account_search(username)[0]
        return account['id']
    except Exception as e:
        logger.warning(f"[Mastodon] Error retrieving account ID for {username}: {e}")
        return None

def fetch_account_posts(api, account_id, clean_func):
    try:
        posts = []
        max_id = None
        while True:
            batch = api.account_statuses(account_id, max_id=max_id, exclude_reblogs=True, exclude_replies=False)
            if not batch:
                break
            posts.extend([clean_func(status["content"]) for status in batch])
            max_id = batch[-1]["id"]
        return posts
    except Exception as e:
        print(f"Error fetching posts: {e}", flush=True)
        return []

def store_instance_posts(api, max_context_length, clean_func, filter_keywords=None, prompt_length=0):
     
    try:
        my_username = api.me()['username']

        posts = dict()
        max_id=None
        while len(json.dumps(posts)) < max_context_length:
            batch = api.timeline_home(max_id=max_id)
            if not batch:
                break
            for status in batch:
                # Filtering out own posts and boosts/images with no text content
                if status['account']['username'] != my_username and status["content"] != "" and status['visibility'] != 'direct':
                    cleaned_content = clean_func(status["content"])
                    if not contains_keyword(cleaned_content, filter_keywords):
                        posts.update({status["id"]: cleaned_content})
            max_id = batch[-1]["id"]

            logger.info(f"[Mastodon] Context stored: {len(json.dumps(posts))} / {max_context_length} chars")
            print("Stored context: " + str(len(json.dumps(posts))) + " / " + str(max_context_length) + " chars.", flush=True)

        # Prune last (oldest) dictionary items until we get back under max length
        while len(json.dumps(posts)) > max_context_length:
            posts.popitem()
            logger.warning(f"[Mastodon] Pruning old posts: {len(json.dumps(posts))} / {max_context_length} chars")
            print("Pruning old posts: " + str(len(json.dumps(posts))) + " / " + str(max_context_length) + " chars.", flush=True)

        # Further prune to account for system prompt size (for LLM context window)
        effective_limit = max_context_length - prompt_length
        while len(json.dumps(posts)) > effective_limit:
            posts.popitem()
            logger.warning(f"[Mastodon] Pruning old posts for context: {len(json.dumps(posts))} / {effective_limit} chars")
            print("Pruning old posts for context: " + str(len(json.dumps(posts))) + " / " + str(effective_limit) + " chars.", flush=True)

        with open('posts.json', 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=4)

    except Exception as e:
        logger.warning(f"[Mastodon] Error fetching posts: {e}")
        return []

# Fetches the parents of a post chain.
def update_instance_posts(api, max_context_length, clean_func, filter_keywords=None, prompt_length=0):
    try:
        my_username = api.me()['username']

        with open('posts.json', 'r', encoding='utf-8') as f:
            posts = json.load(f)
        
        max_id = None
        min_id = list(posts)[0]

        # Empty dictionary
        new_posts = dict()

        # populate new_posts dictionary until min_id is reached
        while True:
            batch = api.timeline_home(max_id=max_id, min_id=min_id)
            if not batch:
                break
            for status in batch:

                # Add to empty dictionary
                if status['account']['username'] != my_username and status["content"] != "" and status['visibility'] != 'direct':
                    cleaned_content = clean_func(status["content"])
                    if not contains_keyword(cleaned_content, filter_keywords):
                        new_posts.update({
                            status["id"]: cleaned_content})

            max_id = batch[-1]["id"]

            logger.info(f"[Mastodon] Added new context: {len(json.dumps(new_posts))} / {max_context_length} chars")
            print("Added new context: " + str(len(json.dumps(new_posts))) + " / " + str(max_context_length) + " chars.", flush=True)

        # Append original posts to new_posts dictionary
        new_posts.update(posts)

        # Replace older posts dictionary with updated version.
        posts = new_posts

        # Prune last (oldest) dictionary items until we get back under max length
        while len(json.dumps(posts)) > max_context_length:
            posts.popitem()
            logger.warning(f"[Mastodon] Pruning old posts: {len(json.dumps(posts))} / {max_context_length} chars")
            print("Pruning old posts: " + str(len(json.dumps(posts))) + " / " + str(max_context_length) + " chars.", flush=True)

        # Further prune to account for system prompt size (for LLM context window)
        effective_limit = max_context_length - prompt_length
        while len(json.dumps(posts)) > effective_limit:
            posts.popitem()
            logger.warning(f"[Mastodon] Pruning old posts for context: {len(json.dumps(posts))} / {effective_limit} chars")
            print("Pruning old posts for context: " + str(len(json.dumps(posts))) + " / " + str(effective_limit) + " chars.", flush=True)

        with open('posts.json', 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=4)
    
    except Exception as e:
        logger.warning(f"[Mastodon] Error fetching posts: {e}")
        return []

# Fetches the parents of a post chain.
def fetch_context(api, status):
    full_context = api.status_context(status['id'])

    message_history = []

    for ancestor in full_context['ancestors']:
        if ancestor['account']['id']==api.me()['id']:
            message_role = "assistant"
            message_content = ""
        else:
            message_role = "user"
            message_content = "[Posted by @" + ancestor['account']['username'] + "] "
        
        message_content += clean_content_keep_usernames(ancestor['content'])

        message_history.append({
            "role": message_role,
            "content": message_content
        })

    if status['account']==api.me():
        message_role = "assistant"
        message_content = "" 
    else:
        message_role = "user"
        message_content = "[Posted by @" + status['account']['username'] + "] "

    message_content += clean_content_keep_usernames(status['content'])

    message_history.append({
        "role": message_role,
        "content": message_content
    })

    return(message_history)

def post_public(api, text, char_limit):
    if len(text) > char_limit:
        text = text[:char_limit]
    response = api.status_post(status=text, language="EN", visibility="public")
    logger.info(f"[Mastodon] Posted successfully: {response['url'][:80]}")

def post_dm(api, text, char_limit, target_account):
    post_text = target_account + " \n\n" + text
    if len(post_text) > char_limit:
        post_text = post_text[:char_limit]
    response = api.status_post(status=post_text, language="EN", visibility="direct")
    logger.info(f"[Mastodon] DM Posted successfully: {response['url'][:80]}")

def post_reply(api, text, char_limit, original_status):

    # If original post is local-only (has an eye emoji) then append eye emoji
    original_status_content = clean_content(original_status['content'])

    eye_index = original_status_content.find("👁️")
    if eye_index != -1:
        text = text + " 👁️"

    # TODO - this would remove the eye
    if len(text) > char_limit:
        text = text[:char_limit]

    # status_reply prepends mentions for the accounts being replied to and retains the visibility of the previous post automatically.
    response = api.status_reply(status=text, to_status=original_status, language="EN")

    logger.info(f"[Mastodon] Reply Posted successfully: {response['url'][:80]}")

    print(f"Posted successfully: {response['url']}", flush=True)

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

