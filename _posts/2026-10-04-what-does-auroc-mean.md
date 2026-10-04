---
layout: post
type: reflection
title: "What does an AUROC of 0.75 actually mean? A field guide to evaluating predictive models"
date: 2026-10-04
summary: "A plain-English guide to the metrics behind a risk model — confusion matrix, precision and recall, AUROC, PR-AUC, precision@k and calibration — with a ten-patient worked example and real numbers from a missed-appointments model."
categories: [machine-learning, evaluation, explainer]
tags: [auroc, roc-curve, precision-recall, calibration, brier-score, class-imbalance, healthcare]
---

> **TL;DR** — **AUROC is the probability that the model gives a randomly chosen
> positive case a higher score than a randomly chosen negative case.** An AUROC of 0.75
> means the model ranks that pair correctly three times out of four. AUROC says nothing
> about how many patients you should act on, whether the scores are real probabilities,
> or how well the model works at the top of the list where you actually spend effort.
> For those, you need precision@k, PR-AUC and calibration.

While writing up
[two case studies on predicting missed outpatient appointments](/2026/10/04/predicting-missed-appointments-case-studies/),
I kept using shorthand like "AUROC 0.77", "PR-AUC against a 0.10 baseline" and
"precision@20". This post unpacks those terms properly. The examples use missed
hospital appointments ("Did Not Attend", or DNA), but the ideas apply to any risk model.

## 1. Start with what the model actually outputs

Most risk models output a **score** for each case, usually between 0 and 1. For example:
"Patient A: 0.82, Patient B: 0.07". The score is not yet a decision. Something else
turns it into one:

- a **threshold** ("flag everyone above 0.5"), or
- a **capacity** ("call the 20 highest-scoring patients this week").

Some metrics judge the **scores themselves** (AUROC, PR-AUC, calibration). Others judge
the **decision** you make with them (accuracy, precision, recall, precision@k). Mixing
these up is the source of most confusion.

## 2. A ten-patient worked example

Ten appointments, sorted by the model's score. Three of them were actually missed:

| Rank | Score | Actually missed? |
|---:|---:|:---:|
| 1 | 0.90 | ✅ |
| 2 | 0.80 | — |
| 3 | 0.60 | ✅ |
| 4 | 0.50 | — |
| 5 | 0.40 | — |
| 6 | 0.30 | ✅ |
| 7 | 0.20 | — |
| 8 | 0.15 | — |
| 9 | 0.10 | — |
| 10 | 0.05 | — |

We'll keep coming back to this table.

## 3. The confusion matrix and its children

Pick a threshold, say **0.5**. Everyone at or above it is predicted "will miss" (ranks
1–4):

| | Predicted miss | Predicted attend |
|---|---:|---:|
| **Actually missed** | 2 (true positives, TP) | 1 (false negative, FN) |
| **Actually attended** | 2 (false positives, FP) | 5 (true negatives, TN) |

Every threshold metric is a ratio from this table:

| Metric | Formula | Plain English | Worked example |
|---|---|---|---:|
| **Accuracy** | (TP + TN) / all | How often is the model right? | 7 / 10 = 0.70 |
| **Precision** (positive predictive value) | TP / (TP + FP) | Of those we flagged, how many really missed? | 2 / 4 = 0.50 |
| **Recall** (sensitivity) | TP / (TP + FN) | Of those who missed, how many did we flag? | 2 / 3 = 0.67 |
| **Specificity** | TN / (TN + FP) | Of those who attended, how many did we leave alone? | 5 / 7 = 0.71 |
| **F1** | harmonic mean of precision and recall | One number balancing the two | 0.57 |

Change the threshold and every number changes. That's why a single precision or recall
figure, without the threshold or capacity behind it, isn't very informative.

### Why accuracy misleads when the outcome is rare

In my hackathon model, only **8.8%** of appointments were missed. A Random Forest
reached **91% accuracy**, the same as predicting "everyone attends". Its confusion
matrix showed the problem:

- **Recall:** 37 of 6,612 missed appointments, i.e. **0.6%**.
- **Precision:** 37 of 166 flagged, i.e. 22%.

