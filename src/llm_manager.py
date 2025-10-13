import requests

def upload_file(url, api_key, file_path):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json'
    }
    files = {'file': open(file_path, 'rb')}
    response = requests.post(url + "v1/files/", headers=headers, files=files)
    return response.json()

def chat_with_file(url, api_key, model, query, file_id):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': query}],
        'files': [{'type': 'file', 'id': file_id}]
    }
    response = requests.post(url + "chat/completions", headers=headers, json=payload)
    return response
    #return response.json()

def chat_with_model(url, api_key, model, query):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    data = {
      "model": model,
      "messages": [
        {
          "role": "user",
          "content": query
        }
      ]
    }
    response = requests.post(url + "chat/completions", headers=headers, json=data)
    return response
    #return response.json()

# Deletes all files called "file_name"
def delete_files(url, api_key, file_name):
    # TODO - error handling for HTML error responses.
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json'
    }
    files_list = requests.get(url + 'v1/files/', headers=headers)

    for file in files_list.json():
        if file['filename'] == file_name:
            requests.delete(url + 'v1/files/' + file['id'], headers=headers)
            
    return

def evaluate_response(text, opening_char, closing_char):
    accepted = False

    openings = text.count(opening_char)
    closings = text.count(closing_char)

    # Check the number of opening/closing characters - want exactly 1 of each
    if openings != 1 or closings != 1:
        print("LLM output failed evaluation! Needs exactly one " + opening_char + closing_char + " pair.")
        return accepted
    
    # Check length of substring between characters. Want more than half of total length
    start_index = text.find(opening_char)
    end_index = text.find(closing_char)
    sub_length = end_index - (start_index + 1)

    if sub_length < len(text)/2:
        print("LLM output failed evaluation! Text between " + opening_char + closing_char + " not long enough.")
        return accepted

    accepted = True

    return accepted