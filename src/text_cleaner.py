from html import unescape
import html_text
import re

def clean_content(content):
    cleaned_content = clean_content_keep_usernames(content)
    cleaned_content = re.sub(r'@\w+', '', cleaned_content)  # Remove usernames

    return cleaned_content

def clean_content_keep_usernames(content):
    # Remove only span elements from html - causes extra spaces in extract_text
    cleaned_content = re.sub(r'<span.*?>|</span>', '', content) 
    cleaned_content = html_text.extract_text(\
        cleaned_content, guess_layout=False)

    return cleaned_content

def remove_delimiters(text, opening_char, closing_char):
    # Find the index of the opening character
    start_index = text.find(opening_char)
    if start_index == -1:
        return text  # Return the original string if no opening square bracket is found
    
    # Find the index of the closing character
    end_index = text.rfind(closing_char)
    
    # Check if there is more than one character between them
    if end_index > start_index + 1:
        return text[start_index + 1:end_index]  # Return the substring between the two brackets
    
    # If not, return the original string
    return text

def remove_special_chars(text):
    cleaned_content = re.sub(r'[^\w\s.,!?;:]', '', text)  # Remove special characters
    return cleaned_content