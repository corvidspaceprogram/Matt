# AGENTS.md

This file contains guidelines and commands for agentic coding agents working on this Mastodon Image Reply Bot repository.

## Project Overview

This is a Python project that creates an automated Mastodon bot responding to @mentions with randomly selected images. In development mode (`RUN_MODE=dev`), images are sent as direct messages to a specified admin account instead of being posted publicly. The bot runs two background threads: `NotificationPolling` (polls @mentions every 10 seconds) and `GreatReactor` (scans the local timeline for `:great:` reactions).

## Environment Setup

**Dependencies Installation:**
```bash
pip install mastodon.py python-dotenv
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

**No formal test framework is configured** — Manual testing is done by running the main application and observing behavior in dev mode.

## Code Style Guidelines

### Import Organization
- Standard library imports first (os, time, datetime, random, threading, etc.)
- Third-party imports second (mastodon, dotenv)
- Local imports last (env_loader, mastodon_client, image_bot_base, etc.)
- One import per line preferred

### Naming Conventions
- **Variables/Functions:** `snake_case` (e.g., `sleep_until_shutdown`, `mastodon_api`)
- **Classes:** `PascalCase` (e.g., `ImageBotBase`, `NotificationPolling`, `GreatReactor`)
- **Constants:** `UPPER_SNAKE_CASE` (not extensively used, but follow this pattern)
- **Private methods:** Prefix with underscore if intended for internal use

### Formatting & Structure
- **Indentation:** 4 spaces (no tabs)
- **Line Length:** Generally kept under 100 characters
- **Function Length:** Functions should be focused on single responsibilities
- **Class Organization:** Related functionality grouped into classes (e.g., `ImageBotBase` base class)

### Error Handling
- Use custom exceptions from `bot_exceptions.py`: `NetworkError`, `FileOperationError`, `ConfigurationError`, `APIResponseError` (all inherit from `MastodonBotError`)
- Wrap API calls and external dependencies in try/except blocks catching these specific exception types
- Log errors via the global `logger` instance (`from logger import logger`) — structured logging to console + rotating file at `logs/app.log`
- Legacy error output writes to `errorlog.txt` directly via inline writes

### File Organization
```
src/
├── main.py              # Main orchestration: NotificationPolling + GreatReactor threads
├── image_bot_base.py    # Core bot class handling image selection and posting logic
├── mastodon_client.py   # Mastodon API interactions (mentions, posting, media)
├── env_loader.py        # Environment variable management
├── warning_manager.py   # Warning suppression
├── startup_validator.py # Startup configuration validation
├── logger.py            # Structured logging (console + rotating file)
├── bot_exceptions.py    # Custom exception hierarchy
└── check_status.py      # Helper script for inspecting Mastodon status objects by URL
```

### Documentation Patterns
- **Docstrings:** Add them for complex functions and public methods
- **Comments:** Use inline comments for complex logic or important context
- **TODOs:** Mark future improvements with `# TODO - description`

### Environment Variables
- **Mandatory:** `MASTODON_BASE_URL`, `MASTODON_ACCESS_TOKEN`
- **Optional:**
  - `ADMIN_MASTODON_ACCOUNT` — receives dev-mode image DMs and error notifications
  - `RUN_MODE` — `"dev"` (default) or `"prod"`
  - `TIMELINE_HOURS` — GreatReactor time cutoff in hours (default: 24)

### Key Patterns

**Notification Polling:** `NotificationPolling` thread checks for @mentions every 10 seconds and responds by selecting a random image from the `/images/` directory. In dev mode, the image is sent as a direct message to the admin account; in prod mode, it's posted as a public reply with attachment.

**Timeline Reactor:** `GreatReactor` thread (subclasses `ImageBotBase`) polls the local timeline every hour for posts containing a `:great:` custom reaction. It deduplicates by checking if the bot already replied directly to that status. In dev mode, the admin receives a DM with the post URL and an attached image; in prod mode, it posts a public reply.

**Error Handling:** Errors are logged via `logger` and written to `errorlog.txt`. If `ADMIN_MASTODON_ACCOUNT` is configured, the admin receives a DM with error details via `post_dm()`.

**Startup Validation:** `startup_validator.validate_all()` is called early in `main.py` to fail fast with clear error messages if required environment variables are missing or invalid.

## Development Notes

- **Dev Mode:** Set `RUN_MODE=dev` to send randomly selected images as DMs to the admin account instead of replying publicly
- **GreatReactor Dev Mode DMs:** Include the reacted-to post URL and a message like "Great reaction found on: {post_url}\nImage attached below."
- **Image Directory:** Place `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp` files in `/images/` at the project root. The bot randomly selects one for each mention/reaction response.
- The bot is image-only — no text posts or message content are generated (except GreatReactor dev-mode DMs).

## No Build/Lint/Test Commands

This project does not include automated testing, linting, or build processes. Manual testing is performed by:
1. Running `python src/main.py`
2. Observing console output in dev mode
3. Checking actual posts/DMs in production mode
4. Monitoring `errorlog.txt` for issues

## Key Dependencies

- `mastodon.py` — Mastodon API client
- `python-dotenv` — Environment variable management
