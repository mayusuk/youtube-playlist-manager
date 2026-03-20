from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs, urlparse
import json
import os
import time
import urllib.parse
import urllib.request

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
DEFAULT_TOKEN_PATH = Path.home() / ".config" / "youtube-playlist-manager" / "token.json"


@dataclass
class SearchMatch:
    query: str
    source_url: str
    source_text: str
    video_id: str
    title: str
    channel_title: str


@dataclass
class SyncResult:
    playlist_id: str
    playlist_title: str
    requested_count: int
    existing_count: int
    added_count: int
    skipped_count: int
    invalid_video_ids: list[str]


def build_youtube_service(
    client_secrets_path: str | Path,
    token_path: str | Path | None = None,
    persist_tokens: bool = False,
):
    token_file = Path(token_path or DEFAULT_TOKEN_PATH)
    if persist_tokens:
        token_file.parent.mkdir(parents=True, exist_ok=True)

    credentials = _load_credentials(
        client_secrets_path,
        token_file,
        persist_tokens=persist_tokens,
    )
    return build("youtube", "v3", credentials=credentials, num_retries=3), credentials


def resolve_playlist(service, playlist_value: str, privacy_status: str = "private") -> tuple[str, str]:
    playlist_id = extract_playlist_id(playlist_value)
    if playlist_id:
        title = get_playlist_title(service, playlist_id)
        return playlist_id, title

    matched = find_playlist_by_title(service, playlist_value)
    if matched:
        return matched

    return create_playlist(service, playlist_value, privacy_status=privacy_status)


def sync_playlist(service, playlist_id: str, playlist_title: str, video_ids: list[str]) -> SyncResult:
    existing_video_ids = get_playlist_video_ids(service, playlist_id)
    valid_video_ids = get_existing_video_ids(service, video_ids)

    added_count = 0
    skipped_count = 0
    invalid_video_ids: list[str] = []

    for video_id in video_ids:
        if video_id not in valid_video_ids:
            invalid_video_ids.append(video_id)
            continue

        if video_id in existing_video_ids:
            skipped_count += 1
            continue

        add_video_to_playlist(service, playlist_id, video_id)
        existing_video_ids.add(video_id)
        added_count += 1

    return SyncResult(
        playlist_id=playlist_id,
        playlist_title=playlist_title,
        requested_count=len(video_ids),
        existing_count=len(existing_video_ids),
        added_count=added_count,
        skipped_count=skipped_count,
        invalid_video_ids=invalid_video_ids,
    )


def extract_playlist_id(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc:
        playlist_values = parse_qs(parsed.query).get("list", [])
        if playlist_values:
            return playlist_values[0]
        return None

    normalized = value.strip()
    if " " in normalized:
        return None

    if normalized.startswith(("PL", "UU", "LL", "RD", "OLAK5uy_")):
        return normalized

    return None


def get_playlist_title(service, playlist_id: str) -> str:
    response = service.playlists().list(part="snippet", id=playlist_id).execute()
    items = response.get("items", [])
    if not items:
        raise ValueError(f"Playlist not found or not accessible: {playlist_id}")
    return items[0]["snippet"]["title"]


def find_playlist_by_title(service, title: str) -> tuple[str, str] | None:
    page_token = None
    while True:
        response = (
            service.playlists()
            .list(part="snippet", mine=True, maxResults=50, pageToken=page_token)
            .execute()
        )
        for item in response.get("items", []):
            if item["snippet"]["title"] == title:
                return item["id"], item["snippet"]["title"]

        page_token = response.get("nextPageToken")
        if not page_token:
            return None


def create_playlist(service, title: str, privacy_status: str = "private") -> tuple[str, str]:
    response = (
        service.playlists()
        .insert(
            part="snippet,status",
            body={
                "snippet": {"title": title},
                "status": {"privacyStatus": privacy_status},
            },
        )
        .execute()
    )
    playlist_id = response["id"]
    _wait_for_playlist_availability(service, playlist_id)
    return playlist_id, response["snippet"]["title"]


def get_playlist_video_ids(service, playlist_id: str) -> set[str]:
    video_ids: set[str] = set()
    page_token = None
    while True:
        response = (
            service.playlistItems()
            .list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=page_token,
            )
            .execute()
        )
        for item in response.get("items", []):
            video_id = item.get("contentDetails", {}).get("videoId")
            if video_id:
                video_ids.add(video_id)

        page_token = response.get("nextPageToken")
        if not page_token:
            return video_ids


