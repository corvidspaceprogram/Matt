# Based on https://linuxtut.com/en/401663bf0cea9c6ad324/

from mastodon import Mastodon, StreamListener
import llm_manager
import mastodon_client
from post_manager import post_reply_to_mastodon
import requests
from text_cleaner import clean_content, remove_delimiters
import env_loader

class Stream(StreamListener):
    def __init__(self, mastodon_api, llm_api_url, llm_api_key, model, max_context_length): #Inheritance
        super(Stream, self).__init__()
        # self.logger = logging.getLogger

        print("Initializing notification listener")

        self.mastodon = mastodon_api
        self.url = llm_api_url
        self.api_key = llm_api_key
        self.model = model
        self.max_context_length = max_context_length

    def on_notification(self,notif): #Called when a notification comes
        if notif['type'] == 'mention': #Check if the content of the notification is a mention

            st = notif['status']
            context = fetch_context(st, self.mastodon)
            user = st['account']['username']
            
            # Write query based on context and other information
            # TODO - add another .env variable? 

            query = """You are an automated account with the username \"@gronk\" on the Mastodon instance mastodo.neoliber.al. Write a short post for this instance, adhering strictly to the following guidelines:
            - use less than 500 characters
            - the post content must begin with a single ¥ character and end with a single √ character. Do not use these characters for any other purpose.
            - use the attached text file of recent posts from other users to inform your writing style
            - do not provide any introductory or concluding remarks
            - your post must be in response to the following conversation: \n\n """

            query += context

            print(query)

            mastodon_client.truncate_post_file(self.max_context_length, query)

            mastodon_client.convert_instance_posts_txt()

            # Delete previous posts_tmp.txt from server
            llm_manager.delete_files(self.url, self.api_key, 'posts_tmp.txt')

            file_upload_response = llm_manager.upload_file(self.url, self.api_key, 'posts_tmp.txt')
            file_id = file_upload_response['id']

            response_accepted = False
            
            while not response_accepted:

                llm_response = llm_manager.chat_with_file(self.url, self.api_key, self.model, query, file_id)

                print(llm_response)

                response_json = llm_response.json()

                response_accepted = llm_manager.evaluate_response(response_json['choices'][0]['message']['content'], "¥", "√")

                print(response_json['choices'][0]['message']['content'])

            generated_text = \
                remove_delimiters(response_json['choices'][0]['message']['content'], "¥", "√") + " 👁️"

            print(generated_text)

            post_reply_to_mastodon(self.mastodon, generated_text, 500, st)

def fetch_context(status, mastodon):
    full_context = mastodon.status_context(status['id'])

    out = ""

    for ancestor in full_context['ancestors']:
        out += "\"" + clean_content(ancestor['content']) + "\" "
        #out += "@" + ancestor['account']['username'] + ": " + \
        #    clean_content(ancestor['content']) + \
        #    '\n\n'

    out += "\"" + clean_content(status['content']) + "\""

    # out += "@" + status['account']['username'] + ": @gronk " + \
    #     clean_content(status['content'])

    # out += "\n\n "

    return(out)
    

def write_query(context):
    # TODO populate
    pass

