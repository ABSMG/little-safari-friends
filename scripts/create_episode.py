#!/usr/bin/env python3
"""Render a Blender scene, create narration, and assemble an MP4."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"


def exe(name):
    """Find a required executable."""
    value = shutil.which(name)

    if not value:
        raise RuntimeError(
            f"Required executable not found on PATH: {name}"
        )

    return value


def run(command):
    """Run a command and stop if it fails."""
    print("+", " ".join(map(str, command)), flush=True)
    subprocess.run(command, check=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    episode_path = ROOT / "episode.json"
    episode = json.loads(
        episode_path.read_text(encoding="utf-8")
    )

    stem = episode["episode_id"]

    silent_video = OUT / f"{stem}_silent.mp4"
    audio_file = OUT / f"{stem}.mp3"
    final_video = OUT / f"{stem}.mp4"

    blender = exe(os.getenv("BLENDER_BIN", "blender"))
    ffmpeg = exe("ffmpeg")

    # Step 1: Render the 3D animation with Blender.
    run([
        blender,
        "-b",
        "--python",
        str(ROOT / "scripts" / "blender_scene.py"),
        "--",
        "--episode",
        str(episode_path),
        "--output",
        str(silent_video)
    ])

    # Step 2: Combine the narration sentences.
    narration = " ".join(
        scene["narration"].strip()
        for scene in episode["scenes"]
        if scene.get("narration", "").strip()
    )

    # Step 3: Generate narration using Edge TTS.
    voice = episode.get("voice", "en-US-AnaNeural")

    run([
        sys.executable,
        "-m",
        "edge_tts",
        "--voice",
        voice,
        "--text",
        narration,
        "--write-media",
        str(audio_file)
    ])

    # Step 4: Combine animation and narration.
    duration = str(
        int(episode.get("duration_seconds", 32))
    )

    run([
        ffmpeg,
        "-y",
        "-i",
        str(silent_video),
        "-i",
        str(audio_file),
        "-filter_complex",
        f"[1:a]apad,atrim=0:{duration}[a]",
        "-map",
        "0:v:0",
        "-map",
        "[a]",
        "-t",
        duration,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        str(final_video)
    ])

    print(f"Video created successfully: {final_video}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(
            f"Build failed: {error}",
            file=sys.stderr
        )
        raise SystemExit(1)
