def post_to_mastodon(api, text, char_limit):
    try:
        if len(text) > char_limit:
            text = text[:char_limit]
        response = api.status_post(status=text, spoiler_text="LLM-generated post", language="EN", visibility="public")
        print(f"Posted successfully: {response['url']}")
    except Exception as e:
        print(f"Error posting to Mastodon: {e}")

def post_dm_to_mastodon(api, text, char_limit, target_account):
    try:
        post_text = target_account + "\n\n" + text
        if len(post_text) > char_limit:
            post_text = post_text[:char_limit]
        response = api.status_post(status=post_text, spoiler_text="LLM-generated post", language="EN", visibility="direct")
        print(f"Posted successfully: {response['url']}")
    except Exception as e:
        print(f"Error posting to Mastodon: {e}")

def post_reply_to_mastodon(api, text, char_limit, original_status):
    try:
        if len(text) > char_limit:
            text = text[:char_limit]

        # status_reply prepends mentions for the accounts being replied to and retains the visibility of the previous post automatically.
        response = api.status_reply(status=text, to_status=original_status, spoiler_text="LLM-generated post", language="EN")

        print(f"Posted successfully: {response['url']}")
    except Exception as e:
        print(f"Error posting to Mastodon: {e}")    

def random_post_schedule_loop(mastodon_api, context_limit, \
    llm_api_url, llm_api_key, llm_model, llm_prompt, char_limit):
    import mastodon_client
    import text_cleaner
    import refresh_schedule
    import llm_manager
    from datetime import datetime
    import os

    while True:

        current_time = datetime.now()
        refresh_interval = refresh_schedule.calculate_refresh_interval()
        next_refresh = refresh_schedule.calculate_next_refresh(current_time, refresh_interval)

        if os.path.exists('posts.json'):
            # Refresh post history file
            mastodon_client.update_instance_posts(mastodon_api, context_limit, text_cleaner.clean_content)
        else: 
            # Create posts.json file
            mastodon_client.store_instance_posts(mastodon_api, context_limit, text_cleaner.clean_content)
        
        mastodon_client.truncate_post_file(context_limit, llm_prompt)

        mastodon_client.convert_instance_posts_txt()

        # Delete previous posts_tmp.txt from server
        llm_manager.delete_files(llm_api_url, llm_api_key, 'posts_tmp.txt')

        file_upload_response = llm_manager.upload_file(llm_api_url, llm_api_key, 'posts_tmp.txt')
        file_id = file_upload_response['id']

        response_accepted = False

        while not response_accepted:

            query_response = llm_manager.chat_with_file(llm_api_url, llm_api_key, llm_model, llm_prompt, file_id)

            print(query_response)
            response_json = query_response.json()
            print(response_json['choices'][0]['message']['content'])

            response_accepted = llm_manager.evaluate_response(response_json['choices'][0]['message']['content'], "¥", "√")

            # TODO - handle html errors
            
        generated_text = \
            text_cleaner.remove_delimiters(response_json['choices'][0]['message']['content'], "¥", "√") + " 👁️"

        post_to_mastodon(mastodon_api, generated_text, char_limit)

        print(generated_text)

        # Sleep until next refresh
        refresh_schedule.sleep_until_next_refresh(next_refresh)