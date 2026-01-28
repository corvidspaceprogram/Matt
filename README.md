# Mastodon LLM Bot

This Python project generates and publishes automated Mastodon posts at random intervals based on posts from the automated account's followers. It periodically updates its dataset, and it also replies to mentions.

Forked and substantially altered from [mastodon-markov](https://github.com/ewanc26/mastodon-markov) by ewanc26 on Github.

## Setup

1. Clone this repository and navigate to the `/src/` directory containing the modular scripts.

2. (Optional) Create and activate a virtual environment for the dependencies: 

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install the required dependencies by running:

   ```bash
   pip install requests mastodon.py python-dotenv
   ```

4. Create a `.env` file and add the following variables:

   ```env
   # Mandatory variables
   MASTODON_BASE_URL=<source Mastodon instance base URL>
   MASTODON_ACCESS_TOKEN=<source Mastodon account access token>
   LLM_API_URL=<OpenAI-format provider URL>
   LLM_API_KEY=<API key for LLM>
   LLM_MODEL=<model name e.g. granite-3.3-2b-instruct>
   SYSTEM_PROMPT=<System prompt for LLM. See below for example.>
   MAX_CONTEXT_LENGTH=<maximum length for context file in characters>

   # Optional variables
   DESTINATION_MASTODON_CHAR_LIMIT=<post character limit> # Defaults to 500
   ADMIN_MASTODON_ACCOUNT=<admin Mastodon account to DM reports to>
   RUN_MODE=<"dev" or "prod"> # Defaults to "dev"
   ```

Example of a system prompt: 

   ```
   "You are automated account on a microblogging platform with the username <USERNAME>. Your responses must adhere strictly to these guidelines:
   - The response must begin with a single ¥ character and end with a single √ character. Do not use these characters for any other purpose.
   - Do not surround your response with quotation marks.
   - Do not provide any introductory or concluding remarks.
   - Use less than 500 characters.
   - <Any additional style or context usage instructions>"
   ```

## Usage

1. Run the `main.py` script located in the `/src/` directory by executing:

   ```bash
   python src/main.py
   ```

2. The script will a) regularly fetch recent posts from the automated Mastodon account's followers and summarize them for context, b) generate LLM text and post it to the Mastodon account at random intervals between 6 and 48 hours, and c) set up a notification listener to respond to mentions. 

3. Press `Ctrl+C` to stop the script.

## File Structure

- `/src/`
  - `warnings_manager.py`: Handles suppression of specific warnings.
  - `env_loader.py`: Loads and manages environment variables.
  - `mastodon_client.py`: Interfaces with the Mastodon API for fetching and posting data.
  - `text_cleaner.py`: Cleans and preprocesses text content.
  - `llm_manager.py`: Manages interaction with the LLM API.
  - `llm_poster.py`: Handles posting generated content to Mastodon.
  - `refresh_schedule.py`: Calculates refresh intervals and manages scheduling.
  - `main.py`: Orchestrates the entire process by tying together all modules.

## Notes

- Ensure that the Mastodon account has appropriate permissions and visibility settings for posting.
- If you need to change any Mastodon or environment variables, update them in the `.env` file.
- The modular structure allows customisation and scaling of specific functionalities by modifying the respective scripts in the `/src/` directory.