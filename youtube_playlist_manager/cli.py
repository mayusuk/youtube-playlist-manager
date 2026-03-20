from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import os
import sys

from youtube_playlist_manager.chat_export import parse_chat_export


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="youtube-playlist-manager",
        description="Sync songs shared in a WhatsApp export into a YouTube playlist.",
    )
    parser.add_argument(
        "--chat-export",
        required=True,
        help="Path to a WhatsApp-exported .txt or .zip file.",
    )
    parser.add_argument(
        "--playlist",
        required=True,
        help="Playlist ID, playlist URL, or playlist title. Missing titles are created.",
    )
    parser.add_argument(
        "--client-secrets",
        default=os.environ.get("YPM_CLIENT_SECRETS"),
        help="Path to your Google OAuth client secret JSON. Can also be set with YPM_CLIENT_SECRETS.",
    )
    parser.add_argument(
        "--token-cache",
        default=os.environ.get(
            "YPM_TOKEN_CACHE",
            "~/.config/youtube-playlist-manager/token.json",
        ),
        help="Where to cache the user's OAuth token when --remember-me is enabled.",
    )
    parser.add_argument(
        "--remember-me",
        action="store_true",
        help="Persist the OAuth token for future runs. By default the login is session-only.",
    )
    parser.add_argument(
        "--privacy-status",
        choices=["private", "unlisted", "public"],
        default="private",
        help="Privacy for a newly created playlist. Ignored for existing playlists.",
    )
    parser.add_argument(
        "--report",
        help="Optional path to write a JSON sync report.",
    )
    parser.add_argument(
        "--search-non-youtube",
        action="store_true",
        help="Search YouTube for non-YouTube links using nearby chat text.",
    )
    parser.add_argument(
        "--max-search-candidates",
        type=int,
        default=10,
        help="Maximum number of non-YouTube chat items to search on YouTube.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.client_secrets:
        parser.error("--client-secrets is required unless YPM_CLIENT_SECRETS is set.")

    try:
        from googleapiclient.errors import HttpError
        from youtube_playlist_manager.youtube_api import (
            build_youtube_service,
            format_http_error,
            resolve_playlist,
            revoke_credentials,
            SearchMatch,
            search_video,
            sync_playlist,
            write_sync_report,
        )
    except ModuleNotFoundError as error:
        print(
            "Missing dependency. Install the project first with `pip install -e .`.",
            file=sys.stderr,
        )
        print(f"Import error: {error}", file=sys.stderr)
        return 1

    credentials = None
    try:
        parse_result = parse_chat_export(args.chat_export)
        service, credentials = build_youtube_service(
            args.client_secrets,
            os.path.expanduser(args.token_cache),
            persist_tokens=args.remember_me,
        )
        search_matches: list[SearchMatch] = []
        seen_video_ids = set(parse_result.video_ids)
        if args.search_non_youtube:
            for candidate in parse_result.search_candidates[: max(args.max_search_candidates, 0)]:
                match = search_video(service, candidate.query)
                if not match:
                    continue
                match.source_url = candidate.source_url
                match.source_text = candidate.source_text
                if match.video_id not in seen_video_ids:
                    parse_result.video_ids.append(match.video_id)
                    seen_video_ids.add(match.video_id)
                search_matches.append(match)

        playlist_id, playlist_title = resolve_playlist(
            service,
            args.playlist,
            privacy_status=args.privacy_status,
        )
        sync_result = sync_playlist(
            service,
            playlist_id=playlist_id,
            playlist_title=playlist_title,
            video_ids=parse_result.video_ids,
        )
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except HttpError as error:
        print(f"YouTube API error: {format_http_error(error)}", file=sys.stderr)
        return 1
    finally:
        if credentials is not None and not args.remember_me:
            revoke_credentials(credentials)

    print(f"Playlist: {sync_result.playlist_title} ({sync_result.playlist_id})")
    print(f"Video IDs found: {sync_result.requested_count}")
    print(f"Added: {sync_result.added_count}")
    print(f"Already present: {sync_result.skipped_count}")
    print(f"Invalid or unavailable: {len(sync_result.invalid_video_ids)}")
    print(f"Unmatched URLs: {len(parse_result.unmatched_urls)}")
    print(f"Search matches: {len(search_matches)}")

    if sync_result.invalid_video_ids:
        print("Invalid IDs:")
        for video_id in sync_result.invalid_video_ids:
            print(f"  {video_id}")

    if parse_result.unmatched_urls:
        print("Unmatched URLs:")
        for url in parse_result.unmatched_urls:
            print(f"  {url}")

    if search_matches:
        print("Search matches:")
        for match in search_matches:
            print(f"  {match.query} -> {match.title} [{match.video_id}]")

    if args.report:
        write_sync_report(
            args.report,
            sync_result,
            parse_result.unmatched_urls,
            search_matches,
        )
        print(f"Report written to: {Path(args.report)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
