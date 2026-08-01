---
layout: post
type: reflection
title: "NoteGuard: a One-Month Retro"
date: 2026-07-10
categories: [healthcare-ai, engineering, retrospective]
tags: [nhs, de-identification, phi, llm, langgraph, healthcare-ai, retro]
summary: "Building the trust layer for clinical AI — from a hackathon hack to a deployed, honestly-measured de-identification agent."
---

> **TL;DR** — I built [NoteGuard](https://github.com/chaeyoonakim/noteguard-agent), a trust layer that de-identifies NHS clinical
> free-text so an LLM agent can safely draft discharge summaries, and *proves* the
> privacy with a measured number. It started at a hackathon as a privacy on-ramp for
> federated learning, got pivoted into a demoable product on the day, and then spent
> the next few weeks getting pruned, re-measured, and debugged into something I'd
> actually trust. This is the retro: what I started with, what I shipped, and the
> handful of things I got wrong on the way.

## How it started

NoteGuard began at the **{Tech: Europe} London AI Hackathon**. The original idea
wasn't an agent at all — it was the *privacy on-ramp for federated learning*: the
de-identification gate that would make NHS notes safe to train on before they went
into a federated/blockchain stack.

That framing died about an hour in. The hackathon had no federated-learning sponsor,
and the rubric rewarded **technical depth + wow + a real problem** — not governance
prose. So I kept the one thing that made NoteGuard *NoteGuard* — **measured,
NHS-aware de-identification of clinical free-text** — and rebuilt everything around it
into something you could actually demo:

> Messy NHS clinical notes go in → a safe, AI-drafted **discharge summary** comes out
> → and the model **provably never sees a single identifier**.

The dataset made the pivot easy: `NHSEDataScience/synthetic_clinical_notes` (Hugging
Face, MIT, fully synthetic) was literally built to evaluate AI-generated discharge
summaries. Perfect match — and because the identifiers live in structured tables next
to the free text, I could join them back and *measure* leakage against ground truth
instead of vibing it.

The one non-negotiable idea, then and now:

```
deidentify_in → assert_clean() → [ ONLY DE-IDENTIFIED TEXT ] → Gemini / Tavily
                                                                 ↓
                                                            reidentify_out → clinician
```

`assert_clean()` raises **before** the model or any tool sees anything. The model
can't leak what it never saw. Everything else in the system is negotiable; that line
is the spine.

## What it actually is

A small, deliberately boring pipeline:

- **`src/deid.py`** — the de-identification core. NHS-aware rules (NHS number, GMC/NMC,
  postcode, DOB, email, phone), a vault built from the dataset's structured tables so
  redaction is *exact and measurable*, consistent surrogates (same patient → same
  `[PERSON_1]` across a note), and a reversible date-shift. Std-lib only at its heart.
- **A LangGraph agent** — `deidentify_in → agent (Gemini + Tavily) → reidentify_out →
  compute_trust`. Tavily grounds the summary in public NICE/NHS guidance; it never
  sees patient text.
- **A trust panel** — the part that's supposed to *prove* it worked.
- **Deployed** as a Docker Hugging Face Space, auto-shipped from `main`.

## The month, in one arc

Here's the honest shape of it. Not a straight line.

### 1. The hackathon build (day one)

Clinician web UI, a `/process` endpoint, the note picker over the synthetic dataset,
the "what the AI sees" toggle, the compact discharge card, and a first pass at
clinician-name de-identification (GMC/NMC connector words, word-boundary fixes so
`Dia` didn't redact inside `Diastolic`). I also burned time on deployment yak-shaving —
Vercel, then Hugging Face Spaces (Docker) — before landing on something that stuck.

By the end of the day it demoed. It was also held together with tape.

### 2. Pruning to 1.0 (the "does this earn its keep?" pass)

After the event I did something I recommend to anyone who ships a hackathon repo:
I went through every dependency and asked *does this actually run in the deployed
thing?* Two didn't:

- **Superlinked** (semantic retrieval) — excluded from the Docker image, lazy-imported,
  never executed in production.
- **n8n** (a workflow proxy) — a three-node passthrough to my own API. Zero logic.

Both were there for hackathon sponsor-surface, not for the product. I cut them,
collapsed the graph, and shipped **1.0.0**. The repo lost ~190 lines and got honest.

If this sounds familiar, it's because it's the second time I've lived this exact
arc: in [the NHS Policy Navigator two-month retro]({% post_url 2026-07-08-nhs-policy-navigator-two-month-retro %})
the same post-hackathon pass stripped the over-specced sponsor engines (the voice
agent, the AWS dependencies) and right-sized the stack to what the product actually
needed — and there, too, the honesty audit that followed ("what here is genuinely
adaptive?") turned out to be the most valuable artefact. Apparently this is just what
week two after a hackathon is *for*.

Then I wired **auto-deploy** to the Space — and immediately hit a great little bug:
Hugging Face's git backend *rejects binary files committed to history*, and there was
a stray 0.14 MB PNG buried in the initial commit. The fix taught me something clean:
a deploy target isn't a source repo, so I push a single **orphan-commit snapshot** of
`main` instead of the full history. No history, no historical binaries, no problem.

### 3. The metric that was lying to me

This was the turning point of the whole month.

The trust panel proudly showed **RE-ID RISK: 0.0%** — while a note with
"Dr Ethel Joanne Duffy" and "Nurse Jasmine Freda Murray" sat *un-redacted* in what the
model saw. The number was computed from the **vault**: it only counted *known*
identifiers that survived. Arbitrary free-text names were never in the vault, so the
metric was structurally blind to the single most important failure mode.

A green metric that measures the wrong thing is worse than no metric. So I rebuilt the
panel to report **only** de-identification correctness:

- Dropped *faithfulness* and *grounded-sources* — those are answer-quality, not privacy.
- Added **`scan_pii`** — a **vault-independent** audit that scans what the model saw for
  residual PII, including a high-precision "person-title" heuristic
  (`Dr/Nurse/Consultant …` + a real-looking name) that catches free-text names the vault
  never knew about.
- The headline became a blunt **PASS / FAIL**, plus *Residual PII (model input)* that
  actually lists what leaked.

The same note that used to read 0.0% now reads **FAIL — Residual PII: 2**, and names
them. That felt like the moment NoteGuard started telling the truth.

### 4. Making de-id actually stronger

Reporting a leak is good; not leaking is better. I turned on **Presidio + spaCy NER**
(`en_core_web_md`) in the deployed image so free-text names with no vault entry get
*redacted*, not just flagged. NER is a recall boost, never a guarantee — so `scan_pii`
stays as the high-precision backstop, and `assert_clean()` stays as the hard gate.

### 5. The bug cascade (a.k.a. using your own product)

Then I did the most valuable thing I did all month: I *used the deployed app* on real
notes and screenshotted everything that looked wrong. Five real de-identification bugs
fell out in a row, each a tiny fix and a real lesson:

- **"Subcut" got redacted as `[PERSON_3]`.** spaCy mislabels clinical abbreviations as
  people, and Presidio scores every entity a flat 0.85 — so *confidence* can't save you.
  → a clinical-term allow-list.
- **`Admitted [DATE_X]` in the summary.** The prompt expected date *tokens*; the de-id
  produced *shifted dates*. The model hallucinated a token to fill the gap, and my
  safety net redacted it. → align the prompt with reality.
- **The patient's name was repeated in the title** — and then a better question:
  *why is the patient named in the summary at all?* → removed it entirely; the summary
  refers to "the patient".
- **`Admitted [redacted]`.** Same date mismatch, deeper. The fix was elegant: the
  date-shift is already *reversible*, so the model copies the shifted date it sees and
  the system restores the **true** admission date for the clinician — who never sees the
  fake one, and neither does the model see the real one.

None of these showed up in the unit tests. All of them showed up in five minutes of
poking the live app.

## What I got wrong (and would tell past-me)

- **Don't measure what's easy to measure — measure what matters.** My proudest number
  (0.0% re-id risk) was the most misleading thing in the app for weeks.
- **A hackathon repo is 40% product, 60% sponsor cosplay.** Pruning wasn't loss; it was
  the point where the thing became legible.
- **NER is not de-identification.** It's a probabilistic recall boost. Pair it with a
  deterministic gate (`assert_clean`) and a precise audit (`scan_pii`), and be honest
  that names of non-English origin have lower recall — that's an equity risk, not a
  footnote.
- **Use your own product.** Synthetic tests are necessary and insufficient. The bugs
  that mattered were all found by looking at real output.

## What's next

- **Recall** — a larger / clinical NER model, and catching single-token names the
  high-precision heuristic deliberately skips.
- **Structured dates** — first-class handling of admission vs. birth dates instead of
  one blanket shift.
- **Real-Trust evaluation** — everything so far is on synthetic data. Synthetic ≠ real;
  I frame it as *methodology*, not a finished product.
- **The federation nod** — the original vision, now a one-liner: each Trust runs
  NoteGuard locally, and only de-identified text ever leaves.

## The one line I'd keep

Pseudonymised ≠ anonymous — this is still personal data under UK GDPR, and the clinician
stays in the loop and signs off every summary. NoteGuard doesn't remove the human. It
just makes sure the machine only ever sees what it's allowed to — and, now, tells the
truth about whether it did.

## Further reading

- [**Where Regex Ends: Practical NER for PII in Free Text**](https://chaeyoonakim.github.io/2026/07/17/where-regex-ends-ner-for-pii/)
  — a technical zoom-in on the NER layer I mention above: Presidio + spaCy, model size as a
  recall dial, and why de-identification is a recall-first problem.

*Built with a de-identification core, LangGraph + Gemini, Tavily for public-guidance
grounding, and a lot of screenshots. Live on Hugging Face Spaces; code on
[GitHub](https://github.com/chaeyoonakim/noteguard-agent).*
