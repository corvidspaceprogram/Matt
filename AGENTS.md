# AGENTS.md

This file contains guidelines and commands for agentic coding agents working on this Mastodon Image Reply Bot repository.

## Project Overview

This is a Python project that creates an automated Mastodon bot responding to @mentions with randomly selected images. In development mode (`RUN_MODE=dev`), images are sent as direct messages to a specified admin account instead of being posted publicly. The bot runs as a single-threaded notification poller.

## Environment Setup

**Dependencies Installation:**
```bash
pip install requests mastodon.py python-dotenv
```

**Virtual Environment (Recommended):**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

## Running the Application

**Main Application:**
```bash
python src/main.py
```

**No formal test framework is configured** - Manual testing is done by running the main application and observing behavior in dev mode.

## Code Style Guidelines

### Import Organization
- Standard library imports first (os, time, datetime, etc.)
- Third-party imports second (requests, mastodon, dotenv, etc.)
- Local imports last (env_loader, mastodon_client, etc.)
- One import per line preferred, but grouping related imports is acceptable

### Naming Conventions
- **Variables/Functions:** `snake_case` (e.g., `calculate_refresh_interval`, `mastodon_api`)
- **Classes:** `PascalCase` (e.g., `ImageBotBase`, `NotificationPolling`)
- **Constants:** `UPPER_SNAKE_CASE` (not extensively used, but follow this pattern)
- **Private methods:** Prefix with underscore if intended for internal use

### Formatting & Structure
- **Indentation:** 4 spaces (no tabs)
- **Line Length:** Generally kept under 100 characters
- **Function Length:** Functions should be focused on single responsibilities
- **Class Organization:** Related functionality grouped into classes (e.g., `ImageBotBase` base class)

### Error Handling
- Use custom exceptions from `bot_exceptions.py`: `NetworkError`, `FileOperationError`, `ConfigurationError`, `APIResponseError`, `LLMError` (all inherit from `MastodonBotError`)
- Wrap API calls and external dependencies in try/except blocks catching these specific exception types
- Log errors via the global `logger` instance (`from logger import logger`) — structured logging to console + rotating file at `logs/app.log`
- Legacy error output writes to `errorlog.txt` directly via inline writes

### File Organization
```
src/
├── main.py              # Main orchestration and notification polling
├── image_bot_base.py    # Core bot class handling image selection and posting logic
├── mastodon_client.py   # Mastodon API interactions (mentions, posting, media)
├── refresh_schedule.py  # Timing and scheduling
├── env_loader.py        # Environment variable management
├── warning_manager.py   # Warning suppression
├── startup_validator.py # Startup configuration validation
├── logger.py            # Structured logging (console + rotating file)
└── bot_exceptions.py    # Custom exception hierarchy
```

### Documentation Patterns
- **Docstrings:** Add them for complex functions and public methods
- **Comments:** Use inline comments for complex logic or important context
- **TODOs:** Mark future improvements with `# TODO - description`

### Environment Variables
- **Mandatory:** `MASTODON_BASE_URL`, `MASTODON_ACCESS_TOKEN`
- **Optional:** `ADMIN_MASTODON_ACCOUNT` (receives dev-mode image DMs and error notifications), `RUN_MODE` (defaults to "dev")

### Key Patterns

**Notification Polling:** A single polling thread checks for @mentions and responds by selecting a random image from the `/images/` directory. In dev mode, the image is sent as a direct message to the admin account; in prod mode, it's posted as a public reply with attachment.

**Error Handling:** Errors are logged via `logger` and written to `errorlog.txt`. If `ADMIN_MASTODON_ACCOUNT` is configured, the admin receives a DM with error details via `post_dm()`.

**Startup Validation:** `startup_validator.validate_all()` is called early in `main.py` to fail fast with clear error messages if required environment variables are missing or invalid.

## Development Notes

- **Dev Mode:** Set `RUN_MODE=dev` to send randomly selected images as DMs to the admin account instead of replying publicly to mentions
- **Image Directory:** Place `.jpg`, `.jpeg`, `.png`, `.gif` files in `/images/` at the project root. The bot randomly selects one for each mention response.
- The bot is image-only — no text posts or message content are generated.

## No Build/Lint/Test Commands

This project does not include automated testing, linting, or build processes. Manual testing is performed by:
1. Running `python src/main.py`
2. Observing console output in dev mode
3. Checking actual posts/DMs in production mode
4. Monitoring `errorlog.txt` for issues

## Key Dependencies

- `mastodon.py` - Mastodon API client
- `requests` - HTTP client (provided by mastodon.py)
- `python-dotenv` - Environment variable management