A logistic regression with balanced class weights had only 56% accuracy, but recall of
**60%**. The cost was precision of 12%: it flagged about 30,000 patients who attended.

Neither model is "the accurate one". They make different trade-offs, and accuracy hides
both. **When one class is rare, leave accuracy out of the headline.**

## 4. ROC curve and AUROC: what they actually mean

### The ROC curve

Instead of picking one threshold, sweep through **every** possible threshold. At each
one, plot:

- **y-axis:** the true positive rate (recall), i.e. the share of missed appointments
  flagged;
- **x-axis:** the false positive rate (1 − specificity), i.e. the share of attended
  appointments wrongly flagged.

A perfect model goes straight up to the top-left corner: it catches everyone before it
makes a single false alarm. A useless model follows the diagonal: every extra true
positive costs a proportional false alarm. The name "receiver operating characteristic"
comes from radar engineering, which is why it sounds odd.

### AUROC is the area under that curve

The cleaner definition is this:

> **AUROC = the probability that a randomly chosen positive case scores higher than a
> randomly chosen negative case.**

Check it on the worked example. There are 3 missed × 7 attended = **21 pairs**. Count
the pairs where the missed patient scored higher:

- The missed patient at 0.90 beats all 7 attenders → 7
- The missed patient at 0.60 beats 6 of them (not 0.80) → 6
- The missed patient at 0.30 beats 4 of them (0.20, 0.15, 0.10, 0.05) → 4

**17 / 21 = 0.81.** That is exactly the area under the ROC curve for this data.

### Reading AUROC values

| AUROC | Interpretation |
|---|---|
| 0.5 | No better than a coin toss at ordering pairs |
| 0.6–0.7 | Weak, but can still help prioritise |
| 0.7–0.8 | Typical of good real-world healthcare risk models |
| 0.8–0.9 | Strong; on noisy behavioural outcomes, also a prompt to check for leakage |
| > 0.9 | Rare for messy human outcomes; investigate before celebrating |

For context, published NHS general-outpatient DNA models sit at about 0.71–0.77.

### What AUROC doesn't tell you

1. **It ignores the threshold and your capacity.** Two models with the same AUROC can
   differ a lot in the top 20 cases, which is the only part a team with 20 calls a week
   ever sees.
2. **It is insensitive to how rare the outcome is.** Because the false positive rate
   divides by *all* negatives, a model can raise thousands of false alarms while the
   false positive rate barely moves when negatives are plentiful.
3. **It ignores calibration.** Multiply every score by 0.5 and the AUROC is unchanged,
   because the ordering is unchanged. The scores now say "half as likely" for everyone.
4. **It averages over thresholds you would never use.** The far-right part of the
   curve, where you flag almost everyone, counts just as much as the useful top-left
   part.

## 5. Precision–recall curve and PR-AUC

The PR curve plots **precision against recall** as the threshold moves. Unlike ROC, it
focuses on the positive class, so it reacts sharply when the outcome is rare.

The summary number is usually **average precision (AP)**, often called PR-AUC. It
averages precision at each point where a true positive is found, going down the ranked
list.

On the worked example:

- Rank 1 is a hit: precision 1/1 = 1.00.
- Rank 3 is a hit: precision 2/3 = 0.67.
- Rank 6 is a hit: precision 3/6 = 0.50.

**AP = (1.00 + 0.67 + 0.50) / 3 = 0.72.**

**The crucial detail is that PR-AUC's no-skill baseline equals the prevalence.** A
random model has AP ≈ the share of positives. Here that's 0.30; for DNAs it's about
0.09. So:

- AP = 0.30 on a 10% outcome is a meaningful lift (3× baseline).
- AP = 0.94 on a 91% outcome is barely better than guessing.

That second case was a trap in my hackathon notebook: the 0.94 was computed for the
*attended* class. **Always ask which class a metric is about, and what its baseline
is.**

## 6. Precision@k and recall@k: metrics for teams with finite capacity

If a booking team can make **k** calls a week, the only part of the ranking that matters
is the top k:

- **Precision@k:** of the k patients we call, how many would have missed?
- **Recall@k:** of all the patients who would have missed, how many are in our top k?

