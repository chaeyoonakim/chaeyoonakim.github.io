---
layout: post
type: reflection
title: "91% accurate, 0.6% useful: lessons from a missed-appointments model"
date: 2026-10-04
summary: "A year on from a No. 10 hackathon challenge on non-attended hospital appointments: why the most accurate model was the least useful, and what ranking, calibration and target definition taught me."
categories: [machine-learning, healthcare, retrospective]
tags: [nhs, class-imbalance, scikit-learn, calibration, target-leakage, responsible-ai, hackathon]
---

> **TL;DR** — In September 2025 I worked on a hackathon challenge set by the No. 10
> data science team: predict which hospital outpatient appointments would be missed, so
> that support could reach patients before the slot was wasted. Our best model was
> **91% accurate and caught 37 of 6,612 missed appointments**. The useful result came
> from somewhere else entirely — ranking patients by risk rather than classifying them.
> This is the retro: what the data looked like, what I got wrong, and what I'd do
> differently.

## The problem

Missed outpatient appointments ("Did Not Attend", or DNA) cost the NHS money and push
waiting lists out. The challenge was simple to state: given an appointment and what we
know about the patient, how likely are they not to turn up?

The hackathon dataset had just under **500,000 appointment rows** and around 300
columns: appointment dates, specialty and provider codes, patient age and long-term
condition flags, frailty and admission-risk scores, and the outcome in
`DNA_DESCRIPTION`.

