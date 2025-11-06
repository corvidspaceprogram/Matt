from html import unescape
import re

def clean_content(content):
    cleaned_content = re.sub('<[^<]+?>', '', content)  # Remove HTML tags
    cleaned_content = unescape(cleaned_content)  # Decode HTML entities
    cleaned_content = re.sub(r'@\w+', '', cleaned_content)  # Remove usernames
    #cleaned_content = re.sub(r'[^\w\s.,!?;:]', '', cleaned_content)  # Remove special characters
    #cleaned_content = re.sub(r':\w+:', '', cleaned_content)  # Remove words enclosed with colons

    return cleaned_content

def clean_content_keep_usernames(content):
    cleaned_content = re.sub('<[^<]+?>', '', content)  # Remove HTML tags
    cleaned_content = unescape(cleaned_content)  # Decode HTML entities

    return cleaned_content

def remove_quotes(text):
    # Find the index of the first quotation mark
    start_index = text.find('"')
    if start_index == -1:
        return text  # Return the original string if no opening quotation mark is found
    
    # Find the index of the last quotation mark
    end_index = text.rfind('"')
    
    # Check if there is more than one character between them
    if end_index > start_index + 1:
        return text[start_index + 1:end_index]  # Return the substring between the two quotation marks
    
    # If not, return the original string
    return text

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