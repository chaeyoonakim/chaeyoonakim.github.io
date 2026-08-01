---
layout: post
type: reflection
title: "Where Regex Ends: Practical NER for PII in Free Text"
date: 2026-07-17
categories: [nlp, data-science]
tags: [ner, spacy, presidio, text-processing, pii, nlp, python]
summary: "Running spaCy NER (via Presidio) to catch names in free text — model selection as a recall dial, the confidence score you can't threshold, domain shift, and why de-identification is a recall-first problem."
---

> Notes from wiring a Named Entity Recognition layer into a PII-detection pipeline.
> Light context in my [NoteGuard retro](https://chaeyoonakim.github.io/2026/07/10/noteguard-one-month-retro/);
> this post is the NLP, not the project.

Most PII in structured-ish text has a *format*. NHS numbers, postcodes, emails, phone
numbers, clinician registration IDs — regex and a dictionary lookup get you very high
precision *and* recall, because the target is a pattern. The moment you need to redact
**names in free text**, that whole approach falls over:

- "Match any Title-Case token" over-redacts — half a clinical note is capitalised.
- A fixed name dictionary (a gazetteer) only knows names you've already seen.

Detecting an open class of entities, in context, from tokens with no fixed shape, is a
**statistical sequence-labelling** problem. That's Named Entity Recognition. Here are the
practical, transferable things I learned running spaCy NER as that layer — the parts the
quickstarts skip.

## Two different problems, two different tools

It's worth being explicit about *why* you switch tools, because it's a precision/recall
story:

| Target | Nature | Tool | Typical error profile |
|---|---|---|---|
| NHS number, postcode, email | Closed, formatted | Regex / rules | ≈0 on well-formed input; misses only malformed cases |
| Person / location names | Open class, context-dependent | NER (trained model) | Both precision **and** recall < 1 — you *design around* that |

Regex failure is a formatting edge case. NER failure is statistical and constant. Once you
accept that the name layer will never hit 1.0, the engineering becomes: *choose the
operating point, then build layers that compensate.*

## The stack: Presidio + spaCy

[Presidio](https://microsoft.github.io/presidio/) is orchestration — it runs a set of
recognisers over an NLP engine and returns typed spans (`PERSON`, `LOCATION`, …). spaCy is
the NLP engine doing the actual sequence labelling. One detail that cost me an afternoon:
if you build `AnalyzerEngine()` with no config, it defaults to expecting spaCy's **large**
model and fails at *import* time if it's absent. Pin the model explicitly, and make it a
parameter you can tune:

```python
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

provider = NlpEngineProvider(nlp_configuration={
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": model}],   # <- a hyperparameter
})
engine = AnalyzerEngine(nlp_engine=provider.create_engine(), supported_languages=["en"])
results = engine.analyze(text, language="en", entities=["PERSON", "LOCATION"])
spans = [text[r.start:r.end] for r in results]
```

## Model size is a recall dial, not a detail

spaCy's English pipelines (`sm` / `md` / `lg`) differ in size and in whether they ship word
vectors — and that translates directly into how well they generalise to **names they never
saw in training** (the whole point). Treat the choice as a hyperparameter you tune against
a recall target and a deployment budget, not a default you accept.

Concretely, on one deliberately awkward sentence:

```
"Contacted GP Dr. Ethel Joanne Duffy. Nurse Jasmine Freda Murray reviewed.
 Seen by Dr Sarah Chen."

en_core_web_sm  (~12 MB) → ['Ethel Joanne Duffy', 'Murray', 'Sarah Chen']
en_core_web_md  (~40 MB) → ['Ethel Joanne Duffy', 'Nurse Jasmine', 'Freda Murray', 'Sarah Chen']
en_core_web_lg  (~560 MB) → better still
```

`sm` caught one full name but only the surname of the second person — "Jasmine Freda" would
have leaked. `md` covered both. For a recall-sensitive task that difference is the whole
game, and `md` was the sweet spot: meaningfully better than `sm`, ~14× smaller than `lg`.
The right framing: **recall vs. footprint vs. latency** is a curve, and you pick a point on
it on purpose.

## Gotcha 1 — the confidence score you can't threshold

The instinctive next move is "only redact if confidence > 0.x". It doesn't work here.
Presidio's spaCy recogniser assigns every entity a **flat score (0.85)** — a correct name
and a garbage detection come back *identical*. spaCy's NER doesn't surface calibrated
per-span probabilities on that path, so there's nothing real to rank by.

The lesson generalises: **before you design confidence-based logic, check whether your
model actually emits a meaningful confidence.** A lot of NLP components return a constant or
an uncalibrated proxy. If you can't threshold, you filter on *other* signals — gazetteers,
context words, POS, or a downstream rule — not on the score.

## Gotcha 2 — spans and tokenisation, not just labels

NER returns **character offsets**, and multi-token names don't always come back as one
clean span. Above, `md` split the second person into `'Nurse Jasmine'` + `'Freda Murray'` —
it even swallowed the role word "Nurse". If your redaction replaces detected spans in place,
partial coverage means partial leaks, and boundary slop means you sometimes delete a
non-name token. Span alignment and tokenisation quietly matter more than the entity label
you were focused on. Budget for a pass that reconciles overlapping/partial spans, and an
independent check for whatever the spans missed.

## Gotcha 3 — domain shift is why "Subcut" becomes a person

spaCy's English models are trained on web/news text (OntoNotes), not clinical notes. Run
them on hospital prose and you get systematic, *confident* errors on domain vocabulary: the
abbreviation **"Subcut"** (subcutaneous) gets tagged `PERSON`. This is textbook **domain
shift** — a model evaluated outside its training distribution fails in structured ways on
in-domain jargon.

Your options are the usual domain-adaptation ladder:

1. **Train / fine-tune** an in-domain NER model — best, most expensive.
2. **Swap to a domain model** — e.g. a clinical de-id transformer trained on i2b2 —
   better in-domain, heavier, and often US-centric.
3. **Patch with a gazetteer / stop-list** — cheap, explainable, incomplete:

```python
_NER_STOPWORDS = frozenset({"subcut", "subcutaneous", "obs", "sats", "nad",
                            "afebrile", "pneumomediastinum", ...})

def detect_names(text):
    return [n for n in ner_persons(text)
            if len(n) > 2 and n.lower() not in _NER_STOPWORDS]
```

Note what that stop-list *is*: a small **precision repair** bolted onto a **recall-oriented**
model. Which is the theme of the whole post.

## Gotcha 4 — a model in the loop makes tests non-deterministic

The moment detection depends on whether a model is installed/loaded, the unit tests for your
*deterministic* layers (the regex rules) start depending on it too, and go flaky across
environments. Standard fix for ML-in-the-loop code: **stub the model by default** in the
test suite (an autouse fixture pinning a no-op detector), and inject a fake only in the one
test that exercises the NER path. Test each layer as the thing it actually is.

## The asymmetry that should drive your evaluation

De-identification has a lopsided cost function. A **false negative** (a missed name) is a
privacy leak. A **false positive** (over-redaction) is just noise in the output. Those are
not equally bad, so you don't optimise F1 — you optimise **recall first**, accept the
precision hit, then buy precision back cheaply (stop-lists) and cover the recall gap with an
independent audit that flags anything suspicious that survived.

Practically, that means your eval report should lead with **recall on names**, not a single
aggregate F1 — and it should be **stratified**, which brings up the part that's easy to skip.

## Recall is not uniform — measure it by subgroup

Because these models are trained largely on Western/English text, **recall is lower for
names of non-English origin.** In a redaction task that's not a neutral miss: those people
carry a *higher* residual re-identification risk than everyone else. It's a fairness problem
hiding inside an aggregate metric. As a data scientist the obligation is concrete — don't
report one recall number; **stratify recall by name origin** and report the spread.
Mitigations are gazetteers for known local names, multilingual/clinical models, and simply
saying the limitation out loud.

## The transferable shape

Strip the domain away and the design is reusable for any PII / entity-extraction pipeline:

```
deterministic rules  →  probabilistic NER  →  high-precision audit  →  hard gate
(formatted IDs)         (open-class names,     (catches what NER        (the guarantee;
                         recall boost)          missed, precisely)       never the model)
```

NER is the only probabilistic component, so it's the one thing you never let *be* the
guarantee — you let it improve the odds, and you put a deterministic check on either side of
it. That framing — recall-oriented model in the middle, precision repair and a hard gate
around it — is the part I'd carry to the next text-extraction problem, clinical or not.

## Takeaways

- **Model size is a recall hyperparameter** — pick a point on the recall/footprint curve on
  purpose; don't accept a default.
- **Don't build on a confidence score you haven't verified is calibrated** — Presidio's
  spaCy score is a flat constant.
- **Expect domain shift** — repair precision with gazetteers, chase recall with a better/
  in-domain model.
- **Tune recall-first for PII**, and report recall **stratified by subgroup**, not a single F1.
- **Stub models in tests** so your deterministic layers stay deterministic.
