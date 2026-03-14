# meditation-skill

A personalized meditation audio generator skill (end-to-end) that outputs a final `.mp3`.

This repo is GitHub-friendly by default:
- ships with a **single sample background track** (`assets/audio/sample-bg.mp3`)
- keeps your **full local music library** out of version control
- keeps secrets out of the repo (`.env` is ignored)

## What it does
- Infers a goal (sleep/relax/anxiety/focus/quiet)
- Generates a **line-by-line** guidance script with markers
- Synthesizes TTS **per sentence**
- Enforces a hard rule: **≥ 1 second gap** between any two items (sentence / bowl / pause)
- Inserts optional markers:
  - `[[PAUSE:seconds]]`
  - `[[BOWL]]`
- Mixes voiceover with background music (loop/cut to match voiceover duration) and exports mp3

## Outputs
- Final audio: `outputs/meditation-*.mp3`

## Sample
- 10-min sleep meditation (mp3): [`samples/sample-sleep-10min.mp3`](samples/sample-sleep-10min.mp3)

> `outputs/` and `tmp/` are intentionally ignored by git.

---

## Requirements
- `ffmpeg` in PATH
- `node` (used by `scripts/pick_music.js`)
- `python3` (3.12+ recommended)

---

## Music library layout (sample vs local)
This repo contains:
- `assets/audio/sample-bg.mp3` — the only background music committed to GitHub
- `assets/audio/music.sample.json` — mapping that points to `sample-bg.mp3`

Your local machine can maintain a full library without committing it:
- `assets/audio/music.local.json` — **local-only**, ignored by git
- `assets/audio/*.mp3` — your full background tracks (local-only)

### How to use your full local library
1) Keep your full background tracks in `assets/audio/`.
2) Maintain `assets/audio/music.local.json` as your real mapping.
3) When running the pipeline locally, point the picker to `music.local.json` (recommended), or temporarily replace `music.sample.json` usage in your runner.

> Note: currently `scripts/pick_music.js` reads `assets/audio/music.json` in the original workspace version.
> For the public repo layout, you can either:
> - add a tiny wrapper (recommended) to prefer `music.local.json` then fallback to `music.sample.json`, or
> - symlink `assets/audio/music.json -> music.local.json` on your machine.

---

## Configure Volcano TTS (recommended)
Copy the template and fill in secrets:

```bash
cp .env.example .env
```

Key env vars:
- `VOLC_TTS_APPID`
- `VOLC_TTS_TOKEN`

Suggested defaults:
- `VOLC_TTS_VOICE_TYPE=BV700_V2_streaming`
- `VOLC_TTS_STYLE=yoga`
- `VOLC_TTS_SPEED_RATIO=0.7`
- `VOLC_TTS_MAX_CHARS=150`

### Fallback TTS (when Volcano is unavailable)
If Volcano TTS is down / unreachable / auth fails, the Skill should fall back to OpenClaw built-in `tts` tool (per sentence).

---

## Run a local demo (scripts)
This repo includes the core scripts used by the Skill:

1) Generate a line-by-line script:
```bash
python3 scripts/generate_script.py --out tmp/script.txt --goal 助眠 --minutes 5 --name Jacky
```

2) Compose voiceover timeline (per sentence TTS + pauses/bowl + mandatory 1s gaps):
```bash
python3 scripts/compose_voiceover.py --script tmp/script.txt --out tmp/voiceover_timeline.wav --max-chars 150
```

3) Pick a background track (goal-based):
```bash
node scripts/pick_music.js --goal 助眠 --seed 2026-03-14
```

4) Mix with ffmpeg (see `SKILL.md` for the full template).

---

## Notes / Troubleshooting
- If you see `exceed max len limit!` from Volcano: lower `VOLC_TTS_MAX_CHARS`.
- If ffmpeg concat fails: check that generated segment paths are absolute and exist.
- Long silences are expected when you increase `[[PAUSE:...]]` and/or enforce mandatory gaps.

---

## Security
- `.env` is ignored; never commit tokens.
- `assets/audio/music.local.json` is ignored.
