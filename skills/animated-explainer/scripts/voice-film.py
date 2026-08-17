#!/usr/bin/env python3
"""
voice-film — generate a timed ElevenLabs voiceover for a canvas-film export and mux it.

The narration is a list of lines pinned to the film's timeline (normally derived from the
caption pairs — the captions already tell the story; the voice reads it). Each line becomes
one TTS clip, placed at its exact t. The script measures every clip and reports how it fits
its slot BEFORE it renders anything, because the one thing you cannot fix in the mix is a
voice that talks over the next beat.

  python3 voice-film.py narration.json --film film.mp4 -o film_voiced.mp4
  python3 voice-film.py narration.json --report-only            # fit check, no render
  python3 voice-film.py narration.json -o track.m4a             # voiceover track only
  python3 voice-film.py narration.json --film film.mp4 \
      --music bg.mp3 -o film_voiced.mp4                         # + background music, ducked under the voice

narration.json:
  {
    "voice_id": "...",                       // or --voice, or $ELEVENLABS_VOICE_ID
    "model_id": "eleven_multilingual_v2",    // optional
    "lines": [
      { "t": 1.0,  "end": 5.8,  "text": "An AI agent is easy to demo." },
      { "t": 6.4,  "end": 11.0, "text": "Running one is a different job." }
    ]
  }
  t   — when the line starts speaking (seconds on the film clock)
  end — optional: the caption window's end; speech past it is a soft warning
        (the HARD limit is always the next line's t — colliding speech fails the run)

--music takes any audio FILE (this script sources nothing): it loops if shorter than the
film, trims to it, fades in/out, and by default sidechain-ducks under the voice so speech
stays clear. Generating/choosing the track is upstream — a music library, Suno, anything.

Clips are cached in --clips DIR keyed on (voice, model, text): re-running after editing two
lines regenerates two clips, not twenty-two. Requires: ffmpeg/ffprobe on PATH,
$ELEVENLABS_API_KEY (or --env pointing at a .env that has it). No pip packages.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128"
DEFAULT_MODEL = "eleven_v3"   # v3 IGNORES voice_settings.speed (200, no effect) — pace with --max-speedup or trims; pin eleven_multilingual_v2 in narration.json model_id if you need the speed knob


def load_env(path):
    """Minimal KEY=VALUE .env loader — only fills vars not already set."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def ffprobe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
        capture_output=True, text=True, check=True)
    return float(json.loads(out.stdout)["format"]["duration"])


TAIL_KEEP = 0.1          # seconds of trailing silence kept on every clip
SILENCE_DB = "-60dB"     # tail gate: CONSERVATIVE on purpose. True TTS dead tail measures
                         # −85..−91dB, so −60 still trims it — but a final word's quiet decay
                         # (−45..−60dB) counts as SPEECH and can never be cut. Truncating a
                         # word is worse than a slightly longer line; the fit absorbs length.


def trailing_silence(path):
    """Seconds of silence at the END of a clip. TTS clips carry ~0.5s of dead tail each;
    counted as speech it fabricates collisions, so the fit report and the render both work
    with the trimmed duration."""
    out = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af",
         f"areverse,silencedetect=noise={SILENCE_DB}:d=0.05", "-f", "null", "-"],
        capture_output=True, text=True)
    # Parse NUMERICALLY: the tail is the silence interval whose (reversed) start is ≈ 0.
    # A substring test ("silence_start: 0" in line) also matches 0.523 — that bug returned a
    # MID-CLIP pause as the tail and truncated the end of the line by that amount.
    start = None
    for line in out.stderr.splitlines():
        m = re.search(r"silence_start: (-?[0-9.]+)", line)
        if m:
            start = float(m.group(1))
            continue
        m = re.search(r"silence_duration: ([0-9.]+)", line)
        if m and start is not None:
            if abs(start) < 0.02:               # this interval really is the tail
                return float(m.group(1))
            start = None                        # some later pause — not the tail; keep looking? no: intervals
                                                # come in order, so the first non-zero start means no tail
    return 0.0


