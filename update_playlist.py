import argparse


def main() -> int:
    from youtube_playlist_manager.youtube_api import (
        build_youtube_service,
        resolve_playlist,
        sync_playlist,
    )

    parser = argparse.ArgumentParser(
        description="Compatibility wrapper around the new playlist sync flow."
    )
    parser.add_argument(
        "--video-ids",
        default="video_ids.txt",
        help="Path to a file containing one YouTube video ID per line.",
    )
    parser.add_argument(
        "--playlist",
        required=True,
        help="Playlist ID, URL, or title.",
    )
    parser.add_argument(
        "--client-secrets",
        required=True,
        help="Path to a Google OAuth client secret JSON file.",
    )
    args = parser.parse_args()

    with open(args.video_ids, "r", encoding="utf-8") as handle:
        video_ids = [line.strip() for line in handle if line.strip()]

    service, _credentials = build_youtube_service(args.client_secrets, persist_tokens=False)
    playlist_id, playlist_title = resolve_playlist(service, args.playlist)
    result = sync_playlist(service, playlist_id, playlist_title, video_ids)

    print(f"Playlist: {result.playlist_title} ({result.playlist_id})")
    print(f"Added: {result.added_count}")
    print(f"Already present: {result.skipped_count}")
    print(f"Invalid or unavailable: {len(result.invalid_video_ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
