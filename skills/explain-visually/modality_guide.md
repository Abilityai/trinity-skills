# Modality Guide - /explain-visually

The core skill is **choosing the right picture for each facet**. Don't default everything to a flowchart. Read the facet, find what it's fundamentally *about*, and match it below.

## Decision table

| The facet is fundamentally about... | Visual modality | Engine | Mermaid type |
|---|---|---|---|
| A **process / pipeline / decision logic** | flowchart | Mermaid | `flowchart` |
| **Ordering of events / evolution / roadmap** | timeline | Mermaid | `timeline` |
| **Who-does-what over time / a protocol / message passing** | sequence diagram | Mermaid | `sequenceDiagram` |
| **System structure / components & how they connect** | architecture / block | Mermaid (or illustration) | `flowchart` / `block-beta` |
| **Entities & relations / a data model** | ER / schema | Mermaid | `erDiagram` |
| **Class / type structure / inheritance** | class diagram | Mermaid | `classDiagram` |
| **Lifecycle / modes / transitions** | state machine | Mermaid | `stateDiagram-v2` |
| **Proportions of a whole** | chart | Mermaid | `pie` |
| **Quantities / a trend over a range** | chart | Mermaid | `xychart-beta` |
| **Trade-offs on two axes / positioning** | comparison | Mermaid | `quadrantChart` |
| **A structured X-vs-Y feature comparison** | comparison table | HTML table | *(author HTML)* |
| **How it all hangs together / a taxonomy** | mind map | Mermaid | `mindmap` |
| **A metaphor or rich visual no structural diagram captures** | conceptual illustration | `/create-explanatory-image` | *(generative)* |

**Tie-breakers:**
- Steps with branches/loops -> `flowchart`. Linear steps with no branching that happen *between actors* -> `sequenceDiagram`. Linear steps tied to *dates/eras* -> `timeline`.
- "Parts of a system" with clear boxes/wires -> `flowchart`/`block-beta`. "Parts of an idea" with no wiring -> `mindmap`.
- Numbers that sum to a whole -> `pie`. Numbers across a range/time -> `xychart-beta`.

## Node budget (LOCKED)

- **<= ~10-12 nodes / steps / rows per diagram.** Beyond that, comprehension drops and the render clips.
- If a facet needs more, **split it into two diagrams** (e.g. "the happy path" + "the error paths") or **raise the abstraction** (group sub-steps into one node).
- **Telegraphic labels: 2-5 words.** "Plan & decompose", not "The orchestrator plans and decomposes the incoming task." Reserved/odd chars in a label -> wrap in quotes: `A["a: b (c)"]`.

## When to escalate to an illustration

Use `/create-explanatory-image` (not Mermaid) when the facet is:
- A **metaphor** ("memory is like a desk vs a warehouse")
- A **physical/spatial** thing (a cross-section, an exploded view, a real-world scene)
- An **emotional / before-after framing** where mood matters more than structure

If the facet has boxes-and-arrows logic, Mermaid is faster, cheaper, editable, and crisper - prefer it. Skip illustrations entirely with `--no-illustrations`.

---

## Mermaid templates (fork these)

All render through the themed wrapper in `style_library.md` - do NOT put colors here; the theme handles look. These set **structure** only.

### flowchart (process / decision)
```
flowchart LR
  A[Ingest] --> B[Plan]
  B --> C{Needs tools?}
  C -->|yes| D[Delegate]
  C -->|no| E[Respond]
  D --> F[Verify] --> E
  classDef accent fill:{ACCENT},stroke:{ACCENT},color:#fff;
  class F accent;
```
Use `flowchart TD` for top-down when there are many branches; `LR` for pipelines.

### sequenceDiagram (handoff / protocol)
```
sequenceDiagram
  actor U as User
  participant O as Orchestrator
  participant W as Worker
  U->>O: request
  O->>W: subtask
  W-->>O: result
  O-->>U: answer
```

### timeline (evolution / roadmap)
```
timeline
  title How we got here
  2023 : Prompts
  2024 : Tools + RAG
  2025 : Agents
  2026 : Autonomous departments
```

### stateDiagram-v2 (lifecycle / modes)
```
stateDiagram-v2
  [*] --> Idle
  Idle --> Running : start
  Running --> Paused : pause
  Paused --> Running : resume
  Running --> Done : finish
  Done --> [*]
```

### erDiagram (data model / schema)
```
erDiagram
  AGENT ||--o{ SKILL : has
  AGENT ||--o{ MEMORY : writes
  SKILL }o--|| TOOL : uses
```

### classDiagram (type structure)
```
classDiagram
  class Agent {
    +identity
    +memory
    +plan()
  }
  Agent <|-- Orchestrator
  Agent o-- Skill
```

### mindmap (taxonomy / how it hangs together)
```
mindmap
  root((Deep agents))
    Planning
      decompose
      revise
    Delegation
    Memory
      persistent
    Context
```

### pie (proportions of a whole)
```
pie showData
  title Where time goes
  "Planning" : 30
  "Delegation" : 25
  "Memory" : 20
  "Context" : 25
```

### xychart-beta (trend / quantities over a range)
```
xychart-beta
  title "Growth"
  x-axis [Q1, Q2, Q3, Q4]
  y-axis "Users (k)" 0 --> 100
  bar [10, 30, 60, 95]
```

### quadrantChart (two-axis positioning)
```
quadrantChart
  title Shallow vs deep agents
  x-axis Low autonomy --> High autonomy
  y-axis Low memory --> High memory
  quadrant-1 Deep
  quadrant-2 Curious
  quadrant-3 Shallow
  quadrant-4 Reactive
  Chatbot: [0.2, 0.2]
  Deep agent: [0.82, 0.85]
```

### block-beta (system architecture, boxed)
```
block-beta
  columns 3
  Ingest["Ingest"] Core["Core engine"] Out["Output"]
  Ingest --> Core
  Core --> Out
```

### comparison table (structured X vs Y) - HTML, not Mermaid
When a feature-by-feature comparison is clearer as a table than a quadrant, author a small HTML table inside the wrapper's `<body>` (instead of `<pre class="mermaid">`), styled with the preset's `BG`/`textColor`/`ACCENT`. Keep it to <= 5 rows x 3 columns; bold/accent the winning cell.
