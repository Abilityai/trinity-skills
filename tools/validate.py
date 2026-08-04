#!/usr/bin/env python3
"""trinity-skills validator — the library's deterministic quality gate.

CONTRIBUTING.md is the human-readable contract; this file is the executable
one. A FAIL is a blocker, never an advisory.

Usage:
    python3 tools/validate.py --all                    all skills + repo-level gates
    python3 tools/validate.py .claude/skills/<name>    one or more skill dirs
    python3 tools/validate.py --write-readme           regenerate the README index
    python3 tools/validate.py --all --platform-parser /tmp/platform
        CI mode: additionally parse every SKILL.md with the Trinity platform's
        own parser (skill_packaging.py + utils/safe_yaml.py vendored into the
        given directory) so this repo and the platform cannot drift.

Stdlib-only. PyYAML is used when available; otherwise a minimal frontmatter
parser covers the YAML subset the library conventions require.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / ".claude" / "skills"

CATEGORIES = {
    "agent-development",
    "visual-communication",
    "documents-and-data",
    "research-and-analysis",
    "workspace",
}

# Library naming is deliberately stricter than the platform's SKILL_NAME_RE.
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
ENV_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
MIRROR_RE = re.compile(r"^abilities@[0-9a-f]{7,40} \S+$")
VERSION_RE = re.compile(r"^\d+\.\d+(\.\d+)?$")

# Platform injection caps — skill_packaging.py @ Abilityai/trinity dev 3f1d4c89
SKILL_MAX_BYTES = 10 * 1024 * 1024
TOTAL_MAX_BYTES = 50 * 1024 * 1024
FRONTMATTER_MAX_BYTES = 64 * 1024
DESCRIPTION_MIN_CHARS = 40

LITTER_DIRS = {".git", "__pycache__", "node_modules", ".venv"}
LITTER_FILES = {".DS_Store"}

# Ambient/harness/shell names — never credentials, never require declaration.
ENV_IGNORE = {
    "PATH", "HOME", "PWD", "OLDPWD", "SHELL", "USER", "LANG", "TERM", "TMPDIR",
    "EDITOR", "IFS", "HOSTNAME", "COLUMNS", "LINES", "RANDOM", "SECONDS",
    "FUNCNAME", "LINENO", "EUID", "UID", "CI", "GITHUB_OUTPUT", "GITHUB_ENV",
    "GITHUB_ACTIONS", "PYTHONPATH", "NODE_ENV", "ARGUMENTS",
    "CLAUDE_SESSION_ID", "CLAUDE_SKILL_DIR", "CLAUDE_PROJECT_DIR",
    "CLAUDE_PLUGIN_ROOT", "CLAUDE_EFFORT", "EFFORT_LEVEL",
}

# The undeclared-reference gate is strict only for names that look like
# credentials/config a skill would genuinely read from its environment.
# Everything else (e.g. $TITLE, $SLUG placeholders inside generated-script
# heredocs) is reported as a non-blocking warning — template placeholders
# are not environment reads.
CRED_SHAPE_RE = re.compile(
    r"(?:TOKEN|KEY|SECRET|PASSWORD|CREDENTIALS?)S?$"
    r"|^(?:GH_|GITHUB_|GOOGLE_|GEMINI_|AWS_|ANTHROPIC_|OPENAI_|REPLICATE_"
    r"|SLACK_|DISCORD_|TELEGRAM_|ELEVENLABS_|CLOUDINARY_|BLOTATO_|KLAP_)"
)

SECRET_PATTERNS = [re.compile(p) for p in (
    r"ghp_[A-Za-z0-9]{36}",
    r"gho_[A-Za-z0-9]{36}",
    r"github_pat_[A-Za-z0-9_]{22,}",
    r"sk-[A-Za-z0-9_-]{28,}",
    r"xox[baprs]-[A-Za-z0-9-]{10,}",
    r"AKIA[0-9A-Z]{16}",
    r"AIza[0-9A-Za-z_-]{35}",
    r"r8_[A-Za-z0-9]{24,}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
)]

ENV_REF_PATTERNS = [
    re.compile(r"\$\{?([A-Z][A-Z0-9_]{2,63})\}?"),
    re.compile(r"os\.environ(?:\.get)?\(\s*[\"']([A-Z][A-Z0-9_]{2,63})"),
    re.compile(r"os\.environ\[\s*[\"']([A-Z][A-Z0-9_]{2,63})"),
    re.compile(r"os\.getenv\(\s*[\"']([A-Z][A-Z0-9_]{2,63})"),
    re.compile(r"process\.env\.([A-Z][A-Z0-9_]{2,63})"),
]
ENV_ASSIGN_PATTERNS = [
    re.compile(r"^\s*(?:export\s+)?([A-Z][A-Z0-9_]{2,63})=", re.M),
    re.compile(r"os\.environ\[\s*[\"']([A-Z][A-Z0-9_]{2,63})[\"']\s*\]\s*="),
]

INDEX_BEGIN = "<!-- INDEX:BEGIN -->"
INDEX_END = "<!-- INDEX:END -->"


# ---------------------------------------------------------------- frontmatter

def split_frontmatter(text):
    if not text.startswith("---"):
        return None, None
    end = text.find("\n---", 3)
    if end == -1:
        return None, None
    return text[4:end], text[end + 4:]


def _scalar(v):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        return [_scalar(x) for x in v[1:-1].split(",") if x.strip()]
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v in ("true", "True"):
        return True
    if v in ("false", "False"):
        return False
    return v


def _mini_parse(block):
    """Minimal YAML-subset parser used only when PyYAML is absent: nested
    mappings by indent, '- ' string lists, inline [a, b] lists, scalars."""
    root = {}
    stack = [(-1, root)]
    pending = None  # (key_indent, dict, key) awaiting a nested block
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if pending is not None:
            k_indent, k_dict, k_key = pending
            if indent > k_indent:
                container = [] if line.startswith("- ") else {}
                k_dict[k_key] = container
                stack.append((k_indent, container))
            else:
                k_dict[k_key] = None
            pending = None
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        cur = stack[-1][1]
        if line.startswith("- "):
            if not isinstance(cur, list):
                return None
            cur.append(_scalar(line[2:]))
        elif ":" in line:
            if isinstance(cur, list):
                return None
            key, _, val = line.partition(":")
            key, val = key.strip(), val.strip()
            if val == "":
                pending = (indent, cur, key)
            else:
                cur[key] = _scalar(val)
        else:
            return None
    if pending is not None:
        pending[1][pending[2]] = None
    return root


def parse_frontmatter_block(block):
    try:
        import yaml
        data = yaml.safe_load(block)
        return data if isinstance(data, dict) else None
    except ImportError:
        return _mini_parse(block)
    except Exception:
        return None


# ------------------------------------------------------------------ file walk

def _text_files(d):
    for p in sorted(d.rglob("*")):
        if not p.is_file() or p.is_symlink():
            continue
        try:
            head = p.open("rb").read(8192)
        except OSError:
            continue
        if b"\0" in head or p.stat().st_size > 1024 * 1024:
            continue
        yield p


def _read(p):
    try:
        return p.read_text(errors="replace")
    except OSError:
        return ""


# ------------------------------------------------------------ per-skill gates

def validate_skill(d):
    problems = []
    fail = lambda gate, msg: problems.append(("FAIL", gate, msg))
    name = d.name

    if not NAME_RE.match(name):
        fail("naming", f"directory {name!r} violates ^[a-z0-9][a-z0-9-]{{0,63}}$")

    skill_md = d / "SKILL.md"
    if not skill_md.is_file():
        fail("structure", "SKILL.md missing")
        return problems

    total = 0
    for p in sorted(d.rglob("*")):
        rel = p.relative_to(d)
        if p.is_symlink():
            fail("hygiene", f"symlink not allowed: {rel}")
            continue
        if any(part in LITTER_DIRS for part in rel.parts):
            fail("hygiene", f"litter directory content: {rel}")
        if p.is_file():
            if p.name in LITTER_FILES:
                fail("hygiene", f"litter file: {rel}")
            total += p.stat().st_size
    if total > SKILL_MAX_BYTES:
        fail("caps", f"skill dir is {total} bytes > per-skill cap {SKILL_MAX_BYTES}")

    text = _read(skill_md)
    block, _body = split_frontmatter(text)
    if block is None:
        fail("frontmatter", "no leading --- frontmatter block")
        return problems
    if len(block.encode("utf-8", errors="replace")) > FRONTMATTER_MAX_BYTES:
        fail("caps", "frontmatter exceeds 64 KiB")
    fm = parse_frontmatter_block(block)
    if fm is None:
        fail("frontmatter", "frontmatter does not parse as a mapping")
        return problems

    if fm.get("name") != name:
        fail("frontmatter", f"name: {fm.get('name')!r} != directory {name!r}")
    desc = fm.get("description")
    if not isinstance(desc, str) or len(desc.strip()) < DESCRIPTION_MIN_CHARS:
        fail("frontmatter", f"description missing or under {DESCRIPTION_MIN_CHARS} chars")
    cat = fm.get("category")
    if cat not in CATEGORIES:
        fail("category", f"category {cat!r} not in {sorted(CATEGORIES)}")

    meta = fm.get("metadata")
    meta = meta if isinstance(meta, dict) else {}
    ver = str(meta.get("version") or "")
    if not VERSION_RE.match(ver):
        fail("versioning", "metadata.version missing or not semver (N.N or N.N.N)")
    changelog = meta.get("changelog")
    if not isinstance(changelog, list) or not changelog:
        fail("versioning", "metadata.changelog missing or empty (newest-first list)")
    mirror = meta.get("mirror")
    if mirror is not None and not (isinstance(mirror, str) and MIRROR_RE.match(mirror)):
        fail("mirror", "metadata.mirror must be 'abilities@<sha> <path-in-abilities>'")

    declared = []
    req = fm.get("requires")
    if req is not None and not isinstance(req, dict):
        fail("requires", "requires must be a mapping of env/binaries/packages")
    elif isinstance(req, dict):
        env = req.get("env") or []
        if not isinstance(env, list):
            fail("requires", "requires.env must be a list of key names")
        else:
            for k in env:
                if not isinstance(k, str) or not ENV_KEY_RE.match(k):
                    fail("requires", f"bad env key name {k!r}")
                else:
                    declared.append(k)

    referenced, assigned = set(), set()
    for p in _text_files(d):
        s = _read(p)
        for pat in SECRET_PATTERNS:
            m = pat.search(s)
            if m:
                fail("secrets", f"secret-looking literal in {p.relative_to(d)}: {m.group()[:12]}…")
        for pat in ENV_REF_PATTERNS:
            referenced.update(pat.findall(s))
        for pat in ENV_ASSIGN_PATTERNS:
            assigned.update(pat.findall(s))

    external = referenced - assigned - ENV_IGNORE
    undeclared = sorted(external - set(declared))
    cred_undeclared = [k for k in undeclared if CRED_SHAPE_RE.search(k)]
    placeholderish = [k for k in undeclared if not CRED_SHAPE_RE.search(k)]
    if cred_undeclared:
        fail("env-coherence", f"credential-shaped env referenced but not declared in requires.env: {cred_undeclared}")
    if placeholderish:
        problems.append(("WARN", "env-coherence",
                         f"non-credential env-looking refs (likely template placeholders): {placeholderish}"))
    for k in declared:
        if k not in external and not re.search(rf"\b{re.escape(k)}\b", text):
            fail("env-coherence", f"declared but never referenced (decorative): {k}")

    return problems


# ---------------------------------------------------------- platform parity

def platform_check(parser_dir, skill_dirs):
    sys.path.insert(0, str(parser_dir))
    import skill_packaging as sp  # noqa: E402
    problems = []
    for d in skill_dirs:
        text = _read(d / "SKILL.md")
        fm, warn = sp.parse_frontmatter(text)
        if warn:
            problems.append((d.name, f"platform parse_frontmatter: {warn}"))
            continue
        if fm is None:
            problems.append((d.name, "platform: frontmatter missing"))
            continue
        _contract, warnings = sp.extract_contract(fm)
        bad = [w for w in warnings if w.startswith("frontmatter_invalid")]
        if bad:
            problems.append((d.name, f"platform extract_contract: {bad}"))
    return problems


# -------------------------------------------------------------- README index

def _skill_dirs():
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())


def write_readme():
    rows = {}
    for d in _skill_dirs():
        block, _ = split_frontmatter(_read(d / "SKILL.md"))
        fm = parse_frontmatter_block(block or "") or {}
        meta = fm.get("metadata")
        meta = meta if isinstance(meta, dict) else {}
        cat = fm.get("category") or "uncategorized"
        origin = "mirrored · abilities" if meta.get("mirror") else "library"
        desc = (fm.get("description") or "").strip().split(". ")[0][:140]
        rows.setdefault(cat, []).append((d.name, str(meta.get("version") or ""), origin, desc))

    out = []
    for cat in sorted(rows):
        out.append(f"### {cat}\n")
        out.append("| Skill | Version | Origin | Description |")
        out.append("|---|---|---|---|")
        for name, ver, origin, desc in sorted(rows[cat]):
            out.append(f"| `{name}` | {ver} | {origin} | {desc} |")
        out.append("")
    if not rows:
        out = ["_No skills yet — seeding in progress._", ""]

    readme_path = ROOT / "README.md"
    readme = _read(readme_path)
    if INDEX_BEGIN not in readme or INDEX_END not in readme:
        print("README.md is missing the INDEX markers", file=sys.stderr)
        return 1
    head = readme[: readme.index(INDEX_BEGIN) + len(INDEX_BEGIN)]
    tail = readme[readme.index(INDEX_END):]
    readme_path.write_text(head + "\n" + "\n".join(out) + tail)
    print(f"README index regenerated ({sum(len(v) for v in rows.values())} skills)")
    return 0


# ----------------------------------------------------------------------- main

def main(argv):
    args = list(argv)
    if "--write-readme" in args:
        return write_readme()

    parser_dir = None
    if "--platform-parser" in args:
        i = args.index("--platform-parser")
        parser_dir = Path(args[i + 1])
        del args[i:i + 2]

    if "--all" in args:
        dirs = _skill_dirs()
    else:
        dirs = [Path(a) for a in args if not a.startswith("--")]
    if not dirs:
        print("No skills to validate (empty library is valid).")
        return 0

    failed = False
    grand_total = 0
    for d in dirs:
        problems = validate_skill(d)
        grand_total += sum(p.stat().st_size for p in d.rglob("*") if p.is_file())
        has_fail = any(level == "FAIL" for level, _, _ in problems)
        if has_fail:
            failed = True
        print(f"{'✗' if has_fail else '✓'} {d.name}")
        for level, gate, msg in problems:
            print(f"    [{level}] {gate}: {msg}")

    if grand_total > TOTAL_MAX_BYTES:
        failed = True
        print(f"✗ library total {grand_total} bytes > cap {TOTAL_MAX_BYTES}")

    if parser_dir is not None:
        for name, msg in platform_check(parser_dir, dirs):
            failed = True
            print(f"✗ {name}: {msg}")

    print(("FAIL" if failed else "PASS") + f" — {len(dirs)} skill(s) checked")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
