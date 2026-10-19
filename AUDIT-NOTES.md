# Audit notes

Inspected current files through the GitHub integration:
- `.github/workflows/build-private-video.yml`
- `README.md`
- `requirements.txt`
- `episode.json`
- `scripts/generate_episode.py`
- `scripts/create_episode.py`
- `scripts/blender_scene.py`
- `scripts/upload_youtube.py`
- `.gitignore`

Concrete issues:
1. The original uploader's default video path was fixed to `output/leo_learns_to_share.mp4`, even though the generator selects among different episode IDs.
2. The original uploader hard-coded a Leo-specific title and description, so metadata could mismatch a generated episode.
3. The original workflow ran ffprobe but did not assert the presence of both audio and video streams or compare duration with the configured duration.
4. Story history was written to `data/episode_history.json`, but a fresh GitHub-hosted runner did not restore that file from the previous run.
5. The README was incomplete/truncated.

The replacement workflow keeps YouTube uploads private and only attempts the upload after validation. No public publishing was enabled.

The GitHub integration rejected a repository write with HTTP 403 (Resource not accessible by integration), so these replacement files have not been committed to the remote repository. Apply them manually or reconnect GitHub with repository write permission, then test the workflow before relying on it.
