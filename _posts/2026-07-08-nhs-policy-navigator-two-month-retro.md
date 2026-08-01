---
layout: post
type: reflection
title: "From Build-in-a-Day to v1.1.0: Two Months of NHS Policy Navigator"
date: 2026-07-08
categories: [rag, engineering, retrospective]
tags: [nhs-policy-navigator, RAP, mongodb, gemini, agentic-rag, adaptive-retrieval, ci, retrospective]
summary: "A retro on the two-month journey of NHS Policy Navigator — from a one-day MongoDB hackathon build in May, through right-sizing the stack for a public-data PoC, to a Gold RAP product with a Query Router (v1.1.0) presented as a prototype in July."
---

In May 2026 I walked into the MongoDB Agentic Evolution Hackathon in London on the strength of a one-line pitch: *"Build in a day. Shape the future of AI Agents."* Two months later, [**NHS Policy Navigator**](https://github.com/chaeyoonakim/nhs-policy-navigator) — an adaptive retrieval agent over the NHS 10 Year Health Plan — is a documented, tested, CI-gated product at **v1.1.0**, and I've just presented it as a prototype. This is the retro on those two months: what happened in each phase, and what each one taught me.

## First, what "adaptive retrieval" means

The hackathon theme was **Adaptive Retrieval**, and it's worth pinning down because it's more than a simple RAG pipeline. Simple RAG is a fixed recipe: embed the question, fetch the nearest chunks, generate an answer — the same path for every query, forever.

An adaptive retrieval agent reasons about *how* to retrieve before it retrieves, and learns from how it went. In NHS Policy Navigator, every query runs the pipeline:

```
classify → select sources → select strategy → retrieve → re-rank → generate → evaluate → log → adapt
```

- **Classify** the question as `factual`, `conceptual`, `comparative`, or `gap_analysis`.
- **Route to sources by type** — a factual question needs only the plan; a gap-analysis question also pulls live NHS news and post-publication documents.
- **Select a retrieval strategy** — keyword, vector, or hybrid search on MongoDB Atlas — starting from a sensible default per type.
- **Adapt** — once a query type has enough history (≥5 runs), the agent switches to whichever strategy has scored best for that type, with the full decision trail logged.

The difference in one sentence: simple RAG executes a pipeline; adaptive retrieval *chooses* one, watches the outcome, and changes its choices over time.

## Phase 1: the day it started (May)

The hackathon brief came with the stack chosen for me: the sponsored database and infrastructure, and a limited LLM model. That meant my first ever day on **MongoDB Atlas** and **AWS**, with **ElevenLabs** in the sponsor mix too — the only familiar face was LangSmith.

What made a one-day build survivable was everything transferable underneath: the AI engineering fundamentals didn't change just because the logos did. Within about an hour I was comfortable wiring an MVP dashboard, and the day produced a working proof of concept — a **FastAPI** backend (there from the very first commit, whose docstring still reads *"Run with: `uvicorn app:app --reload`"*), MongoDB Atlas vector and full-text search, GPT for embeddings and generation with a LangSmith wrapper, and a single-file front end.

FastAPI earned its place within that first hour, and kept earning it for two months. On day one, a `pip install` and one uvicorn command gave me a running API with interactive docs generated for free, Pydantic validating the request bodies, and the front end served from the same process. And because the app is a standard ASGI object, the exact same code runs under uvicorn locally (today it's `make run`, which wraps `python -m uvicorn nhs_policy_navigator.app:app --reload`) and ships to Vercel unchanged — the deployment story in Phase 2 was easy precisely because of this framework choice on day one.

But it was hackathon code: one flat folder, no tests, no CI, `print()` statements for logging, and an "adaptive" story that was more aspiration than implementation.

**Lesson: the stack is swappable; the fundamentals are the asset.** Being new to Atlas and AWS on the same morning cost me an hour, not the day.

## Phase 2: right-sizing the stack (about two days)

The first post-hackathon job wasn't a feature — it was deciding what the PoC actually needed, as I moved development towards an NHS tenant context and away from the hackathon workspace.

The honest answer: not much. The required functionality — news feeds, sorting, routing, summarising — is not a complex job. So the sponsor-shaped, over-specified engines came off: the voice agent (ElevenLabs) went, and the AWS dependencies went with it. **MongoDB Atlas stayed unchanged** — it carries the retrieval core, and it also connected me with a team at NHS England already working with MongoDB, turning a hackathon dependency into a professional conversation.

What made the slimming-down safe is the nature of the data. The corpus is **public open sources** — the published NHS 10 Year Health Plan and NHS England's public feeds — so its query vector index is perfectly fine sitting on a shared cluster. No sensitive data, no isolation requirement, no heavyweight infrastructure justified. The free tiers of Atlas and Gemini were simply *adequate for the job*, which also means the project can be handed over without anyone procuring anything.

The weightiest single decision in the move was **swapping the embedding model from GPT to Gemini** (`gemini-embedding-001`). Embeddings are not interchangeable between models: a query embedded by one model cannot be searched against an index built by another — the vectors live in different spaces, and the search silently returns nothing rather than failing loudly. So the model exchange wasn't a config change; it meant **re-embedding the entire corpus** (all 586 chunks), **recreating the Atlas vector index** with dimensions to match, and **re-exporting the bootstrap dump** in the repo so anyone loading it gets Gemini-space vectors rather than orphaned GPT ones. It's also why the pipeline has a dedicated `reembed.py`: after this experience, re-embedding is a first-class operation in the codebase, not a one-off script.

The front end deliberately stayed at hack level while the backend was overhauled: the UI could wait; the foundations couldn't.

**Lesson: spec the engineering to the job, not to the sponsor table.** A PoC on public data doesn't need the machinery a production clinical system would — and pretending it does just adds drag.

## Phase 3: structure before features (June, v1.0.0)

With the stack right-sized, I resisted the urge to build the shiny feature and instead repackaged everything to **Gold RAP** — the NHS Reproducible Analytical Pipeline standard: a proper `src/` package, environment-driven configuration with no hard-coded secrets, structured logging, a pytest suite, GitHub Actions CI, a changelog, and documentation that lives next to the code. That shipped as **v1.0.0** on 24 June.

It felt slow. It wasn't. Every feature afterwards landed on a base that tested itself across three Python versions (3.10–3.12) and refused to merge if anything broke. The test count went from 0 to 29 in that first PR and climbed to 49 by the end — all mocked, no network or database required — and not once did I ship a regression I had to chase in production. **The boring work bought me speed later.**

## The architecture, briefly

The shape that came out of phases 2 and 3 is three layers (the full write-up is in [`docs/architecture.md`](https://github.com/chaeyoonakim/nhs-policy-navigator/blob/main/docs/architecture.md)):

1. **Front end** — a single-file vanilla HTML/JS page styled to the NHS England identity.
2. **API** — a FastAPI application exposing query, stats, history, digest and health endpoints.
3. **Agent + data** — the adaptive retrieval agent over MongoDB Atlas, with Gemini for embeddings and generation.

Three Atlas collections carry the state: `nhs_chunks` (embedded plan chunks with vector and full-text indexes), `query_log` (the append-only decision trail that powers both the history tab and the strategy learning), and `query_digest` (deduplicated question clusters behind the main-page digest). Live NHS England RSS is fetched at query time, and everything — tagging, dedup routing, news and publication fetches, re-ranking — degrades gracefully: a failure never blocks an answer.

**Embeddings** come from a thin `httpx` wrapper around Gemini's `embedContent` REST endpoint — calling REST directly avoids SDK versioning churn and keeps the dependency surface small. The wrapper uses Gemini's asymmetric task types: document chunks are embedded with `RETRIEVAL_DOCUMENT` at ingestion time, and each incoming question is embedded with `RETRIEVAL_QUERY` at ask time, so the two sides of the vector search are optimised for their roles rather than embedded identically. Input text is truncated to 8,000 characters, and the query embedding does double duty — it powers the Atlas vector search *and* the Query Router's dedup check (cosine ≥ 0.92 against existing clusters). The repo also ships a pre-built dump of all 586 embedded chunks (`dump/nhs_chunks.json`), so a new environment can load the corpus and go, without re-running ingestion or spending any embedding calls.

**Deployment** is on **Vercel**: `vercel.json` routes `/api/*` to the FastAPI app running as a Python serverless function (`api/index.py`) and serves the front end as static files — no server to manage, and every push to `main` redeploys the live demo.

**CI** lives in the repo as a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs on every push and pull request: `ruff` linting, `black` formatting checks, and the pytest suite, in a matrix across Python 3.10, 3.11 and 3.12. Alongside it sit the local guardrails — a `Makefile` for the common tasks and `pre-commit` hooks that catch lint and formatting issues before they ever reach CI.

## Phase 4: the Query Router, and naming what's actually adaptive (June, v1.1.0)

The headline feature — shipped as **v1.1.0** the day after v1.0.0, which tells you how much the groundwork helped — was the **Query Router**. Every query is tagged with NHS-domain facets (care setting and professional group), and near-identical questions are deduplicated into a categorised digest: the front page shows the top-10 most-asked topics per category, while a separate Previous Queries tab keeps the full append-only history. A supervising LLM produces the executive summary; live news and publication feeds fill in what happened after the plan was published.

### How the scoring actually works now

Two scores drive the system, and neither is shown as stars any more:

- **Re-ranking score** — during retrieval, an LLM scores each retrieved chunk for relevance to the query (0–10) and re-orders them before generation.
- **Answer quality score** — after generation, the model self-evaluates the answer (1–5). That score is written to `query_log` alongside the query type, strategy, and sources — and it's what the strategy switch reads: once a query type has five or more logged runs, the agent picks the strategy with the best average score for that type.

Earlier versions displayed these as Selection & Relevance star marks in the UI. I took that display off in v1.1.0 — the scores are the model grading itself, and presenting them to users as if they were a quality guarantee felt misleading. The scoring still runs, but it now works silently in the log, where its real job is: steering the adaptation. What users see instead is the plain-English **"This query"** legend — which type the question was, which sources were searched, which strategy was used.

### The honesty audit

Partway through I asked a blunt question of my own codebase: *what here is genuinely adaptive, and what just looks it?* The honest answer was humbling. The strategy selection is real — it reads logged outcomes and changes behaviour — but it's **greedy** (once a strategy wins, the others stop being tried), it learns from the **model grading itself** rather than from users, and it averages over all time with no sense of recency. It's a bandit with the exploration switched off.

Writing that down, without flattering the work, turned out to be the most valuable artefact of the two months. It's the backlog for what comes next.

## Phase 5: process lessons the hard way

**Separate capability from presentation.** I tried to ship the Query Router as one pull request, bundling the backend feature and the UI on top of it. Splitting them into two reviewable PRs hit the obvious-in-hindsight wall: the UI commits *depended* on the feature, so they couldn't merge independently. The fix was a stacked pair — feature PR into `main`, UI PR retargeted after it merged — plus a rebase and a careful tree-equality check. **Decide your review boundaries before you write the code, not after.**

**Iterate the UI deliberately, not accidentally.** I'd taken inspiration from how the Gmail team uses iterative design alongside machine learning, and from the NHS England data visualisation community of practice. The iteration worked — annotated screenshots drove real improvements (dropping the example pills and stats panels, the "This query" legend, top-10 per category) — but it churned across several PRs. A front-loaded UI spec would have turned four rounds into one.

**The tooling will surprise you.** Importing the UI design from Claude Design didn't work in the running session, so the handoff became a plain git patch; publishing the `v1.1.0` git tag was blocked by the environment, so tag and release notes go out manually. Neither was a disaster — both cost time I hadn't budgeted. **Confirm the mechanics of your handoffs and your release process early**, while they're cheap to fix.

## What I'm proud of

- A one-day hackathon build is now a documented, tested, CI-gated, versioned product — **v1.1.0** — sized honestly for what a public-data PoC needs.
- The documentation tells the truth about what the system does, including where the "adaptive" label is aspirational.
- Graceful degradation everywhere: a failure never blocks an answer.
- Small, green, reversible increments the whole way.

## What's next

The final slide of the prototype presentation lists the open items — deliberately incomplete, because these aren't my guesses. They're what I've already collected as feedback from potential users of the prototype:

- **More example questions**, and a **TL;DR answer** mode.
- **Benchmark / evaluation** — an offline harness with a labelled query set, so retrieval changes are validated rather than self-reported.
- **Functions beyond summarisation**, and additional dashboard components.
- **Extending the corpus with the 10 Year Workforce Plan** — and deciding the right pairing: workforce plan alongside the 10 Year Health Plan, or bridging back to the Long Term Workforce Plan.

Under the hood, the adaptive honesty audit sets the engineering order: a genuine user feedback signal instead of the model marking its own homework, ε-greedy exploration so strategies keep being sampled, recency-weighted scoring so the system tracks drift, and reciprocal-rank fusion in place of concatenate-and-dedupe.

The demo answered questions. The product should get better at answering them.

---

*NHS Policy Navigator runs on MongoDB Atlas and Google Gemini. Live demo: <https://nhs-policy-navigator.vercel.app>*