The code is on
[GitHub](https://github.com/chaeyoonakim/hack-the-state-reduce-non-attended-hospital-appointments).

## Lesson 1: defining the target is a policy decision, not a preprocessing step

`DNA_DESCRIPTION` has seven values, and only two are unambiguous:

| Outcome | What we did |
|---|---|
| Seen; Arrived late but was seen | **Attended** (1) |
| Did not attend – no advance warning; Arrived late and could not be seen | **Missed** (0) |
| Cancelled by the hospital; cancelled by the patient; appointment in the future | **Dropped** |

Dropping the last group removed about **123,000 rows (a quarter of the data)**. That
felt like tidying up at the time. Looking back, it was the most important modelling
choice we made, and we made it in five minutes.

A patient who cancels the day before and a patient who simply doesn't come are both
"not attending" from the clinic's point of view, but they need very different
interventions. Treating late arrivals who weren't seen as no-shows is also a choice:
some of those are transport or parking failures, not patient behaviour. **Whatever goes
into the target is what the model learns to blame**, so that definition deserves the
same scrutiny as the model itself — ideally with the people who run the clinics.

## Lesson 2: with an 8.8% minority class, accuracy is the wrong scoreboard

After cleaning, **8.8%** of appointments were missed. A model that predicts "everyone
attends" is 91.2% accurate before it learns anything.

Our Random Forest was 91% accurate. Its confusion matrix told the real story:

| | Predicted missed | Predicted attended |
|---|---:|---:|
| **Actually missed** | 37 | 6,575 |
| **Actually attended** | 129 | 68,429 |

It found **0.6%** of the missed appointments. The notebook still printed
"MODELING COMPLETE – READY FOR DEPLOYMENT!" underneath, which I now keep as a reminder
that a celebratory print statement is not a validation step.

The logistic regression with balanced class weights looked far worse on accuracy (56%)
but recovered **60% of missed appointments** — at the cost of flagging over 30,000
patients who would have attended. Neither threshold is "right"; each one is a
different operational trade-off.

One more trap: the notebook reported an **average precision of 0.94**. That was computed
for the *attended* class, whose baseline is already 0.91. For the class we actually
cared about, the baseline is 0.088, and that is the number a score should be compared
against. Always ask *which* class a metric is about.

## Lesson 3: the useful output was a ranking, not a yes/no

Cross-validated ROC-AUC was a modest **~0.62** for both models. That sounds
disappointing, until you stop asking the model to classify and use it to *prioritise*:

| Targeting | Patients | Missed-appointment rate | Share of all missed |
|---|---:|---:|---:|
| Everyone (baseline) | 75,170 | 8.8% | 100% |
| Top 10% by risk | 7,883 | **16.3%** | **19.5%** |
| Top 5% by risk | 4,030 | **18.4%** | 11.2% |

A clinic with capacity to phone 1 in 10 patients finds missed appointments at nearly
**twice the base rate**. That's the honest pitch: not "we predict no-shows" but "we
make a fixed outreach budget go about twice as far".

## Lesson 4: check calibration before anyone reads a score as a probability

The risk buckets showed the model ranking correctly, but over-confident at the top:

| Bucket | Mean predicted risk | Actual missed rate |
|---|---:|---:|
| Very low (≤5%) | 3.0% | 5.3% |
| Low (5–10%) | 7.8% | 8.9% |
| Moderate (10–15%) | 12.7% | 11.0% |
| High (15–25%) | 19.1% | 14.5% |
| Very high (>25%) | **34.6%** | **20.3%** |

Ranking survives this; a dashboard that says "35% chance of not attending" does not.
If a score is going to be shown to staff as a percentage, it needs calibrating
(isotonic or Platt scaling on a held-out set) first.

## Lesson 5: leakage hides in plausible-looking columns

Two kinds of leakage came up:

- **Columns recorded after the appointment.** Payment-by-Results flags and HRG codes
  are assigned when activity is coded, so they partly encode whether the patient was
  seen. We removed `SPELL_IN_PBR_NOT_IN_PBR`, `CORE_HRG_VERSION_CALCULATED` and the
  encoded `CORE_HRG`.
- **Target encoding.** For high-cardinality codes (provider, site, borough) we
  replaced each category with its historical attendance rate. Done naively on the full
  dataset, that leaks the test labels into the features, so the encoding used
  out-of-fold means with smoothing.

The question I now ask of every column: *would this value exist at the moment we'd
want to act?* For a reminder call, that's days before the appointment.

## Lesson 6: a synthetic demo can only show you your own assumptions

To demo the pipeline without sharing real data, the repo includes a synthetic
generator. It assigns attendance with a hand-written logistic formula: penalties for
evening slots, mental-health conditions and age bands. A model trained on that data
scores well (the README quotes ~85–90% accuracy) because it's rediscovering a formula
we wrote.

The real data gave ROC-AUC 0.62. Both numbers are true, but only one says anything
about patients. If I publish a synthetic demo again, its metrics will sit next to the
real-data metrics with a clear label, or not appear at all.

## Lesson 7: who gets flagged matters as much as how many

The feature set included ethnicity, postcode region, borough and
mental-health flags. These are predictive, and that's exactly the problem.

A risk score like this can be used to **support** patients (a reminder, a call,
transport help, a more convenient slot) or to **ration** them (overbooking their
clinic, deprioritising their referral). Same model, opposite effects on health
inequalities. Before deployment I'd want:

- an agreed use policy that limits the score to supportive interventions;
- performance and flag rates broken down by ethnicity, age, deprivation and condition
  groups;
- a check on whether removing sensitive features changes who gets help, not just the
  AUC.

## What I'd do differently

1. **Agree the target with operational staff first**, and model cancellations and
   genuine no-shows separately.
2. **Split by time, not at random.** Train on earlier months and test on later ones,
   because that's how the model would be used.
3. **Choose the threshold from capacity and cost**: how many calls a clinic can make,
   and what a missed slot costs, rather than defaulting to 0.5.
4. **Lead with PR-AUC for the minority class, recall at top-k and a calibration
   plot**, and keep accuracy out of the headline.
5. **Keep one model path.** A training script, a pipeline module and a notebook each
   ended up with a different model. Under hackathon pressure that drift is natural,
   but the README should describe the model that produced the results.

## The one line I'd keep

> A model that is right 91% of the time can still be useless. What it's for decides
> whether it's good.

## Further reading

- [**Accuracy matters, but usefulness matters more**](/2026/04/28/accuracy-matters-usefulness-more/)
  — an earlier, shorter take on the same theme.
- [**From Guardrails to Governance**](/2026/07/23/from-guardrails-to-governance/)
  — on turning responsible-AI principles into working controls.
