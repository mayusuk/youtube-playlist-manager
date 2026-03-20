from pathlib import Path
import argparse

from youtube_playlist_manager.chat_export import parse_chat_export


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compatibility wrapper around the new chat export parser."
    )
    parser.add_argument(
        "chat_export",
        nargs="?",
        default="_chat.txt",
        help="Path to a WhatsApp export .txt or .zip file.",
    )
    parser.add_argument(
        "--output",
        default="video_ids.txt",
        help="Where to write extracted video IDs.",
    )
    args = parser.parse_args()

    result = parse_chat_export(args.chat_export)
    Path(args.output).write_text("\n".join(result.video_ids) + "\n", encoding="utf-8")

    if result.unmatched_urls:
        print("Unmatched URLs:")
        for url in result.unmatched_urls:
            print(url)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
