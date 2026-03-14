#!/usr/bin/env python3
"""Volcengine (ByteDance OpenSpeech) TTS client.

Endpoint (per your snippet): https://openspeech.bytedance.com/api/v1/tts
Auth header: Authorization: Bearer;<access_token>

Env vars:
  VOLC_TTS_APPID
  VOLC_TTS_TOKEN
Optional:
  VOLC_TTS_CLUSTER (default: volcano_tts)
  VOLC_TTS_UID (default: 388808087185088)
  VOLC_TTS_VOICE_TYPE (default: BV700_V2_streaming)
  VOLC_TTS_STYLE (default: yoga)
  VOLC_TTS_SPEED_RATIO (default: 0.9)
  VOLC_TTS_VOLUME_RATIO (default: 1.0)
  VOLC_TTS_PITCH_RATIO (default: 1.0)

Usage:
  python3 scripts/tts_volc.py --text-file tmp/voiceover_text.txt --out tmp/voiceover_raw.mp3
  python3 scripts/tts_volc.py --text "hello" --out tmp/voiceover_raw.mp3
"""

import argparse
import base64
import json
import os
import sys
import uuid
import urllib.request
import subprocess

API_URL = "https://openspeech.bytedance.com/api/v1/tts"


def _load_dotenv(dotenv_path: str):
    """Minimal .env loader (KEY=VALUE, no export required)."""
    if not dotenv_path or not os.path.exists(dotenv_path):
        return
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


def _env(name: str, default=None):
    v = os.environ.get(name)
    return v if v not in (None, "") else default


def build_payload(text: str):
    appid = os.environ["VOLC_TTS_APPID"]
    token = os.environ["VOLC_TTS_TOKEN"]

    cluster = _env("VOLC_TTS_CLUSTER", "volcano_tts")
    uid = _env("VOLC_TTS_UID", "388808087185088")

    voice_type = _env("VOLC_TTS_VOICE_TYPE", "BV700_V2_streaming")
    style = _env("VOLC_TTS_STYLE", "yoga")

    speed_ratio = float(_env("VOLC_TTS_SPEED_RATIO", "0.9"))
    volume_ratio = float(_env("VOLC_TTS_VOLUME_RATIO", "1.0"))
    pitch_ratio = float(_env("VOLC_TTS_PITCH_RATIO", "1.0"))

    return {
        "app": {"appid": appid, "token": token, "cluster": cluster},
        "user": {"uid": str(uid)},
        "audio": {
            "voice_type": voice_type,
            "encoding": "mp3",
            "speed_ratio": speed_ratio,
            "volume_ratio": volume_ratio,
            "pitch_ratio": pitch_ratio,
            # In your snippet this is called `emotion` and uses the style string.
            "emotion": style,
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "text_type": "plain",
            "operation": "query",
            "with_frontend": 1,
            "frontend_type": "unitTson",
        },
    }


def call_tts(payload: dict) -> dict:
    token = os.environ["VOLC_TTS_TOKEN"]
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            # IMPORTANT: per your code sample, it's `Bearer;{token}` (with semicolon)
            "Authorization": f"Bearer;{token}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read()
            ctype = resp.headers.get("Content-Type", "")
    except Exception as e:
        # Make HTTP 4xx/5xx debuggable by printing body
        if hasattr(e, "read"):
            err_raw = e.read()
            raise RuntimeError(f"HTTPError: {e}\nBody: {err_raw[:1000]!r}")
        raise

    # Some deployments might return audio directly; handle that too.
    if ctype.startswith("audio/"):
        return {"_audio_bytes": raw}

    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        raise RuntimeError(f"Unexpected response (not JSON/audio). content-type={ctype} raw={raw[:200]!r}")


