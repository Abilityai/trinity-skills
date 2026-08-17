# Image Concepts

Generated imagery in this family is **topical, not decorative**: the picture embodies the
idea on the page instead of being generic stock. This file maps a topic to a specific
visual concept, then gives the prompt grammar that renders it in one coherent style.

Style rules (textless, no humans, one lineage per run) live in `brand_defaults.md` §4 and
are not repeated here. Generate through the `/nano-banana-image-generator` skill — invoke
it **by name**, never by reaching into another skill's scripts.

## How to use

1. Scan the source for the dominant topic / keywords.
2. Match a row below, or improvise a concept following the same style grammar.
3. Fill the template at the bottom with the matched concept.
4. Generate, then dim/scrim it under any text per `brand_defaults.md` §4.

## Concept archetypes

The left column is a *semantic* match, not a keyword lookup — read the topic and pick the
archetype whose shape fits the idea.

| The idea is about… | Visual concept |
|---|---|
| **Comparison, contrast, "X vs Y", taxonomy** | Two contrasting monolithic pillars side by side. Left: dim, cracked, hollow, faint cool glow. Right: tall, vibrant, glowing amber-rose with complex internal filaments. |
| **A network, connections, synthesis, a graph** | Luminous holographic graph — a sphere of glowing nodes connected by amber edges, suspended in the space. |
| **A loop, recursion, memory, accumulation, feedback** | Spiraling recursive light pattern — concentric rings expanding from a glowing core. A loop that opens and folds back. |
| **Many coordinated parts, a fleet, an organization** | A field of glowing monoliths in formation, each pulsing with its own light, one slightly taller (the coordinator). |
| **Interfaces, panels, tools, function surfaces** | Floating holographic projection panels — translucent glass with abstract glyphs (NO real text) suspended in the space. |
| **Convergence, intake, retrieval, funneling** | A glowing data stream flowing into a central monolith, particles converging from above and the sides. |
| **Oversight, governance, audit, safety, watching** | A brutalist control chamber with a single dim monitor wall — no operators, just the architecture of watching. |
| **Architecture, infrastructure, scale, a system** | A vast concrete corridor extending to a vanishing point, one luminous monolith centered far down it. |
| **Decay, drift, degradation, entropy, time** | A slowly disintegrating monolith, its surface dissolving into glowing particles drifting upward. |
| **Identity, character, a thing having a shape** | A single tall glowing pillar with subtle internal patterns visible. |
| **Planning, branching, decision trees, search** | A branching luminous tree structure — root above, branching downward, each leaf a glowing node. |
| **Emptiness, a hollow or failing thing** | A small dim flickering pillar in the foreground, vast empty space overhead. |
| **A fork, two futures, a choice** | Two diverging corridors — one bright, welcoming, active; one dim, echoing, empty. |
| **Default / abstract / no clear topic** | Floating volumetric data sphere — a rotating glowing core suspended in the space. |

## Prompt template

Replace `{OBJECT_DESCRIPTION}` and `{OBJECT_NOUN}` from the matched concept. Adjust
`ASPECT RATIO` to the slot you're filling (`1:1`, `16:9`, a wide banner crop).

```
Cinematic medium-format film photograph, eye-level wide angle, zero humans in frame. ABSOLUTELY NO TEXT, LETTERS, NUMBERS, OR WRITTEN CHARACTERS ANYWHERE IN THE IMAGE.

SUBJECT (architecture and luminous form are the subject, no people, no text):
{OBJECT_DESCRIPTION}

ENVIRONMENT:
- Near-future interior, monumental scale
- Polished concrete floor reflecting the glowing {OBJECT_NOUN}
- Massive curved concrete walls with subtle LED veins running along the seams
- Soft volumetric mist diffusing the light
- Single beam of soft daylight from a slit skylight far above
- Brutalist architecture in the Tadao Ando lineage
- The room is empty of any human presence

TECHNICAL (locked):
- Shot on Pentax 67 medium format with Kodak Portra 400 film
- Visible halation — soft warm bloom around the glowing {OBJECT_NOUN}
- Visible film grain structure, NOT digital sharpness
- Lifted blacks (shadows 15-20 percent, never crushed)
- Soft magenta in shadow detail of the concrete
- Organic film bokeh on the deepest background reflections
- Slight light leak warmth at frame edges

SCENE COLOR TEMPERATURE: warm pastel red and cream against deep charcoal-magenta concrete shadows; {OBJECT_NOUN} glows amber-rose

COMPOSITION: symmetrical one-point perspective, vanishing point dead center; the {OBJECT_NOUN} centered slightly below middle of frame, space overhead left empty so a crop has room for typography on the top portion

MOOD: reverence, quiet, the architecture of a thinking system

ASPECT RATIO: 1:1 square

ABSOLUTELY NO HUMAN FIGURES, SILHOUETTES, OR CHARACTERS ANYWHERE.
ABSOLUTELY NO TEXT, LETTERS, NUMBERS, OR WRITTEN CHARACTERS ANYWHERE IN THE IMAGE. The image must be PURELY a photograph — no overlays, no captions, no signage.
```

**Swapping the lineage.** The environment/technical blocks above are one coherent
photographic world, and holding them fixed is what makes a run look designed. If your brand
has a different visual lineage, replace those two blocks wholesale — but replace them
*once* and keep every image in the deliverable inside the new world. Mixing lineages
within one deliverable is the failure this file exists to prevent.

## Anti-patterns

- **The default sphere for every topic** — lazy, and it defeats the point of matching.
- **Baked-in text** of any kind — the HTML overlays the title; the source MUST be textless.
- **Humans or silhouettes** when the run's lineage excludes them.
- **Off-palette color** in the image (cyan, electric blue, lime, neon green) — stay inside
  the run's color family.
- **Photorealistic CGI** look — the film-grain + halation aesthetic is the whole texture.
- **The identical shot reused** across two slots in one deliverable — vary the framing and
  angle within the same world.

## Extending

If a topic matches nothing here, improvise a concept, generate it, and — if it works — add
a row. The table is meant to grow with use; a skill copy that never gains a row is a skill
nobody adapted.
