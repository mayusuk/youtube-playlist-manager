from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs, urlparse
import re
import zipfile


URL_PATTERN = re.compile(r"https?://\S+")
SUPPORTED_TEXT_EXTENSIONS = {".txt"}
WHATSAPP_PREFIX_PATTERN = re.compile(
    r"^\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4},\s+\d{1,2}:\d{2}(?:\s?[APMapm]{2})?\s+-\s+"
)


@dataclass
class SearchCandidate:
    query: str
    source_url: str
    source_text: str


@dataclass
class ParsedUrl:
    url: str
    video_id: str | None
    query: str | None
    source_text: str


@dataclass
class ParseResult:
    video_ids: list[str]
    unmatched_urls: list[str]
    search_candidates: list[SearchCandidate]


def load_chat_text(chat_export_path: str | Path) -> str:
    path = Path(chat_export_path)
    if not path.exists():
        raise FileNotFoundError(f"Chat export not found: {path}")

    if path.suffix.lower() == ".zip":
        return _read_chat_from_zip(path)

    if path.suffix.lower() not in SUPPORTED_TEXT_EXTENSIONS:
        raise ValueError(
            f"Unsupported chat export format: {path.suffix}. Use a .txt or .zip export."
        )

    return path.read_text(encoding="utf-8", errors="replace")


def parse_chat_export(chat_export_path: str | Path) -> ParseResult:
    text = load_chat_text(chat_export_path)
    return parse_chat_text(text)


def parse_chat_text(text: str) -> ParseResult:
    video_ids: list[str] = []
    unmatched_urls: list[str] = []
    search_candidates: list[SearchCandidate] = []
    seen: set[str] = set()

    for parsed_url in extract_urls_with_context(text):
        if parsed_url.video_id is None:
            unmatched_urls.append(parsed_url.url)
            if parsed_url.query:
                search_candidates.append(
                    SearchCandidate(
                        query=parsed_url.query,
                        source_url=parsed_url.url,
                        source_text=parsed_url.source_text,
                    )
                )
            continue

        if parsed_url.video_id not in seen:
            seen.add(parsed_url.video_id)
            video_ids.append(parsed_url.video_id)

    return ParseResult(
        video_ids=video_ids,
        unmatched_urls=unmatched_urls,
        search_candidates=search_candidates,
    )


def extract_urls(text: str) -> Iterable[str]:
    for match in URL_PATTERN.finditer(text):
        yield match.group(0).rstrip(").,]}>\"'")


def extract_urls_with_context(text: str) -> Iterable[ParsedUrl]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        urls = list(extract_urls(line))
        if not urls:
            continue

        inline_query = derive_search_query(line, urls)
        neighbor_query = derive_neighbor_query(lines, index)
        query = inline_query or neighbor_query
        source_text = normalize_message_text(line)

        for url in urls:
            yield ParsedUrl(
                url=url,
                video_id=extract_video_id(url),
                query=query,
                source_text=source_text,
            )


def extract_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]

    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
        return video_id or None

    if host not in {"youtube.com", "m.youtube.com", "music.youtube.com"}:
        return None

    if parsed.path == "/watch":
        return _first_query_value(parsed.query, "v")

    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) >= 2 and path_parts[0] in {"shorts", "embed", "live"}:
        return path_parts[1]

    return None


def _first_query_value(query: str, key: str) -> str | None:
    values = parse_qs(query).get(key, [])
    if not values:
        return None
    return values[0] or None


def _read_chat_from_zip(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        text_entries = [
            name
            for name in archive.namelist()
            if Path(name).suffix.lower() in SUPPORTED_TEXT_EXTENSIONS
        ]
        if not text_entries:
            raise ValueError("ZIP export does not contain a .txt chat file.")

        preferred_name = next(
            (name for name in text_entries if Path(name).name.lower() == "_chat.txt"),
            text_entries[0],
        )
        with archive.open(preferred_name) as handle:
            return handle.read().decode("utf-8", errors="replace")


def derive_search_query(line: str, urls: list[str]) -> str | None:
    cleaned = normalize_message_text(line)
    for url in urls:
        cleaned = cleaned.replace(url, " ")
    return _normalize_query(cleaned)


def derive_neighbor_query(lines: list[str], index: int) -> str | None:
    for offset in (1, 2):
        previous_index = index - offset
        if previous_index < 0:
            break

        previous_line = lines[previous_index]
        if list(extract_urls(previous_line)):
            continue

        query = _normalize_query(normalize_message_text(previous_line))
        if query:
            return query
    return None


def normalize_message_text(line: str) -> str:
    normalized = WHATSAPP_PREFIX_PATTERN.sub("", line).strip()
    if ": " in normalized:
        normalized = normalized.split(": ", 1)[1]
    return normalized.strip()


def _normalize_query(text: str) -> str | None:
    collapsed = re.sub(r"\s+", " ", text).strip(" -")
    if len(collapsed) < 3:
        return None
    return collapsed
