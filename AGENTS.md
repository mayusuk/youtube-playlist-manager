# AGENTS.md

## Project Purpose

This repository is now a shareable CLI project for turning YouTube links shared in a WhatsApp export into a YouTube playlist on the user's own account.

The main workflow is:

1. Read a WhatsApp `.txt` or `.zip` export.
2. Extract YouTube video IDs from the shared links.
3. Authenticate the user with their own Google OAuth client.
4. Find or create a target playlist on that user's YouTube account.
5. Add valid videos that are not already in the playlist.

The project still includes the original scripts, but the supported entrypoint is now the installable CLI.

## Repository Layout

- `pyproject.toml`: Package metadata and CLI entrypoint.
- `youtube_playlist_manager/cli.py`: Main CLI interface.
- `youtube_playlist_manager/chat_export.py`: WhatsApp export loading and YouTube URL parsing.
- `youtube_playlist_manager/youtube_api.py`: OAuth, playlist lookup/creation, and sync logic.
- `song_parser.py`: Compatibility wrapper around the new parser.
- `update_playlist.py`: Compatibility wrapper around the new YouTube sync logic.
- `tests/test_chat_export.py`: Parser tests.
- `CHANGELOG.md`: Release notes.
- `README.md`: User-facing setup and usage instructions.

## How The Scripts Work

### 1. Chat Export Parsing

The main parser now accepts either:

- a WhatsApp-exported `.txt`
- a WhatsApp-exported `.zip`

Behavior:

- Loads the text directly from the provided file.
- For ZIP exports, prefers `_chat.txt` when present.
- Extracts all URLs from the text.
- Recognizes YouTube watch links, `youtu.be` short links, and `/shorts/`, `/embed/`, or `/live/` paths.
- Deduplicates video IDs while preserving order.
- Returns unmatched non-YouTube URLs for reporting.
- Builds optional YouTube search candidates for non-YouTube links using inline or nearby chat text.

Important implementation details:

- The parser no longer depends on a hardcoded `_chat.txt`.
- Query parameters on `youtu.be/<id>?...` links are now ignored correctly.
- The project still does not infer songs from plain text messages without URLs.

### 2. YouTube Playlist Sync

The main CLI now handles authentication and playlist sync directly.

Behavior:

- Loads the user's OAuth client secret JSON from `--client-secrets` or `YPM_CLIENT_SECRETS`.
- Uses session-only OAuth by default.
- Revokes the token automatically after the run unless persistent login is explicitly enabled.
- Can cache the OAuth token locally in `~/.config/youtube-playlist-manager/token.json` when `--remember-me` is used.
- Accepts a target playlist as a playlist ID, playlist URL, or playlist title.
- If a title is provided and no matching playlist exists, creates a new playlist on the user's account.
- Reads the current playlist contents to avoid duplicate insertions.
- Validates candidate video IDs against the YouTube Data API before inserting.
- Can optionally search YouTube for non-YouTube links when enough text context exists.
- Optionally writes a JSON sync report.

Important implementation details:

- Playlist targeting is no longer hardcoded.
- Credentials are no longer hardcoded.
- The tool uses the user's own YouTube account and permissions.
- Default token handling is ephemeral at the application level.
- Duplicate avoidance is based on actual playlist contents, not an external text skip-list.

## Expected Runtime Inputs

The shareable CLI expects:

- a WhatsApp export file: `.txt` or `.zip`
- a Google OAuth client secret JSON file for the user running the tool
- a playlist target provided as title, ID, or URL

Optional generated artifacts:

- local OAuth token cache
- optional JSON sync report

## Dependencies

The project now declares its dependencies in `pyproject.toml`. Runtime dependencies are:

- `google-auth-oauthlib`
- `google-api-python-client`

The parser uses only Python standard library modules.

## Data Flow Summary

`chat export (.txt/.zip)` -> parser -> video IDs -> YouTube auth -> playlist lookup/create -> playlist sync

Optional side outputs:

- unmatched URLs printed by the CLI
- invalid or unavailable video IDs printed by the CLI
- optional JSON report written with `--report`

## Current Limitations And Risks

- The project still depends on user-created Google Cloud credentials.
- The parser assumes shared songs come through YouTube URLs, not free-text song names.
- Non-YouTube fallback search is heuristic and may choose the wrong YouTube result.
- Direct reading from personal WhatsApp chat history is not implemented and is not expected to be supported through Meta's official business-focused APIs.
- Only the parser currently has tests.

## Safe Expectations For Future Work

If this project is revived, the first improvements should be:

1. Add tests around playlist resolution and sync logic.
2. Add richer playlist matching when multiple playlists share a title.
3. Support dry-run mode.
4. Improve reporting and logging.
5. Publish the package so users can install it without cloning the repo.
6. Potentially add desktop packaging for non-technical users.

## Practical Summary

This is now a lightweight shareable CLI for:

- reading a WhatsApp export
- extracting YouTube video IDs robustly
- syncing those videos into a user-selected playlist on the user's own account

The original one-off scripts are preserved as wrappers, but the maintained path is the packaged CLI.
