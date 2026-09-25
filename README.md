# Mastodon Image Reply Bot

A Python bot that responds to @mentions on Mastodon by randomly posting an attached image. In development mode (`RUN_MODE=dev`), images are sent as direct messages to a specified admin account instead of being posted publicly.

Forked and substantially altered from [mastodon-markov](https://github.com/ewanc26/mastodon-markov) by ewanc26 on Github.

## Setup

1. Clone this repository. All commands below should be run from the repository root.

2. (Optional) Create and activate a virtual environment for the dependencies: 

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required dependencies by running:

   ```bash
   pip install mastodon.py python-dotenv
   ```

4. In the `src/` directory, create a `.env` file with the following variables:

   ```env
   # Mandatory variables
   MASTODON_BASE_URL=<source Mastodon instance base URL>
   MASTODON_ACCESS_TOKEN=<source Mastodon account access token>

   # Optional variables
   ADMIN_MASTODON_ACCOUNT=<admin Mastodon account to DM reports to>
   RUN_MODE=dev  # "dev" sends images as DMs; "prod" replies publicly to mentions
   ```

A `.env.example` file is included in `src/` for reference with all variable names and example values.

To create an access token for this application, go to Settings > Development while logged into Mastodon as the automated account. This bot requires the following application scopes: 
- `read:notifications`
- `profile`
- `write:media`
- `write:statuses`

## Usage

1. Place image files (`.jpg`, `.jpeg`, `.png`, `.gif`) in the `/images/` directory at the project root.

2. Run the `main.py` script located in the `/src/` directory:

   ```bash
   python src/main.py
   ```

3. The bot will respond to @mentions by randomly selecting an image and either replying with it publicly (prod mode) or sending it as a direct message to the admin account (dev mode). It also listens for notifications in real-time.

4. Press `Ctrl+C` to stop the script gracefully.

## File Structure

- `/src/`
  - `image_bot_base.py`: Core bot class handling image selection and posting logic.
  - `mastodon_client.py`: Interfaces with the Mastodon API for fetching mentions and posting media.
  - `refresh_schedule.py`: Calculates timing intervals and manages sleep scheduling.
  - `env_loader.py`: Loads and manages environment variables.
  - `logger.py`: Structured logging to console + rotating file.
  - `bot_exceptions.py`: Custom exception hierarchy for the bot.
  - `startup_validator.py`: Validates configuration at startup for fail-fast error reporting.
  - `warning_manager.py`: Handles suppression of specific warnings.
  - `main.py`: Entry point — initializes the API client and starts the notification polling thread.
- `/images/`: Directory containing image files the bot randomly selects from.

## Notes

- Ensure that the Mastodon account has appropriate permissions and visibility settings for posting.
- If you need to change any Mastodon or environment variables, update them in the `.env` file.