def extract_audio_bytes(result: dict) -> bytes:
    if "_audio_bytes" in result:
        return result["_audio_bytes"]

    # Common schema: {code, message, data}
    # Volc OpenSpeech often returns code=3000 with message=Success.
    if isinstance(result, dict):
        code = result.get("code")
        msg = result.get("message")
        ok_codes = {0, "0", 3000, "3000", None}
        if code not in ok_codes:
            raise RuntimeError(f"TTS error: code={code} message={msg} raw={result}")

        data = result.get("data")
        if isinstance(data, str) and data:
            # Usually base64 encoded mp3
            try:
                return base64.b64decode(data)
            except Exception as e:
                raise RuntimeError(f"Failed to base64 decode `data`: {e}; data_head={data[:50]!r}")

        # Sometimes nested
        for key in ("audio", "audio_data", "speech"):
            v = result.get(key)
            if isinstance(v, str) and v:
                return base64.b64decode(v)

    raise RuntimeError(f"Could not find audio bytes in response: {result}")


def _split_text(text: str, max_chars: int):
    """Split Chinese text into chunks under max_chars using newlines and punctuation."""
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    # First split by blank lines
    parts = []
    for block in text.split("\n"):
        b = block.strip()
        if b:
            parts.append(b)

    # If still too long, split by sentences
    seps = "。！？；;.!?"
    sentences = []
    for p in parts:
        buf = ""
        for ch in p:
            buf += ch
            if ch in seps:
                sentences.append(buf.strip())
                buf = ""
        if buf.strip():
            sentences.append(buf.strip())

    chunks = []
    cur = ""
    for s in sentences:
        if not cur:
            cur = s
        elif len(cur) + 1 + len(s) <= max_chars:
            cur = cur + "\n" + s
        else:
            chunks.append(cur)
            cur = s
    if cur:
        chunks.append(cur)

    # Fallback: hard split
    final = []
    for c in chunks:
        if len(c) <= max_chars:
            final.append(c)
        else:
            for i in range(0, len(c), max_chars):
                final.append(c[i:i+max_chars])
    return [x for x in final if x.strip()]


def _concat_mp3(files, out_path):
    """Concat mp3 segments using ffmpeg concat demuxer (re-encode-free when possible)."""
    tmp_list = out_path + ".concat.txt"
    with open(tmp_list, "w", encoding="utf-8") as f:
        for fp in files:
            f.write(f"file '{os.path.abspath(fp)}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", tmp_list, "-c", "copy", out_path]
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    # Load .env if present (helps when the calling process doesn't inherit your shell env)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_root = os.path.abspath(os.path.join(script_dir, ".."))
    _load_dotenv(os.path.join(skill_root, ".env"))

    ap = argparse.ArgumentParser()
    ap.add_argument("--text", help="text to synthesize")
    ap.add_argument("--text-file", help="path to utf-8 text file")
    ap.add_argument("--out", required=True, help="output mp3 path")
    ap.add_argument("--max-chars", type=int, default=int(_env("VOLC_TTS_MAX_CHARS", "800")),
                    help="max chars per TTS request; long text will be chunked")
    args = ap.parse_args()

    if not args.text and not args.text_file:
        ap.error("Provide --text or --text-file")

    if args.text_file:
        text = open(args.text_file, "r", encoding="utf-8").read().strip()
    else:
        text = args.text.strip()

    if not text:
        raise SystemExit("Empty text")

    chunks = _split_text(text, args.max_chars)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    if len(chunks) == 1:
        payload = build_payload(chunks[0])
        result = call_tts(payload)
        audio = extract_audio_bytes(result)
        with open(args.out, "wb") as f:
            f.write(audio)
        sys.stdout.write(args.out)
        return

    # Chunked synthesis
    seg_dir = os.path.join(os.path.dirname(args.out) or ".", ".tts_segs")
    os.makedirs(seg_dir, exist_ok=True)
    seg_files = []
    for i, ch in enumerate(chunks, 1):
        payload = build_payload(ch)
        result = call_tts(payload)
        audio = extract_audio_bytes(result)
        seg_path = os.path.join(seg_dir, f"seg_{i:03d}.mp3")
        with open(seg_path, "wb") as f:
            f.write(audio)
        seg_files.append(seg_path)

    _concat_mp3(seg_files, args.out)

    sys.stdout.write(args.out)


if __name__ == "__main__":
    main()