def tts(text, voice, model, api_key, prev_text=None, next_text=None, speed=1.0):
    """One ElevenLabs REST call. previous/next_text give the model prosody context so
    per-line clips don't all read like cold opens. speed (0.7-1.2) is the API's own pacing
    control — a slow narrator at 1.15 compresses pauses too (~28% shorter, not 15%)."""
    body = {"text": text, "model_id": model}
    if speed != 1.0:
        body["voice_settings"] = {"speed": speed}
    if prev_text:
        body["previous_text"] = prev_text
    if next_text:
        body["next_text"] = next_text
    req = urllib.request.Request(
        API.format(voice=voice),
        data=json.dumps(body).encode(),
        headers={"xi-api-key": api_key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs {e.code} on line {text[:60]!r}: {e.read().decode()[:400]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("narration", help="narration.json (timed lines)")
    ap.add_argument("--film", help="silent MP4 from export-film.js; omit to build only the audio track")
    ap.add_argument("-o", "--out", help="output file (voiced .mp4 with --film, else audio .m4a)")
    ap.add_argument("--voice", help="ElevenLabs voice id (overrides narration.json / $ELEVENLABS_VOICE_ID)")
    ap.add_argument("--speed", type=float, default=None,
                    help="ElevenLabs pacing 0.7-1.2 (overrides narration.json 'speed'; default 1.0). "
                         "Fix a slow narrator here BEFORE cutting words")
    ap.add_argument("--model", default=None, help=f"model id (default {DEFAULT_MODEL})")
    ap.add_argument("--clips", default=None, help="clip cache dir (default: <narration_dir>/vo_clips)")
    ap.add_argument("--env", default=None, help="path to a .env with ELEVENLABS_API_KEY")
    ap.add_argument("--gain-db", type=float, default=0.0, help="voiceover gain in dB (default 0)")
    ap.add_argument("--music", help="background music file — looped/trimmed to the film, faded, mixed under the voice")
    ap.add_argument("--music-volume", type=float, default=0.06,
                    help="music level, linear 0-1 (default 0.06 — background, matching the video pipelines)")
    ap.add_argument("--music-fade", type=float, default=3.0, help="music fade-in/out seconds (default 3)")
    ap.add_argument("--no-duck", action="store_true",
                    help="disable sidechain ducking (default: music dips ~8-12dB while the voice speaks)")
    ap.add_argument("--max-speedup", type=float, default=1.0,
                    help="atempo cap to auto-fix collisions (e.g. 1.08). Default 1.0 = never alter pace; fix the words instead")
    ap.add_argument("--base-speedup", type=float, default=1.0,
                    help="uniform atempo applied to EVERY clip (render-time pace for models that "
                         "ignore the API speed knob, e.g. eleven_v3; 1.05 = 5%% faster, no re-billing). "
                         "Collision fixes may exceed it, up to --max-speedup")
    ap.add_argument("--min-gap", type=float, default=0.3,
                    help="guaranteed silence between a line's speech END and the NEXT line's start "
                         "(default 0.3s). Line starts never move — they are the film alignment; the "
                         "previous line must end early, absorbed by atempo or a text trim")
    ap.add_argument("--report-only", action="store_true", help="generate/measure clips and print the fit report, render nothing")
    ap.add_argument("--force", action="store_true", help="render even with unresolved collisions (they WILL overlap audibly)")
    args = ap.parse_args()

    if args.env:
        load_env(args.env)
    load_env(Path.cwd() / ".env")
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ELEVENLABS_API_KEY not set. Export it, or pass --env /path/to/.env")

    narr_path = Path(args.narration)
    narr = json.loads(narr_path.read_text())
    lines = narr.get("lines", [])
    if not lines:
        sys.exit("narration.json has no lines")
    voice = args.voice or narr.get("voice_id") or os.environ.get("ELEVENLABS_VOICE_ID")
    if not voice:
        sys.exit("no voice id: pass --voice, set voice_id in narration.json, or export ELEVENLABS_VOICE_ID")
    model = args.model or narr.get("model_id") or DEFAULT_MODEL
    speed = args.speed if args.speed is not None else float(narr.get("speed", 1.0))
    if not 0.7 <= speed <= 1.2:
        sys.exit(f"speed {speed} outside ElevenLabs' 0.7-1.2 range")

    for i in range(1, len(lines)):
        if lines[i]["t"] <= lines[i - 1]["t"]:
            sys.exit(f"lines must be sorted by t: line {i} starts at {lines[i]['t']} after {lines[i-1]['t']}")

    film_dur = ffprobe_duration(args.film) if args.film else None

    clips_dir = Path(args.clips) if args.clips else narr_path.parent / "vo_clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    # ---- generate (cache-aware) and measure ----------------------------------
    # "dur" downstream is the EFFECTIVE duration: raw minus the dead tail beyond TAIL_KEEP.
    # The render trims the same tail, so the report and the mix always agree.
    clips = []
    for i, ln in enumerate(lines):
        cache_id = f"{voice}|{model}|{ln['text']}" if speed == 1.0 else f"{voice}|{model}|{speed}|{ln['text']}"
        key = hashlib.sha1(cache_id.encode()).hexdigest()[:10]
        clip = clips_dir / f"line_{i:02d}_{key}.mp3"
        if not clip.exists():
            print(f"  tts [{i+1}/{len(lines)}] {ln['text'][:64]}{'…' if len(ln['text']) > 64 else ''}")
            # eleven_v3 rejects previous/next_text outright (400 unsupported_model) —
            # prosody context is a v2-family feature; v3 carries its own expressiveness
            ctx_ok = not model.startswith("eleven_v3")
            audio = tts(ln["text"], voice, model, api_key,
                        prev_text=lines[i - 1]["text"] if i and ctx_ok else None,
                        next_text=lines[i + 1]["text"] if i + 1 < len(lines) and ctx_ok else None,
                        speed=speed)
            clip.write_bytes(audio)
        raw = ffprobe_duration(clip)
        tail = trailing_silence(clip)
        clips.append({"path": clip, "raw_dur": raw,
                      "dur": raw - max(0.0, tail - TAIL_KEEP), **ln})

    # ---- fit report -----------------------------------------------------------
    # Hard limit: the next line's start MINUS the guaranteed breathing gap (speech must never
    # collide with speech, and the listener needs a beat of silence between lines).
    # Soft limit: this line's own caption window end (spilling past the fade is style, not a bug).
    collisions, spills = [], []
    print(f"\n  {'#':>2} {'t':>7} {'dur':>6} {'slot':>6}  fit   (slot = to next line − {args.min_gap:.2f}s gap)")
    for i, c in enumerate(clips):
        gap = args.min_gap if i + 1 < len(clips) else 0.0
        hard = (clips[i + 1]["t"] if i + 1 < len(clips) else (film_dur or c.get("end") or c["t"] + c["dur"])) - c["t"] - gap
        status = "ok"
        c["atempo"] = args.base_speedup
        eff = c["dur"] / c["atempo"]                      # what the mix will actually run
        if eff > hard + 0.05:
            need = c["dur"] / hard
            cap = max(args.max_speedup, args.base_speedup)
            if cap > 1.0 and need <= cap:
                c["atempo"] = round(need + 0.005, 3)
                status = f"COLLIDES → atempo {c['atempo']}"
            else:
                status = f"COLLIDES with next line by {eff - hard:.1f}s — shorten the text"
                collisions.append(i)
        elif c.get("end") and c["t"] + eff > c["end"] + 0.05:
            status = f"spills {c['t'] + eff - c['end']:.1f}s past its caption (soft)"
            spills.append(i)
        print(f"  {i+1:>2} {c['t']:>6.1f}s {c['dur']:>5.1f}s {hard:>5.1f}s  {status}")

    total_speech = sum(c["dur"] / c["atempo"] for c in clips)
    print(f"\n  {len(clips)} lines · {total_speech:.0f}s of speech"
          + (f" over a {film_dur:.0f}s film ({100 * total_speech / film_dur:.0f}% voiced)" if film_dur else "")
          + f" · {len(collisions)} collision(s), {len(spills)} soft spill(s)"
          + (f" · base atempo {args.base_speedup}" if args.base_speedup != 1.0 else ""))

    if args.report_only:
        return
    if collisions and not args.force:
        sys.exit("\nfix the colliding lines (or re-run with --max-speedup 1.08, or --force) — refusing to render overlapping speech")

    # ---- assemble the timed track ---------------------------------------------
    out = Path(args.out) if args.out else (
        Path(args.film).with_name(Path(args.film).stem + "_voiced.mp4") if args.film else narr_path.with_name("voiceover.m4a"))
    track_dur = film_dur or max(c["t"] + c["dur"] / c["atempo"] for c in clips) + 0.5

    cmd = ["ffmpeg", "-y"]
    for c in clips:
        cmd += ["-i", str(c["path"])]
    music_idx = film_idx = None
    if args.music:
        if not Path(args.music).exists():
            sys.exit(f"music file not found: {args.music}")
        music_idx = len(clips)
        cmd += ["-stream_loop", "-1", "-i", args.music]   # loop forever; atrim below ends it
    if args.film:
        film_idx = len(clips) + (1 if args.music else 0)
        cmd += ["-i", args.film]

    # tail-trim: cut each clip at EXACTLY the effective duration the fit report used — never
    # re-detect silence at render time. (silencedetect and silenceremove are different
    # detectors — absolute level vs windowed RMS — and on breathy v3 tails they disagree by
    # ~0.3s, which silently ate the min-gap guarantee. The measurement IS the trim.)
    # The 0.12s fade-out ending at the cut is the terminal declick: ElevenLabs clips sometimes
    # end in a sharp click/chirp, and a hard cut also gives the sidechain release a cliff.
    # It rides mostly on the TAIL_KEEP silence, so it never audibly shortens speech.
    parts, labels = [], []
    for i, c in enumerate(clips):
        tempo = f"atempo={c['atempo']}," if c["atempo"] != 1.0 else ""
        d = c["dur"]
        detail = f"atrim=0:{d:.3f},afade=t=out:st={max(0.0, d - 0.12):.3f}:d=0.12,"
        parts.append(f"[{i}:a]{detail}{tempo}adelay={int(c['t'] * 1000)}:all=1[a{i}]")
        labels.append(f"[a{i}]")
    gain = f",volume={args.gain_db}dB" if args.gain_db else ""
    parts.append(f"{''.join(labels)}amix=inputs={len(clips)}:duration=longest:normalize=0"
                 f",apad,atrim=0:{track_dur:.3f}{gain}[vo]")

    final = "[vo]"
    if args.music:
        fade = min(args.music_fade, track_dur / 2)
        parts.append(f"[{music_idx}:a]atrim=0:{track_dur:.3f},volume={args.music_volume}"
                     f",afade=t=in:st=0:d={fade},afade=t=out:st={track_dur - fade:.3f}:d={fade}[bg]")
        if args.no_duck:
            parts.append(f"[vo][bg]amix=inputs=2:duration=first:normalize=0[mix]")
        else:
            # duck the music by the voice's own level: dips ~10dB while speech plays, breathes
            # back in gaps. level_sc=4 (+12dB) puts conversational VO RMS (~-41dB) well over
            # the threshold — without it the compressor never triggers and the "duck" is silent.
            parts.append(f"[vo]asplit=2[voM][voSC]")
            parts.append(f"[bg][voSC]sidechaincompress=threshold=0.01:ratio=8:attack=25:release=600:level_sc=4[bgd]")
            parts.append(f"[voM][bgd]amix=inputs=2:duration=first:normalize=0[mix]")
        final = "[mix]"
    filtergraph = ";".join(parts)

    if args.film:
        cmd += ["-filter_complex", filtergraph,
                "-map", f"{film_idx}:v", "-map", final,
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]
    else:
        cmd += ["-filter_complex", filtergraph, "-map", final, "-c:a", "aac", "-b:a", "192k", str(out)]

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ffmpeg failed:\n{r.stderr[-2000:]}")

    print(f"\n  {out}  ({ffprobe_duration(out):.2f}s)")
    if args.music:
        print(f"  music: {Path(args.music).name} @ {args.music_volume}"
              + (" (no ducking)" if args.no_duck else " (ducked under the voice)"))
    if args.film:
        print("  verify: play the first 20s AND one late beat — a global offset is inaudible in a spot-check of one")


if __name__ == "__main__":
    main()
