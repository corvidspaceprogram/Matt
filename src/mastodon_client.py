from mastodon import Mastodon
import json

def init_mastodon(api_base_url, access_token):
    return Mastodon(access_token=access_token, api_base_url=api_base_url)

def get_account_id(api, username):
    try:
        account = api.account_search(username)[0]
        return account['id']
    except Exception as e:
        print(f"Error retrieving account ID for {username}: {e}")
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
        print(f"Error fetching posts: {e}")
        return []

def fetch_instance_posts(api, clean_func):
    try:
        posts = []
        max_id = None
        while len(posts) < 200:
            batch = api.timeline_local(max_id=max_id)
            if not batch:
                break
            posts.extend([clean_func(status["content"]) for status in batch])
            max_id = batch[-1]["id"]
        return posts
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return []

def store_instance_posts(api, max_context_length, clean_func):
    try:
        posts = dict()
        max_id=None
        while len(json.dumps(posts)) < max_context_length:
            batch = api.timeline_local(max_id=max_id)
            if not batch:
                break
            for status in batch:
                posts.update({status["id"]: clean_func(status["content"])})
            max_id = batch[-1]["id"]

            print("Stored context: " + str(len(json.dumps(posts))) + " / " + str(max_context_length) + " chars.")

        # Prune last (oldest) dictionary items until we get back under max length
        while len(json.dumps(posts)) > max_context_length:
            posts.popitem()
            print("Pruning old posts: " + str(len(json.dumps(posts))) + " / " + str(max_context_length) + " chars.")

        with open('posts.json', 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=4)

    except Exception as e:
        print(f"Error fetching posts: {e}")
        return []

def convert_instance_posts_txt():
    try:
        text = ""

        with open('posts_tmp.json', 'r', encoding='utf-8') as f:
            posts = json.load(f)

        for value in posts.values():
            text += value + "\n"

        with open('posts_tmp.txt', 'w', encoding='utf-8') as f:
            f.write(text)

    except Exception as e:
        print(f"Error converting posts to txt file: {e}")
        return []

def update_instance_posts(api, max_context_length, clean_func):
    try:
        with open('posts.json', 'r', encoding='utf-8') as f:
            posts = json.load(f)
        
        max_id = None
        min_id = list(posts)[0]

        # Empty dictionary
        new_posts = dict()

        # populate new_posts dictionary until min_id is reached
        while True:
            batch = api.timeline_local(max_id=max_id, min_id=min_id)
            if not batch:
                break
            for status in batch:
                # Add to empty dictionary
                new_posts.update({status["id"]: clean_func(status["content"])})

            max_id = batch[-1]["id"]

            print("Added new context: " + str(len(json.dumps(posts))) + " / " + str(max_context_length) + " chars.")

        # Append original posts to new_posts dictionary
        new_posts.update(posts)

        # Replace older posts dictionary with updated version.
        posts = new_posts

        # Prune last (oldest) dictionary items until we get back under max length
        while len(json.dumps(posts)) > max_context_length:
            posts.popitem()
            print("Pruning old posts: " + str(len(json.dumps(posts))) + " / " + str(max_context_length) + " chars.")

        with open('posts.json', 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=4)
    
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return []

# Creates a posts_tmp.json file ensuring that the combined length of posts and 
# prompt stays under the max_context_length
def truncate_post_file(max_context_length, prompt):
    try:
        with open('posts.json', 'r', encoding='utf-8') as f:
            posts = json.load(f)

        # Prune last (oldest) dictionary items until we get back under max length
        while len(json.dumps(posts)) > (max_context_length - len(prompt)):
            posts.popitem()
            print("Pruning old posts for tmp json file: " + str(len(json.dumps(posts))) + " / " + str(max_context_length) + " chars.")

        with open('posts_tmp.json', 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=4)

    except Exception as e:
        print(f"Error truncating post file: {e}")
        return []
