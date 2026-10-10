---
name: nano-banana-image-generator
description: Generate images using Google's Nano Banana 2 (Gemini 3.1 Flash Image). Use when creating infographics, diagrams, thumbnails, social media graphics, or any AI-generated images. Costs $0.067/image.
allowed-tools: Bash, Read, Write
category: visual-communication
requires:
  env: [GEMINI_API_KEY, GOOGLE_API_KEY]
  binaries: [python3]
metadata:
  version: "1.1.1"
  changelog:
    - "1.1.1: Fix — the runtime replaces every dollar-digit placeholder in a skill body with the words the skill was invoked with, so dollar-digit text here was rewritten on runs with arguments. Shell positionals are now ${0}/${1}, intended placeholders $ARGUMENTS[0], and prices are written in USD (library validator rule arg-substitution, 2026-10-10)"
    - "1.1: GA model ID gemini-3.1-flash-image across all three scripts (was the -preview ID; both resolve today, the GA one is the stable contract); generate_image.py is now the preferred entry point (proper JSON escaping + aspect ratio) and generate.sh is documented as the fallback that breaks on prompts containing double quotes; stale Gemini 2.5 header comments fixed. Folded back from a field copy's 2026-07-11 audit (library becomes the single source)"
    - "1.0: Promoted to trinity-skills library (2026-08-04)"
---

# Nano Banana Image Generator

Generate images using Google's Gemini 3.1 Flash Image model (model ID: `gemini-3.1-flash-image`, codename: Nano Banana 2).

Script paths below are relative to **this skill's directory**.

## Quick Start

**Preferred - Python script (handles JSON escaping, aspect ratio control):**
```bash
python3 scripts/generate_image.py "A red apple on white background" /tmp/apple.png
```

**Generate a 16:9 thumbnail:**
```bash
python3 scripts/generate_thumbnail.py "YouTube thumbnail showing AI agents" /tmp/thumb.png
```

**Bash fallback (breaks on prompts containing double quotes - prefer the Python script):**
```bash
OUTPUT_DIR=/tmp bash scripts/generate.sh "Sunset over mountains" sunset.png
```

## Scripts

| Script | Purpose | Output |
|--------|---------|--------|
| `scripts/generate_image.py` | **Preferred.** Python with aspect ratio control + proper JSON escaping | Configurable |
| `scripts/generate_thumbnail.py` | 16:9 thumbnails | 1344x768 PNG |
| `scripts/generate.sh` | Bash fallback (no escaping - fails on double quotes in prompts) | 1024x1024 PNG |

All three scripts call the same model: `gemini-3.1-flash-image`.

## Pricing & Limits

- **Cost**: USD 0.067 per image
- **Free tier**: 500 requests/day
- **Generation time**: ~22 seconds
- **Resolution**: 1024x1024 (square), 1344x768 (16:9)

## Best Practices

For detailed prompt engineering and brand styling guidelines, see [best_practices.md](best_practices.md).

### Critical Constraints

| Element | Maximum |
|---------|---------|
| Visual boxes/shapes | **10 maximum** |
| Text pieces/labels | **10 maximum** |
| Hierarchy levels | **3 maximum** |

### Prompt Structure

**DO:** Write narrative descriptions
```
Create a simple infographic with black background showing a central concept
with 4-5 supporting elements. Use white text, DM Sans font, bold titles.
```

**DON'T:** Use keyword lists
```
LinkedIn post, gradient, red, white, large text, 15 boxes, arrows everywhere
```

### Brand Styling (Eugene's)

Include in prompts for brand consistency:
```
Use Eugene's brand style: black background (#000000), white text (#ffffff),
DM Sans font, bold 700 weight for titles, clean minimal design.
```

## Use Cases

**Perfect For:**
- Social media infographics and carousels
- YouTube thumbnails
- Diagrams and technical documentation
- Product mockups
- Mobile-optimized content

**Not Ideal For:**
- Hyper-realistic photography
- Complex multi-font typography
- Fine detail technical renders

## Environment Variables

- `GOOGLE_API_KEY` or `GEMINI_API_KEY` - API key (required)
- `OUTPUT_DIR` - Output directory (default: current directory)

## Examples

**Infographic:**
```bash
python3 scripts/generate_image.py "Simple framework diagram with black background. CENTER: 'AI Agents' in large white text. SURROUNDING: 4 icons for Planning, Memory, Tools, Learning. DM Sans font, minimal design." agents_framework.png
```

**Thumbnail:**
```bash
python3 scripts/generate_thumbnail.py "Professional YouTube thumbnail: bold white text 'DEEP AGENTS' on dramatic black background with subtle blue glow, tech aesthetic" deep_agents_thumb.png
```
