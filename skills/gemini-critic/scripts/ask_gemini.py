#!/usr/bin/env python3
"""Self-contained Gemini caller for the gemini-critic skill.

Calls the Gemini REST API directly (no MCP server needed). Key resolution:
GEMINI_API_KEY env var, else the `gemini_api_key` file in the skill directory.

Usage:
  echo "prompt" | ask_gemini.py [--model M] [--system-file F] [--temperature T] [--search] [--file PATH]...
  ask_gemini.py --prompt-file PATH [...]

Prints the model's text response to stdout; errors go to stderr with exit 1.
"""
import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
INLINE_LIMIT = 19 * 1024 * 1024  # REST inline_data total request cap is ~20MB


def resolve_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    sys.exit("ERROR: GEMINI_API_KEY not set — add it to this agent's credentials")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="gemini-pro-latest",
                   help="alias tracking Google's newest flagship pro model")
    p.add_argument("--prompt-file", help="read user prompt from file (default: stdin)")
    p.add_argument("--system-file", help="read system instruction from file")
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--thinking-budget", type=int, default=-1,
                   help="-1 = dynamic/unlimited thinking (default)")
    p.add_argument("--search", action="store_true", help="enable Google Search grounding")
    p.add_argument("--file", action="append", default=[], dest="files",
                   help="attach a binary/media file (PDF, image, audio, video); repeatable")
    p.add_argument("--timeout", type=int, default=570, help="request timeout in seconds")
    args = p.parse_args()

    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text()
    else:
        prompt = sys.stdin.read()
    if not prompt.strip():
        sys.exit("ERROR: empty prompt (pass via stdin or --prompt-file)")

    parts = [{"text": prompt}]
    total_inline = 0
    for f in args.files:
        path = Path(f)
        if not path.exists():
            sys.exit(f"ERROR: attachment not found: {path}")
        data = path.read_bytes()
        total_inline += len(data)
        if total_inline > INLINE_LIMIT:
            sys.exit(f"ERROR: attachments exceed ~20MB inline limit at {path}")
        mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        parts.append({"inline_data": {"mime_type": mime,
                                      "data": base64.b64encode(data).decode()}})

    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "temperature": args.temperature,
            "thinkingConfig": {"thinkingBudget": args.thinking_budget},
        },
    }
    if args.system_file:
        payload["system_instruction"] = {
            "parts": [{"text": Path(args.system_file).read_text()}]
        }
    if args.search:
        payload["tools"] = [{"google_search": {}}]

    req = urllib.request.Request(
        f"{API_BASE}/{args.model}:generateContent",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": resolve_key()},
    )
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            body = json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"ERROR: HTTP {e.code} from Gemini API: {e.read().decode(errors='replace')[:2000]}")
    except Exception as e:
        sys.exit(f"ERROR: request failed: {e}")

    try:
        candidate = body["candidates"][0]
        text = "".join(part.get("text", "")
                       for part in candidate["content"]["parts"])
    except (KeyError, IndexError):
        sys.exit(f"ERROR: unexpected response shape: {json.dumps(body)[:2000]}")

    finish = candidate.get("finishReason", "")
    if finish not in ("", "STOP"):
        print(f"[finishReason: {finish}]", file=sys.stderr)
    print(text)


if __name__ == "__main__":
    main()
