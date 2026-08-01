---
layout: post
type: reflection
title: "Prompting Gemini to generate Makaton-style symbol cards"
date: 2026-05-24
summary: "What I learnt about prompt engineering for consistent, licensing-safe AAC symbol generation while building the Getting Started with Makaton choice board."
tags: [gemini, image-generation, makaton, AAC, SEND, prompt-engineering]
---

## Background

While building [Getting Started with Makaton](https://github.com/chaeyoonakim/getting-started-with-makaton) — a digital AAC choice board for non-verbal and emerging-verbal pupils in UK SEN schools — I needed a set of symbol cards covering everyday school vocabulary: locations, actions, food, and communication controls.

Official Makaton symbols are licensed under a paid scheme, and ARASAAC/Mulberry symbols (the main open alternatives) are limited in coverage and stylistically inconsistent with each other. I decided to generate a bespoke set using Gemini image generation, targeting 16 core symbols.

---

## What I tried

The 16 symbols I needed fell into four groups:

| Group | Symbols |
|-------|---------|
| Locations | `bus`, `classroom`, `playground`, `toilet` |
| Actions | `sit`, `listen`, `look`, `work` |
| Food & drink | `snack`, `lunch`, `drink` |
| Communication controls | `choose`, `more`, `stop`, `finish`, `quiet` |

My first instinct was a simple prompt per card:

> *"A Makaton symbol for 'bus', simple line drawing, white background."*

The outputs were inconsistent — some photorealistic, some cartoon, some overly detailed. Unusable for a coherent choice board.

### Iteration 1 — locking the visual style

I added a shared style anchor to every prompt:

> *"Flat vector illustration, thick black outline, single subject centred on white background, no text, no shadows, suitable for a children's communication card."*

Consistency improved significantly. The symbols were now clearly from the same visual family.

### Iteration 2 — handling ambiguous concepts

Concrete nouns (`bus`, `toilet`) worked well immediately. Abstract communication controls were harder. An early `quiet` card came back as a sound-wave graphic — the opposite of what I needed.

Fixes:
- `quiet` → *"a person with one finger raised to lips"*
- `finish` → *"two open hands turned face-down simultaneously"* (describing the Makaton sign gesture directly)
- `choose` → *"a hand pointing at one of two objects"*

Describing the **Makaton signing gesture** rather than the concept produced the most recognisable results for abstract words.

### Iteration 3 — batch consistency

Generating cards one at a time led to subtle style drift between sessions. I standardised a single system prompt used for every card:

```
You are generating a symbol card for a UK SEN school communication board.
Style: flat vector, thick black outline (#000000, 3–4px), solid white background,
single subject centred with 16px padding, no text, no drop shadows, no gradients.
The symbol must be immediately recognisable to a child aged 5–11.
```

Running all 16 in one session with this as the fixed context kept the visual weight and line style consistent enough to use as a set.

---

## What worked well

- Describing **signing gestures** for abstract words, not the concepts themselves
- A **shared visual specification** in the system prompt (stroke weight, background, padding)
- Keeping the session alive across all 16 so Gemini could internally reference earlier outputs
- Keeping prompts short — adding more adjectives rarely helped and often confused the style

## What didn't work

- Asking Gemini to *"match the style of the previous card"* — it doesn't retain image context across turns, only text
- Generic terms like *"simple"* or *"minimalist"* without numeric constraints (stroke width, colour values)
- Generating communication controls without grounding them in a physical gesture

---

## Lessons learnt

**1. Visual specifications need numbers, not adjectives.** "Simple" means different things each run. `3px black outline, white background, 16px padding` is reproducible.

**2. For AAC symbols, gesture > concept.** Children and practitioners recognise Makaton signs from the hand shape. Prompting on the gesture rather than the word gave symbols that map to the physical sign, which matters for paired use with BSL/Makaton training.

**3. Batch in one session.** Style drift is real. All 16 in one context window beats 16 separate sessions.

**4. Licensing still needs documenting.** AI-generated images sidestep the ARASAAC/Mulberry licensing constraints, but I documented in the project's data dictionary that these are AI-generated originals and not derivatives of licensed symbol sets.

---

## Outputs

The 16 generated cards live at [`assets/cards/`](https://github.com/chaeyoonakim/getting-started-with-makaton/tree/main/assets/cards) in the Getting Started with Makaton repository and are loaded by the choice board's multi-source symbol resolver as the local cache layer — the first fallback before ARASAAC, Mulberry, and Sclera.
