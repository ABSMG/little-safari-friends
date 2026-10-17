#!/usr/bin/env python3
"""Upload generated episode metadata and MP4 to YouTube."""
import json, os, sys
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/upload_youtube.py path/to/video.mp4")
    video = Path(sys.argv[1])
    if not video.is_file():
        raise FileNotFoundError(f"Video not found: {video}")
    episode = json.loads((ROOT / "episode.json").read_text(encoding="utf-8"))
    client_id, secret, refresh = (os.getenv(k) for k in
        ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"))
    if not all((client_id, secret, refresh)):
        raise RuntimeError("YouTube OAuth secrets are missing; upload aborted.")
    creds = Credentials(token=None, refresh_token=refresh,
        token_uri="https://oauth2.googleapis.com/token", client_id=client_id,
        client_secret=secret, scopes=SCOPES)
    creds.refresh(Request())
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
    request = youtube.videos().insert(part="snippet,status", body={
      "snippet": {
        "title": episode.get("title", "Little Safari Friends — New Story")[:100],
        "description": episode.get("description", "An original safari story.")[:5000],
        "tags": ["Little Safari Friends", "kids stories", "animal stories", "preschool stories"],
        "categoryId": "1", "defaultLanguage": "en", "defaultAudioLanguage": "en"
      },
      "status": {
        "privacyStatus": os.getenv("YOUTUBE_PRIVACY_STATUS", "public"),
        "selfDeclaredMadeForKids": True
      }
    }, media_body=MediaFileUpload(str(video), chunksize=8*1024*1024, resumable=True))
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress()*100)}%", flush=True)
    video_id = response.get("id")
    print(f"Upload succeeded. Video ID: {video_id}")
    print(f"https://www.youtube.com/watch?v={video_id}")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"YouTube upload failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