In the worked example, at k = 3: precision@3 = 2/3 and recall@3 = 2/3.

In the hackathon model, the top 10% by risk had a **16.3%** missed rate against an
**8.8%** baseline, and contained **19.5%** of all missed appointments. That is roughly
twice as efficient as calling at random. A manager can act on that sentence, which isn't
true of "AUROC 0.62".

A related way to say the same thing is **lift**: precision@k divided by prevalence.

## 7. Calibration: can you read the score as a probability?

A model is **well calibrated** if, among patients it scores at 0.2, about 20% actually
miss. Check it by grouping predictions into bins and comparing the predicted with the
observed rate:

| Risk bucket | Mean predicted | Actual missed |
|---|---:|---:|
| Very low | 3.0% | 5.3% |
| Moderate | 12.7% | 11.0% |
| Very high | **34.6%** | **20.3%** |

These are real numbers from my hackathon model. It **ranked** patients correctly, which
is why AUROC was fine, but was **over-confident** at the top. Showing staff "35% chance"
for a group that actually misses 20% of the time would mislead them.

Useful summaries:

- **Calibration slope.** Ideally 1. Below 1 means predictions are too extreme; above 1
  means too timid.
- **Calibration-in-the-large** (intercept). Is the average prediction right overall?
- **Brier score.** The mean of (score − outcome)², from 0 (perfect) upwards. It mixes
  calibration and discrimination. On the worked example it's 0.18. Compare it with the
  Brier score of always predicting the prevalence.

**Fixes:** Platt scaling or isotonic regression, fitted on held-out data. Also beware
resampling tricks such as SMOTE and undersampling: they deliberately distort the class
balance, so they distort probabilities too.

## 8. Which metric should I report?

| Question you're answering | Metric |
|---|---|
| Does the model rank cases better than chance overall? | **AUROC**, with a confidence interval |
| How much better than chance is it on a rare outcome? | **PR-AUC**, stated next to its prevalence baseline |
| If we act on the top k each week, how well does that go? | **Precision@k, recall@k, lift** |
| Can staff read the score as a probability? | **Calibration plot, slope and intercept, Brier score** |
| At this threshold, what are the error trade-offs? | **Confusion matrix, precision, recall, specificity** |
| Does it work equally well across patient groups? | All of the above, **by subgroup** |
| Is the model worth using at all? | **Decision curve / net benefit**, against simple rules |

My default report for a healthcare risk model:

- AUROC with a confidence interval;
- PR-AUC with its baseline;
- precision@k at the real capacity;
- a calibration plot;
- all of the above broken down by key subgroups;
- a comparison with a simple rule, such as "previous DNA ≥ 1".

## 9. Five habits worth keeping

1. **Name the positive class.** "Precision 0.94" means nothing until you know whether
   it's for "missed" or "attended".
2. **Quote the baseline.** Prevalence for PR-AUC, 0.5 for AUROC, "everyone attends" for
   accuracy.
3. **Evaluate at the operating point.** That means your real threshold or capacity, not
   a default of 0.5.
4. **Check calibration before anyone sees a percentage.** Ranking well and being
   calibrated are different properties.
5. **Treat suspiciously good numbers as a bug report.** On noisy human outcomes, an
   AUROC above about 0.85 more often means leakage than genius.

## Further reading

- [**Predicting missed outpatient appointments: two case studies and what the evidence says**](/2026/10/04/predicting-missed-appointments-case-studies/)
  — where these metrics were put to work.
- [**Accuracy matters, but usefulness matters more**](/2026/04/28/accuracy-matters-usefulness-more/)
- Saito & Rehmsmeier (2015), PLoS ONE —
  [The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets](https://doi.org/10.1371/journal.pone.0118432)
- Van Calster et al. (2019), BMC Medicine —
  [Calibration: the Achilles heel of predictive analytics](https://doi.org/10.1186/s12916-019-1466-7)
- Vickers & Elkin (2006), Medical Decision Making —
  [Decision curve analysis: a novel method for evaluating prediction models](https://doi.org/10.1177/0272989X06295361)
