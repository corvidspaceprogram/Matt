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
- Use `try/except` blocks for API calls and external dependencies
- Log errors to `errorlog.txt` using the `handle_error()` method in `LlmPoster`
- Print errors in dev mode, DM admin account in production
- Specific error messages should be descriptive

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
└── warning_manager.py  # Warning suppression
```

### Documentation Patterns
- **Docstrings:** Not extensively used, but add them for complex functions
- **Comments:** Use inline comments for complex logic or temporary workarounds
- **TODOs:** Mark future improvements with `# TODO - description`

### Environment Variables
- **Mandatory:** `MASTODON_BASE_URL`, `MASTODON_ACCESS_TOKEN`, `LLM_API_URL`, `LLM_API_KEY`, `LLM_MODEL`, `SYSTEM_PROMPT`, `MAX_CONTEXT_LENGTH`
- **Optional:** `DESTINATION_MASTODON_CHAR_LIMIT` (defaults to 500), `ADMIN_MASTODON_ACCOUNT`, `RUN_MODE` (defaults to "dev")

### Key Patterns

**Threading:** Multiple concurrent loops run in separate threads:
- Posts summary refresher (hourly)
- Random poster (6-48 hour intervals)
- Follower refresher (5 minute intervals)
- Notification listener (streaming, fallback to polling)

**Error Recovery:** API failures are caught and handled gracefully:
- Retry mechanisms for file uploads
- Fallback notification polling if streaming fails
- Error logging and admin notifications

**LLM Integration:** Uses OpenAI-compatible API format with file attachments for context management.

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