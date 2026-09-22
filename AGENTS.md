# AGENTS.md

This file contains guidelines and commands for agentic coding agents working on this Mastodon LLM bot repository.

## Project Overview

This is a Python project that creates an automated Mastodon bot using LLM-generated content. The bot:
- Fetches posts from followers for context
- Generates posts using LLM APIs at random intervals
- Responds to mentions
- Manages follow relationships automatically

## Environment Setup

**Dependencies Installation:**
```bash
pip install requests mastodon.py python-dotenv html_text
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
- **Classes:** `PascalCase` (e.g., `LlmPoster`, `StreamListener`)
- **Constants:** `UPPER_SNAKE_CASE` (not extensively used, but follow this pattern)
- **Private methods:** Prefix with underscore if intended for internal use

### Formatting & Structure
- **Indentation:** 4 spaces (no tabs)
- **Line Length:** Generally kept under 100 characters
- **Function Length:** Functions should be focused on single responsibilities
- **Class Organization:** Related functionality grouped into classes (e.g., `LlmPoster` base class)

### Error Handling
- Use custom exceptions from `bot_exceptions.py`: `NetworkError`, `FileOperationError`, `ConfigurationError`, `APIResponseError`, `LLMError` (all inherit from `MastodonBotError`)
- Wrap API calls and external dependencies in try/except blocks catching these specific exception types
- Log errors via the global `logger` instance (`from logger import logger`) — structured logging to console + rotating file at `logs/app.log`
- Legacy error output still writes to `errorlog.txt` via `warning_handler()` for backward compatibility
- Print errors in dev mode, DM admin account in production

### File Organization
```
src/
├── main.py              # Main orchestration and threading
├── env_loader.py        # Environment variable management
├── mastodon_client.py   # Mastodon API interactions
├── llm_manager.py       # LLM API interactions
├── llm_poster.py        # Base class for posting logic
├── text_cleaner.py      # Text processing utilities
├── refresh_schedule.py  # Timing and scheduling
├── warning_manager.py   # Warning suppression
├── startup_validator.py # Startup configuration validation
├── retry_utils.py       # Retry with exponential backoff decorator
├── logger.py            # Structured logging (console + rotating file)
├── bot_exceptions.py    # Custom exception hierarchy
└── validation_utils.py  # API response validation helpers
```

### Documentation Patterns
- **Docstrings:** Not extensively used, but add them for complex functions
- **Comments:** Use inline comments for complex logic or temporary workarounds
- **TODOs:** Mark future improvements with `# TODO - description`

### Environment Variables
- **Mandatory:** `MASTODON_BASE_URL`, `MASTODON_ACCESS_TOKEN`, `LLM_API_URL`, `LLM_API_KEY`, `LLM_MODEL`, `SYSTEM_PROMPT`, `POSTS_CONTEXT_LENGTH`
- **Optional:** `DESTINATION_MASTODON_CHAR_LIMIT` (defaults to 500), `ADMIN_MASTODON_ACCOUNT`, `RUN_MODE` (defaults to "dev"), `FILTER_KEY_WORDS` (comma-separated keywords to filter posts), `MAX_RETRIES` (default: 3), `RETRY_INITIAL_DELAY` in seconds (default: 1), `RETRY_MAX_DELAY` in seconds (default: 60)

### Key Patterns

**Threading:** Multiple concurrent loops run in separate threads:
- Random poster (6-48 hour intervals)
- Follower refresher (5 minute intervals)
- Notification listener (streaming, fallback to polling)

**Error Recovery:** API failures are caught and handled gracefully:
- Retry mechanisms for file uploads
- Fallback notification polling if streaming fails
- Error logging and admin notifications

**LLM Integration:** Uses OpenAI-compatible API format with file attachments for context management.

**Retry with Backoff:** Functions decorated with `@retry_with_backoff()` from `retry_utils.py` automatically retry on `NetworkError` with exponential backoff (configurable via env vars). Non-network exceptions are not retried.

**Startup Validation:** `startup_validator.validate_all()` is called early in `main.py` to fail fast with clear error messages if required environment variables are missing or invalid.

**API Response Validation:** `validation_utils.py` provides helpers like `validate_json_response()`, `validate_llm_response()`, and `safe_get()` for safe nested data access.

## Development Notes

- **Dev Mode:** Set `RUN_MODE=dev` to print instead of post publicly
- **Admin Notifications:** Configure `ADMIN_MASTODON_ACCOUNT` to receive error DMs
- **Context Management:** Posts are stored in `posts.json`, truncated to respect context limits
- **Character Limits:** Posts are automatically truncated to respect instance limits
- **Special Characters:** LLM outputs are evaluated for ¥...√ delimiters before posting

## No Build/Lint/Test Commands

This project does not include automated testing, linting, or build processes. Manual testing is performed by:
1. Running `python src/main.py`
2. Observing console output in dev mode
3. Checking actual posts in production mode
4. Monitoring `errorlog.txt` for issues

## Key Dependencies

- `mastodon.py` - Mastodon API client
- `requests` - HTTP client for LLM API calls
- `python-dotenv` - Environment variable management
- `html_text` - HTML content extraction and cleaning