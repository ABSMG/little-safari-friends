#!/usr/bin/env python3
"""Upload a video privately using YouTube OAuth credentials."""

import os
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload"
]


def main():
    video = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "output/leo_learns_to_share.mp4"
    )

    if not video.is_file():
        raise FileNotFoundError(
            f"Video not found: {video}"
        )

    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")

    if not all([
        client_id,
        client_secret,
        refresh_token
    ]):
        print(
            "YouTube secrets missing. "
            "Upload skipped; download the workflow artifact."
        )
        return

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )

    credentials.refresh(Request())

    youtube = build(
        "youtube",
        "v3",
        credentials=credentials,
        cache_discovery=False
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": (
                    "Leo Learns to Share | "
                    "Little Safari Friends"
                ),
                "description": (
                    "Leo the little lion learns that sharing "
                    "makes playtime happier. A gentle original "
                    "safari story for young children.\n\n"
                    "#LittleSafariFriends "
                    "#KidsStories #Sharing"
                ),
                "tags": [
                    "Little Safari Friends",
                    "kids story",
                    "sharing",
                    "safari animals"
                ],
                "categoryId": "1",
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en"
            },
            "status": {
                "privacyStatus": "private",
                "selfDeclaredMadeForKids": True
            }
        },
        media_body=MediaFileUpload(
            str(video),
            chunksize=8 * 1024 * 1024,
            resumable=True
        )
    )

    response = None

    while response is None:
        status, response = request.next_chunk()

        if status:
            progress = int(status.progress() * 100)
            print(f"Upload progress: {progress}%")

    print(
        "Video uploaded privately. Video ID:",
        response.get("id")
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(
            f"YouTube upload failed: {error}",
            file=sys.stderr
        )
        raise SystemExit(1)
