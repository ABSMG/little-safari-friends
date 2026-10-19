#!/usr/bin/env python3
"""Upload a validated episode privately using YouTube OAuth credentials.

This uploader always uses privacyStatus="private". It intentionally does not
support public publishing; review the video in YouTube Studio before changing
any publishing policy.
"""

import json
import os
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    episode_path = ROOT / "episode.json"
    episode = json.loads(episode_path.read_text(encoding="utf-8"))

    default_video = ROOT / "output" / f"{episode['episode_id']}.mp4"
    video = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else default_video
    if not video.is_absolute():
        video = (Path.cwd() / video).resolve()

    if not video.is_file() or video.stat().st_size == 0:
        raise FileNotFoundError(f"Video not found or empty: {video}")

    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print("YouTube secrets missing. Upload skipped; use the workflow artifact.")
        return

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    credentials.refresh(Request())

    youtube = build(
        "youtube",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )

    title = str(episode.get("title", "Little Safari Friends"))[:100]
    description = str(episode.get("description", "")).strip()
    theme = str(episode.get("theme", "animal story")).strip()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description[:5000],
                "tags": [
                    "Little Safari Friends",
                    "kids story",
                    "animal stories",
                    theme[:100],
                ],
                "categoryId": "1",
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en",
            },
            "status": {
                "privacyStatus": "private",
                "selfDeclaredMadeForKids": True,
            },
        },
        media_body=MediaFileUpload(
            str(video),
            chunksize=8 * 1024 * 1024,
            resumable=True,
        ),
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    print("Video uploaded privately. Video ID:", response.get("id"))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Private YouTube upload failed: {error}", file=sys.stderr)
        raise SystemExit(1)
