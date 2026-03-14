# meditation-skill

A personalized meditation audio generator skill (end-to-end) that outputs a final `.mp3`.

## What it does
- Infers a goal (sleep/relax/anxiety/focus) from conversation
- Generates a **line-by-line** guidance script with markers
- Synthesizes TTS **per sentence**, inserting **mandatory gaps** between items
- Mixes voiceover with background music (loop/cut to match voiceover duration)

## Outputs
- Final audio: `outputs/meditation-*.mp3`

## Quick start
1. Put your background tracks in `assets/audio/` locally and keep `assets/audio/music.local.json` updated (not committed).
   For the public repo, we ship `assets/audio/music.sample.json` + `assets/audio/sample-bg.mp3`.
2. Copy `.env.example` to `.env` and fill in `VOLC_TTS_APPID` and `VOLC_TTS_TOKEN`.
3. Run your pipeline (via OpenClaw or scripts).

## Security
- `.env` is ignored; never commit tokens.
