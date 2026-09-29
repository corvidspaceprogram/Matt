import argparse
import json
import sys
import urllib.parse

import env_loader
from mastodon import Mastodon
from mastodon.errors import MastodonNotFoundError, MastodonAPIError


def extract_status_id(url):
    """Extract a numeric status ID from a Mastodon URL."""
    parsed = urllib.parse.urlparse(url)
    path_parts = [p for p in parsed.path.split("/") if p]

    if not path_parts:
        return None

    last_part = path_parts[-1]

    # Validate it's numeric (Mastodon IDs are integers)
    if not last_part.isdigit():
        return None

    return last_part


def main():
    parser = argparse.ArgumentParser(
        description="Inspect the structure of a Mastodon status object by URL."
    )
    parser.add_argument("url", help="Mastodon status URL (e.g., https://instance.tld/@user/123456789012345678)")
    args = parser.parse_args()

    # Extract status ID from URL
    status_id = extract_status_id(args.url)
    if status_id is None:
        print(f"Error: Could not extract numeric status ID from URL: {args.url}", file=sys.stderr)
        sys.exit(1)

    print(f"[CheckStatus] Fetching status: {status_id}")
    print(f"[CheckStatus] From URL:   {args.url}")
    print()

    # Load credentials from .env
    env_loader.load_environment_variables()

    mastodon_base_url = env_loader.get_env_variable("MASTODON_BASE_URL")
    mastodon_access_token = env_loader.get_env_variable(
        "MASTODON_ACCESS_TOKEN",
        prompt_message="Enter your Mastodon access token (optional for public statuses): ",
    )

    # Initialize API client
    mastodon_api = Mastodon(access_token=mastodon_access_token, api_base_url=mastodon_base_url)

    # Fetch status
    try:
        status = mastodon_api.status(status_id)
    except MastodonNotFoundError:
        print(f"Error: Status {status_id} not found.", file=sys.stderr)
        sys.exit(1)
    except MastodonAPIError as e:
        print(f"Error: Bad request — {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching status: {e}", file=sys.stderr)
        sys.exit(1)

    # Pretty-print as JSON
    #print(json.dumps(status, indent=2, ensure_ascii=False))
    print(status)


if __name__ == "__main__":
    main()
