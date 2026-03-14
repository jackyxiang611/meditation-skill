#!/usr/bin/env python3
"""Compose voiceover timeline from a meditation script.

This is a scaffold implementing the desired logic:
1) Generate a meditation script with per-line sentences and inline markers.
2) Call Volc TTS PER SENTENCE (one request per line) to generate mp3 segments.
3) Insert pauses (silence_1s.mp3 repeated) and bowls (song.mp3) based on markers.
4) Concat everything into tmp/voiceover_timeline.wav (or mp3) and return its duration.

Script format (plain text):
- One sentence per line (recommended).
- Markers as standalone tokens or on their own line:
  - [[PAUSE:2]]  -> insert 2 seconds of silence
  - [[BOWL]]     -> insert one bowl sound (~25s)

Usage:
  python3 scripts/compose_voiceover.py --script tmp/script.txt --out tmp/voiceover_timeline.wav

Note: This script assumes Volc TTS env vars are configured and uses scripts/tts_volc.py.
"""

import argparse
import os
import re
import subprocess
import tempfile

SKILL_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AUDIO_DIR = os.path.join(SKILL_ROOT, "assets", "audio")
SILENCE_1S = os.path.join(AUDIO_DIR, "silence_1s.mp3")
BOWL = os.path.join(AUDIO_DIR, "song.mp3")
TTS = os.path.join(SKILL_ROOT, "scripts", "tts_volc.py")

PAUSE_RE = re.compile(r"\[\[PAUSE:(\d+(?:\.\d+)?)\]\]")


def run(cmd):
    # Capture stderr so failures are debuggable
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        tail = "\n".join(p.stderr.splitlines()[-80:])
        raise RuntimeError(f"Command failed ({p.returncode}): {' '.join(cmd)}\n--- stderr tail ---\n{tail}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-chars", default="150")
    ap.add_argument("--sample-rate", default="48000")
    ap.add_argument("--channels", default="2")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    with open(args.script, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f.read().splitlines()]

    seg_dir = os.path.join(os.path.dirname(args.out) or ".", ".voiceover_segs")
    os.makedirs(seg_dir, exist_ok=True)

    concat_list = []
    seg_i = 0

    # Prebuild a reusable 1-second silence wav (for mandatory minimum gap between items)
    silence1_wav = os.path.join(seg_dir, "_silence_1s.wav")
    if not os.path.exists(silence1_wav):
        run(["ffmpeg", "-y", "-i", SILENCE_1S, "-t", "1", "-ar", args.sample_rate, "-ac", args.channels, silence1_wav])

    def add_min_gap():
        # Ensure at least 1 second gap between ANY two items
        if concat_list:
            concat_list.append(silence1_wav)

    for ln in lines:
        if not ln:
            continue

        if ln == "[[BOWL]]":
            add_min_gap()
            # convert bowl to wav for stable concat
            out = os.path.join(seg_dir, f"seg_{seg_i:04d}_bowl.wav")
            run(["ffmpeg", "-y", "-i", BOWL, "-ar", args.sample_rate, "-ac", args.channels, out])
            concat_list.append(out)
            seg_i += 1
            # Always enforce a gap after bowl as well
            concat_list.append(silence1_wav)
            continue

        m = PAUSE_RE.fullmatch(ln)
        if m:
            seconds = float(m.group(1))
            # A PAUSE is itself silence; still ensure at least 1s gap before it when preceding item was speech/bowl.
            add_min_gap()
            out = os.path.join(seg_dir, f"seg_{seg_i:04d}_pause.wav")
            run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", SILENCE_1S, "-t", str(seconds), "-ar", args.sample_rate, "-ac", args.channels, out])
            concat_list.append(out)
            seg_i += 1
            continue

        # Normal sentence -> TTS per line
        add_min_gap()
        seg_txt = os.path.join(seg_dir, f"seg_{seg_i:04d}.txt")
        with open(seg_txt, "w", encoding="utf-8") as tf:
            tf.write(ln)
        seg_mp3 = os.path.join(seg_dir, f"seg_{seg_i:04d}.mp3")
        run([
            "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3",
            TTS,
            "--text-file", seg_txt,
            "--out", seg_mp3,
            "--max-chars", str(args.max_chars),
        ])
        seg_wav = os.path.join(seg_dir, f"seg_{seg_i:04d}.wav")
        run(["ffmpeg", "-y", "-i", seg_mp3, "-ar", args.sample_rate, "-ac", args.channels, seg_wav])
        concat_list.append(seg_wav)
        seg_i += 1
        # Mandatory minimum 1s gap after every spoken sentence
        concat_list.append(silence1_wav)

    # concat wavs
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt") as lf:
        for fp in concat_list:
            lf.write(f"file '{os.path.abspath(fp)}'\n")
        list_path = lf.name

    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-ar", args.sample_rate, "-ac", args.channels, args.out])

    print(args.out)


if __name__ == "__main__":
    main()
