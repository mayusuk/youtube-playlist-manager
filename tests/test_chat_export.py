import unittest

from youtube_playlist_manager.chat_export import (
    derive_neighbor_query,
    derive_search_query,
    extract_video_id,
    parse_chat_text,
)


class ChatExportTests(unittest.TestCase):
    def test_parse_chat_text_extracts_unique_video_ids(self):
        text = """
        3/20/24, 8:01 PM - Friend: https://www.youtube.com/watch?v=dFaKxBz1reQ&feature=shared
        3/20/24, 8:02 PM - Me: https://youtu.be/NqvlLQHZQgw?si=abc123
        3/20/24, 8:03 PM - Friend: https://www.youtube.com/shorts/MgkQe9IHA_c?feature=share
        3/20/24, 8:04 PM - Me: https://youtu.be/NqvlLQHZQgw?si=abc123
        """
        result = parse_chat_text(text)

        self.assertEqual(
            result.video_ids,
            ["dFaKxBz1reQ", "NqvlLQHZQgw", "MgkQe9IHA_c"],
        )
        self.assertEqual(result.unmatched_urls, [])

    def test_parse_chat_text_reports_non_youtube_urls(self):
        text = "https://example.com/test"
        result = parse_chat_text(text)

        self.assertEqual(result.video_ids, [])
        self.assertEqual(result.unmatched_urls, ["https://example.com/test"])
        self.assertEqual(result.search_candidates, [])

    def test_parse_chat_text_creates_search_candidates_for_non_youtube_links(self):
        text = """
        3/20/24, 8:00 PM - Friend: Kun Faya Kun
        3/20/24, 8:01 PM - Friend: https://open.spotify.com/track/example
        """
        result = parse_chat_text(text)

        self.assertEqual(result.video_ids, [])
        self.assertEqual(result.unmatched_urls, ["https://open.spotify.com/track/example"])
        self.assertEqual(len(result.search_candidates), 1)
        self.assertEqual(result.search_candidates[0].query, "Kun Faya Kun")

    def test_extract_video_id_from_supported_youtube_formats(self):
        self.assertEqual(
            extract_video_id("https://www.youtube.com/watch?v=abc123xyz00"),
            "abc123xyz00",
        )
        self.assertEqual(
            extract_video_id("https://youtu.be/abc123xyz00?si=share-token"),
            "abc123xyz00",
        )
        self.assertEqual(
            extract_video_id("https://www.youtube.com/shorts/abc123xyz00?feature=share"),
            "abc123xyz00",
        )

    def test_derive_search_query_uses_inline_text(self):
        line = "3/20/24, 8:01 PM - Friend: Namo Namo https://open.spotify.com/track/example"
        self.assertEqual(
            derive_search_query(line, ["https://open.spotify.com/track/example"]),
            "Namo Namo",
        )

    def test_derive_neighbor_query_uses_previous_non_url_line(self):
        lines = [
            "3/20/24, 8:00 PM - Friend: Chaleya",
            "3/20/24, 8:01 PM - Friend: https://music.apple.com/example",
        ]
        self.assertEqual(derive_neighbor_query(lines, 1), "Chaleya")


if __name__ == "__main__":
    unittest.main()
