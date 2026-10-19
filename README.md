# Little Safari Friends 🦁

Free-first GitHub Actions pipeline for original procedural 3D safari stories.

## What the workflow does

1. Selects an original child-friendly story blueprint.
2. Validates the generated `episode.json`.
3. Renders a procedural 3D animation with Blender.
4. Generates English narration using Edge TTS.
5. Combines the video and narration with FFmpeg.
6. Checks that the final MP4 contains both video and audio and has the expected duration.
7. Saves the validated MP4 as a GitHub Actions artifact for seven days.
8. Optionally uploads the validated video to YouTube **as private only**, if the required OAuth secrets are configured.

The workflow does not publish videos publicly.

## Files

- `scripts/generate_episode.py` — creates an episode configuration and story history.
- `scripts/create_episode.py` — runs Blender, generates narration, and muxes the MP4.
- `scripts/blender_scene.py` — builds the procedural safari scene and animation.
- `scripts/upload_youtube.py` — uploads the generated episode privately.
- `episode.json` — current episode configuration.
- `.github/workflows/build-private-video.yml` — scheduled and manual production workflow.

## Run locally

Requirements: Python 3.11+, Blender, FFmpeg, and a working internet connection for Edge TTS.

```bash
python -m pip install -r requirements.txt
python scripts/generate_episode.py
python scripts/create_episode.py
```

The finished file should be at `output/<episode_id>.mp4`.

Check it with:

```bash
ffprobe -v error -show_entries format=duration,size:stream=codec_type,codec_name -of json output/<episode_id>.mp4
```

## Run on GitHub

1. Open the repository's **Actions** tab.
2. Select **Little Safari Friends Automation**.
3. Choose **Run workflow**.
4. Wait for the validation step and render to complete.
5. Download `little-safari-friends-video` from the successful run's artifacts.

The schedule uses `0 6 * * *` (06:00 UTC, or 09:00 Tanzania time). Scheduled workflows can be delayed by GitHub, so this is not a guaranteed exact publishing time.

## Optional private YouTube upload

Configure these repository Actions secrets only if you want private uploads:

- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`

The uploader reads the current `episode.json` for its title and description and selects the matching `episode_id` video. It always sets `privacyStatus` to `private`.

Review the uploaded video in YouTube Studio before making any separate decision about public release. Correctly classify children's content as made for kids where applicable.

## Free-tier notes

GitHub Actions usage and artifact retention are subject to GitHub's current limits. Blender rendering may take several minutes or longer. Edge TTS depends on an external online service and is not an unlimited or guaranteed service. This project does not guarantee views or revenue.

## Troubleshooting

- **Missing MP4:** inspect the Blender render step and ensure `scripts/blender_scene.py` exists.
- **Missing narration:** inspect the Edge TTS step and confirm runner internet access.
- **Audio or duration validation fails:** download the artifact only if the workflow produced one; inspect the FFmpeg command and `episode.json` timing.
- **Repeated stories:** the workflow restores and saves the episode-history cache. Cache availability is not a permanent database, so repetition is still possible if the cache expires or is evicted.