def get_existing_video_ids(service, video_ids: Iterable[str]) -> set[str]:
    valid_video_ids: set[str] = set()
    video_id_list = list(video_ids)
    for start in range(0, len(video_id_list), 50):
        chunk = video_id_list[start : start + 50]
        response = service.videos().list(part="id,status", id=",".join(chunk)).execute()
        for item in response.get("items", []):
            if item.get("status", {}).get("privacyStatus") == "private":
                continue
            valid_video_ids.add(item["id"])
    return valid_video_ids


def add_video_to_playlist(service, playlist_id: str, video_id: str) -> None:
    (
        service.playlistItems()
        .insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id,
                    },
                }
            },
        )
        .execute()
    )


def search_video(service, query: str) -> SearchMatch | None:
    response = (
        service.search()
        .list(
            part="snippet",
            q=query,
            type="video",
            maxResults=1,
        )
        .execute()
    )
    items = response.get("items", [])
    if not items:
        return None

    item = items[0]
    return SearchMatch(
        query=query,
        source_url="",
        source_text="",
        video_id=item["id"]["videoId"],
        title=item["snippet"]["title"],
        channel_title=item["snippet"]["channelTitle"],
    )


def write_sync_report(
    path: str | Path,
    result: SyncResult,
    unmatched_urls: list[str],
    search_matches: list[SearchMatch] | None = None,
) -> None:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "playlist_id": result.playlist_id,
                "playlist_title": result.playlist_title,
                "requested_count": result.requested_count,
                "existing_count": result.existing_count,
                "added_count": result.added_count,
                "skipped_count": result.skipped_count,
                "invalid_video_ids": result.invalid_video_ids,
                "unmatched_urls": unmatched_urls,
                "search_matches": [
                    {
                        "query": match.query,
                        "source_url": match.source_url,
                        "source_text": match.source_text,
                        "video_id": match.video_id,
                        "title": match.title,
                        "channel_title": match.channel_title,
                    }
                    for match in (search_matches or [])
                ],
            },
            indent=2,
        )
        + os.linesep,
        encoding="utf-8",
    )


def _load_credentials(
    client_secrets_path: str | Path,
    token_file: Path,
    persist_tokens: bool,
) -> Credentials:
    credentials = None
    if persist_tokens and token_file.exists():
        credentials = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if credentials and credentials.valid:
        return credentials

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        if persist_tokens:
            _write_token_file(token_file, credentials.to_json())
        return credentials

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets_path), SCOPES)
    credentials = flow.run_local_server(port=0)
    if persist_tokens:
        _write_token_file(token_file, credentials.to_json())
    return credentials


def format_http_error(error: HttpError) -> str:
    return getattr(error, "reason", str(error))


def revoke_credentials(credentials: Credentials) -> None:
    token_to_revoke = credentials.refresh_token or credentials.token
    if not token_to_revoke:
        return

    request = urllib.request.Request(
        "https://oauth2.googleapis.com/revoke",
        data=urllib.parse.urlencode({"token": token_to_revoke}).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10):
            pass
    except Exception:
        return


def _wait_for_playlist_availability(service, playlist_id: str, attempts: int = 5) -> None:
    for attempt in range(attempts):
        try:
            service.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=1,
            ).execute()
            return
        except HttpError:
            if attempt == attempts - 1:
                raise
            time.sleep(1 + attempt)


def _write_token_file(token_file: Path, content: str) -> None:
    token_file.write_text(content, encoding="utf-8")
    try:
        os.chmod(token_file, 0o600)
    except OSError:
        return
