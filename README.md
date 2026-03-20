# youtube-playlist-manager

`youtube-playlist-manager` turns a WhatsApp chat export into a YouTube playlist on the user's own account.

It is designed to be shareable:

- no hardcoded playlist IDs
- no hardcoded credential filenames
- accepts WhatsApp `.txt` or `.zip` exports directly
- uses the user's own Google OAuth credentials
- can target an existing playlist or create one by name
- can optionally search YouTube for songs shared as non-YouTube links
- uses session-only OAuth by default

## What It Does

1. Reads a WhatsApp-exported chat file.
2. Extracts YouTube video IDs from shared links.
3. Authenticates the user with YouTube Data API v3.
4. Finds or creates the target playlist.
5. Adds only valid videos that are not already present.

## Installation

From source:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

For a released package, the intended end-user install will be:

```bash
pip install youtube-playlist-manager
```

As of March 20, 2026, the exact PyPI name `youtube-playlist-manager` appeared available when checked against the PyPI JSON endpoint.

## Google Setup

Create an OAuth client for a desktop app and enable the YouTube Data API v3 for your Google Cloud project.

Official docs:

- https://developers.google.com/youtube/registering_an_application

Then download the OAuth client secret JSON and keep it on your machine. The tool does not ship shared credentials.

Recommended local layout:

```text
credentials/client_secret.json
```

The repo ignores `credentials/`, `.venv/`, token caches, and common OAuth JSON filenames so secrets stay local.

## Usage

Minimal usage:

```bash
youtube-playlist-manager \
  --chat-export /path/to/whatsapp-export.zip \
  --playlist "Road Trip Songs" \
  --client-secrets /path/to/client_secret.json
```

By default this is a session-only login:

- the tool opens the browser for consent
- uses the token for that run
- revokes the token when the run finishes
- does not persist an OAuth token locally

The `--playlist` value can be:

- a playlist title
- a playlist ID
- a full YouTube playlist URL

If you pass a title and no matching playlist exists, the tool creates it on your account.

Optional report:

```bash
youtube-playlist-manager \
  --chat-export /path/to/_chat.txt \
  --playlist "Shared Songs" \
  --client-secrets /path/to/client_secret.json \
  --report sync.report.json
```

Using an environment variable instead of repeating the client secret path:

```bash
export YPM_CLIENT_SECRETS=credentials/client_secret.json
youtube-playlist-manager \
  --chat-export /path/to/_chat.txt \
  --playlist "Shared Songs"
```

If a user wants convenience over strict session-only behavior, they can opt in:

```bash
youtube-playlist-manager \
  --chat-export /path/to/_chat.txt \
  --playlist "Shared Songs" \
  --client-secrets credentials/client_secret.json \
  --remember-me
```

With `--remember-me`, the OAuth token is cached locally and reused on future runs.

## OAuth Behavior

Default behavior:

- session-only login
- no token cache written
- token revoked automatically after the run

Optional persistent behavior:

- enable `--remember-me`
- token cached at `~/.config/youtube-playlist-manager/token.json`
- cache path can be overridden with `--token-cache`

When persistent login is enabled, the token cache file is written with owner-only permissions where supported.

## Security Notes

- Users should supply their own Google OAuth client JSON.
- Client secret files must stay out of source control.
- Session-only auth is the recommended default for shared usage because it avoids long-lived refresh-token storage.
- Persistent login is a convenience feature and should be treated as a deliberate trust decision by the user.

## Distribution

This repository is now structured as a Python package with a CLI entrypoint:

```bash
youtube-playlist-manager --help
```

To build distributable artifacts locally:

```bash
python -m build
```

That produces:

- a source distribution in `dist/`
- a wheel in `dist/`

Those artifacts can be shared directly or published to a package index later.

## Next Improvement

The next security improvement should be replacing file-based persistent token storage with OS-native secure storage:

- macOS Keychain
- Windows Credential Manager
- Linux Secret Service

Session-only auth already avoids long-lived token storage by default, so this is specifically for strengthening the opt-in `--remember-me` path.

## Why The Tool Uses Chat Exports

This project does not read personal WhatsApp chats directly from WhatsApp.

Reason:

- Meta's official WhatsApp APIs are for WhatsApp Business Platform use cases, business phone numbers, and webhook-based messaging workflows, not for pulling personal chat history from a user's account.
- For a general-purpose shareable tool, exported chat files are the practical and supportable input format.

So the supported workflow is:

1. Export a WhatsApp chat.
2. Run the CLI against the exported `.txt` or `.zip`.
3. Let the tool sync videos into your playlist.

## Non-YouTube Links

Chats often contain songs from Spotify, Apple Music, SoundCloud, or Instagram instead of direct YouTube URLs.

The CLI supports an opt-in fallback:

```bash
youtube-playlist-manager \
  --chat-export /path/to/_chat.txt \
  --playlist "Shared Songs" \
  --client-secrets credentials/client_secret.json \
  --search-non-youtube
```

How it works:

- If a line has a non-YouTube URL and also contains text like a song title, that text becomes the YouTube search query.
- If the URL-only line has no text, the tool looks at the previous one or two non-link lines for context.
- It then searches YouTube and takes the top video result.

Important tradeoffs:

- This is heuristic, not exact.
- The best result depends on the quality of the chat text.
- Review the reported matches if you care about precision.
- YouTube search calls are much more quota-expensive than direct video inserts, so this mode should stay optional.

## CLI Entry Point

The supported entrypoint is the CLI:

```bash
python -m youtube_playlist_manager --help
```
