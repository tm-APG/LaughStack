# LaughStack web app (Firebase)

Front end + analyzer + dashboard, deployed on Firebase:

- **Hosting** — static SPA in `public/` (no build step; vanilla JS + Firebase
  CDN SDK): upload, sessions list, session dashboard, A/B compare.
- **Cloud Functions (Python, 2nd gen)** — `functions/main.py`:
  `analyze_upload` (Storage trigger runs the laughstack pipeline),
  `compare_sessions` (callable A/B). The DSP stays server-side by design
  (trade-secret posture, see ../docs/PATENTS.md).
- **Firestore** — session status + summary metrics (rules: owner-only).
- **Storage** — `uploads/{uid}/{sessionId}/…` (client writes),
  `results/{uid}/{sessionId}/session.json` (functions write, owner reads).

## Demo mode

With no Firebase config, the app serves bundled sample data (two nights of
the same set, silent bit and all) so every view is previewable:

```bash
cd web/public && python -m http.server 8080   # open http://localhost:8080
```

Regenerate the demo data after pipeline changes:
`python web/scripts/make_demo_data.py`

## Going live

1. Create a Firebase project (Blaze plan — Python functions require it).
   Enable **Authentication → Google**, **Firestore**, **Storage**.
2. Put your project id in `.firebaserc`, and paste the web-app config into
   `public/js/firebase-init.js` (this switches demo mode off).
3. Bundle the pipeline into the functions dir (rerun after any change under
   `src/laughstack/`):
   ```bash
   ./scripts/sync_package.sh
   ```
4. Deploy:
   ```bash
   firebase deploy   # hosting + functions + rules + indexes
   ```

## Operational notes

- `analyze_upload` runs at 2 GB / 540 s / concurrency 1. A one-hour set at
  16 kHz analyzes comfortably inside that; if sets time out, raise
  `timeout_sec` or move the analyzer to Cloud Run.
- Non-WAV uploads are transcoded with the ffmpeg binary bundled by
  `imageio-ffmpeg` (no system ffmpeg needed in Functions).
- Transcription (per-bit tables) is **off** in the cloud analyzer by
  default — faster-whisper model downloads don't fit comfortably in a
  cold-starting function. Options: run analysis with `--transcribe` locally
  and upload the session JSON, or move the analyzer to Cloud Run with a
  baked-in model. Detection, laugh map, and set metrics all work without it.
- Retention: recordings are client-confidential (spec §10). Add a lifecycle
  rule on the bucket to auto-delete `uploads/` after your stated retention
  window.
