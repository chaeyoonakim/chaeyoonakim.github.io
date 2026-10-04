---
layout: post
type: reflection
title: "Would my own models pass? Auditing five ML models against my evaluation checklist"
date: 2026-10-04
summary: "A model register of every trained machine-learning model in my public repositories, from MSc coursework to a hackathon DNA model, each re-read against the evaluation checklist from my AUROC guide. What held up, what didn't, and the backlog to fix it."
categories: [machine-learning, evaluation, retrospective]
tags: [model-register, model-cards, auroc, ndcg, calibration, validation, naive-bayes, logistic-regression, random-forest, mlp, svm]
---

> **TL;DR** — I wrote
> [a guide to evaluating predictive models](/2026/10/04/field-guide-to-evaluating-predictive-models/), then
> turned its checklist on myself. My public GitHub holds **five trained ML models**
> built between 2020 and 2025. **All five report a performance number. Only one also
> reports uncertainty, and none checks performance across subgroups.** Two re-reads
> found problems I hadn't noticed at the time:
>
> - a coursework poster whose conclusion ("Naive Bayes beats logistic regression")
>   contradicts its own table;
> - a regression evaluated only on the data it was trained on.
>
> The strongest entry, CitySAT, held up because an external challenge forced a blind
> test set on it.

## "Would it pass your own checklist?"

Writing an evaluation guide is the easy part. The awkward question comes afterwards:
**if a reviewer applied it to my own repositories, what would they find?**

So I did the review. This post is the result, written as a **model register**: one
entry per model, with the same fields each time. That's the format NHS England's
model-card template and the TRIPOD+AI checklist push towards. Each entry records what
was built, what was reported, what the checklist would have asked for, and what to do
about the gap.

> **"A checklist you only apply to other people's models is a style guide, not a
> standard."**

## Scope: what counts as an ML predictive model here

**In scope:** models that were **trained on data** to predict an outcome or a label,
and are published in my repositories:

| # | Model | Repository | Year | Task |
|---:|---|---|---|---|
| 1 | Linear regression: suicide rates | [msc-data-science-projects](https://github.com/chaeyoonakim/msc-data-science-projects) | 2020–21 | Regression |
| 2 | Naive Bayes vs logistic regression: CIFAR-10 cat vs dog | [inm431-inm427-machine-learning-neural-computing](https://github.com/chaeyoonakim/inm431-inm427-machine-learning-neural-computing) | 2021 | Binary image classification |
| 3 | SVM vs MLP (with a CNN reference): CIFAR-10 | same repository | 2021 | Binary and 10-class image classification |
| 4 | **CitySAT**: semantic answer-type prediction | [smart-2021-at-answer-type-prediction](https://github.com/chaeyoonakim/smart-2021-at-answer-type-prediction) | 2021 | Multi-class classification and ranking |
| 5 | Missed-appointment (DNA) risk model | [hack-the-state-reduce-non-attended-hospital-appointments](https://github.com/chaeyoonakim/hack-the-state-reduce-non-attended-hospital-appointments) | 2025 | Binary risk prediction |

**Out of scope:**
- **Generative and LLM systems** (RAG agents, chatbots, LLM classifiers), which need
  different evaluation: faithfulness, groundedness and task success.
- **Rule-based scorers and statistical projections**, which have no trained model.
- **Off-the-shelf pre-trained components**, such as the spaCy NER inside my PII tools,
  where I tuned the pipeline but didn't train the model.

## The scorecard

Each model was scored on seven questions taken from the guide:

1. **Metric fit.** Does the headline metric suit the task and class balance?
2. **Baseline.** Is it compared with chance or a simple rule?
3. **Held-out test.** Is it evaluated on data the model never saw?
4. **Uncertainty.** Is there a confidence interval, standard deviation or similar?
5. **Operating point.** Is it judged where it would be used (top-k, a threshold)?
6. **Calibration.** If scores are read as probabilities, are they calibrated?
7. **Subgroups.** Is performance broken down by class or population group?

✅ = done, ◐ = partly, ✗ = not done, — = not applicable.

| Model | Metric fit | Baseline | Held-out | Uncertainty | Operating point | Calibration | Subgroups |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| 1. Suicide-rate regression | ◐ | ✗ | ✗ | ✗ | — | — | ✗ |
| 2. NB vs LR (cat/dog) | ✅ | ◐ | ✅ | ✗ | — | — | ✗ |
| 3. SVM vs MLP (CIFAR-10) | ◐ | ◐ | ✅ | ◐ | — | — | ✗ |
| 4. CitySAT | ✅ | ✅ | ✅ | ✗ | ✅ | — | ◐ |
| 5. DNA risk model | ◐ | ◐ | ◐ | ◐ | ✅ | ◐ | ✗ |

Reading down the columns is more revealing than reading across:

- **Held-out testing** is the habit that stuck. Four of five did it.
- **Uncertainty** was almost always missing.
- **Subgroup analysis** never happened, not even a per-class breakdown.

---

## Register entries

### 1. Linear regression: suicide rates (MSc, 2020–21)

| Field | Entry |
|---|---|
| **Question** | Do national well-being indicators explain suicide rates, with a focus on rising rates among young women in South Korea? |
| **Data** | Merged country–year–sex–age panel: suicide rates per 100k, plus World Happiness Report indicators (GDP, family, health, freedom, trust) |
| **Model** | Ordinary least squares, `sklearn.linear_model.LinearRegression`, on all numeric columns |
| **Reported** | Mean absolute error **7.80** suicides per 100k |
| **How it was measured** | Predictions on the **same data the model was fitted on** |

**What the checklist finds**

- **No held-out data.** An in-sample MAE flatters the model. It measures memorisation
  as much as prediction, and with country–year panels the right test is to hold out
  later years or whole countries.
- **No baseline, and the one number available is a warning.** The median target value
  is **6.54 per 100k**, smaller than the model's average error of 7.80. Without the MAE
  of simply predicting the median, I can't show the model beats doing nothing.
- **Design issues the coefficients reveal.**
  - The two sex dummies have equal and opposite coefficients (±6.68): the classic
    dummy-variable trap, where both levels are included alongside an intercept.
  - The preview shows the same target value repeated across years for one
    country–sex–age group, which suggests the merge duplicated rows. Duplicates inflate
    the effective sample size and leak between any random split.
- **Subgroups.** The research question is about young women, yet error was never
  reported for that group.

**Verdict:** an exploratory fit, not an evaluated model. Its value was the data work
around it.

### 2. Naive Bayes vs logistic regression: CIFAR-10 cat vs dog (MSc, 2021)

| Field | Entry |
|---|---|
| **Question** | Which classifier separates cats from dogs better on raw pixels, with and without PCA? |
| **Data** | CIFAR-10 classes 3 and 5. Training 10,000 images (70/30 train/validation), test 2,000 images, balanced |
| **Model** | Gaussian Naive Bayes and nominal logistic regression (MATLAB), at PCA k ∈ {30, 50, 80, 100} |
| **Reported** | Best NB test accuracy **57.9%**; best LR test accuracy **62.1%**. ROC curves and AUROC compared across PCA settings |

**What the checklist finds**

- **The conclusion contradicts the table.** The poster's evaluation section concludes
  "Classification Accuracy: NBC > LGC", yet its own best-model results show logistic
  regression ahead (62.1% vs 57.9%). This is the most useful finding of the whole
  audit: **write the conclusion from the numbers, and check it against the table
  before publishing**.
- **The baseline was implicit.** With balanced classes, chance is 50%, so the two
  models add **7.9 and 12.1 points over chance**. That framing is more honest than
  "around 60%".
- **No uncertainty.** On 2,000 test images, a 95% interval for an accuracy near 60% is
  roughly ±2.1 points (normal approximation). The NB–LR gap is larger than that, but
  most of the PCA comparisons fall within it.
- **Good habit.** A separate validation split was used for choosing k, keeping the test
  set for the final number.

**Verdict:** sound design, conclusion wrongly stated. One sentence to fix.

### 3. SVM vs MLP, with a CNN reference: CIFAR-10 (MSc, 2021)

| Field | Entry |
|---|---|
| **Question** | How do an SVM and a multi-layer perceptron compare on image classification, with a CNN as a reference point? |
| **Data** | CIFAR-10: a cat/dog subset for the SVM; all 10 classes (10,000 test images) for the MLP and CNN |
| **Model** | SVM on pixels; PyTorch MLP tuned by 3-fold grid search over depth (3, 5, 7 layers) and width factor; the PyTorch tutorial CNN as reference |
| **Reported** | SVM cat/dog accuracy **57.7%–60.7%** across settings (SD about 1–1.7 points). MLP 10-class test accuracy **50–52%**. CNN reference **54–55%** |

**What the checklist finds**

- **The comparison isn't like-for-like.** The SVM figures are binary (chance 50%); the
  MLP and CNN figures are 10-class (chance 10%). Side by side, "60% vs 52%" looks like
  the SVM won. In fact the MLP is **42 points over its chance level**, against about 10
  for the SVM, on a much harder task. **Always quote chance next to accuracy when tasks
  differ.**
- **Overfitting signal.** The tuned MLP's training loss kept falling (to about 0.64 by
  epoch 10) while test accuracy stayed near 52%. A validation curve would have shown
  where to stop.
- **Partial uncertainty.** The SVM runs report standard deviations, which is good. The
  neural-network figures are single runs from one random seed.
- **Subgroups.** There's no per-class accuracy, yet CIFAR-10 errors are very uneven
  between classes, and cat vs dog is notoriously the hardest pair.

**Verdict:** a reasonable learning exercise, but the headline comparison needs
re-framing against chance.

### 4. CitySAT: semantic answer-type prediction (MSc dissertation, ISWC 2021)

| Field | Entry |
|---|---|
| **Question** | Given a natural-language question, predict its answer category (boolean, literal or resource) and the expected types (e.g. `dbo:Person`) from the DBpedia ontology |
| **Data** | SMART 2021 DBpedia dataset. 80/20 train/validation split; official blind test set scored by the organisers |
| **Model** | Two-stage hybrid. Logistic regression for category (**98.36%** accuracy) and for literal type (**97.90%**); a multi-layer perceptron ranking about 760 resource types |
| **Reported** | Final test **accuracy 0.984, NDCG@5 0.842, NDCG@10 0.854**; validation 0.973 / 0.736 / 0.738. **1st place** on the leaderboard |

**What the checklist finds**

- **This is the model that passes.** The metrics fit the task (accuracy for the
  category, NDCG@k for a ranked type list), there are external baselines (the previous
  best NDCG@5/@10 were about 0.80 / 0.79), and an independent party scored it on a
  blind test set.
- **Validation–test agreement was tracked.** Six submissions were each logged with
  their configuration, and their validation and test scores moved together. That
  record is what makes the result credible.
- **But six test submissions is a mild risk.** Each submission tells you something
  about the test set. Choosing the "best" of six by test score is light-touch
  overfitting to the leaderboard. It would be safer to choose by validation score and
  submit once, or to report all six (which the README does).
- **No uncertainty.** A bootstrap interval on test NDCG would show whether the gaps of
  under 0.01 between versions 4–6 mean anything. They probably don't.
- **Partial subgroup analysis.** Results are reported per component (category, literal,
  resource) but not per answer category or ontology branch, where errors usually
  concentrate.

**Verdict:** the strongest entry. External evaluation did what self-discipline didn't
always do.

### 5. Missed-appointment (DNA) risk model (No. 10 hackathon, 2025)

| Field | Entry |
|---|---|
| **Question** | Which outpatient appointments will be missed, so that support can reach patients beforehand? |
| **Data** | About 500,000 appointments; 375,848 after excluding cancellations and future appointments; **8.8%** missed |
| **Model** | Logistic regression (balanced class weights) and Random Forest on 35 engineered features; a gradient-boosted variant in the training script |
| **Reported** | Test AUROC **0.615 (LR) / 0.621 (RF)**; 5-fold cross-validated AUROC **0.615 ± 0.002 / 0.618 ± 0.003**. Top-10% risk group missed rate **16.3% vs 8.8%** baseline (19.5% of all missed appointments). Calibration by risk bucket |

**What the checklist finds**

- **Operating point: done well.** The top-10% and top-5% analysis is exactly the
  "precision@k at capacity" view the guide recommends, and it turned a weak AUROC into
  a usable message: about twice as efficient as calling at random.
- **Calibration: checked, not fixed.** The risk buckets showed over-confidence at the
  top (34.6% predicted vs 20.3% observed). No recalibration followed.
- **Metric fit: mixed.**
  - The notebook headlined accuracy (91%) for a model that caught 0.6% of missed
    appointments.
  - It reported average precision (0.94) for the majority class, so the score was
    measuring the easy class.
- **Validation design: partial.** A stratified random split means the same patient's
  appointments can sit in both training and test, and later months can predict earlier
  ones. A temporal, patient-grouped split would give a more honest (probably lower)
  AUROC.
- **Uncertainty: partial.** The cross-validation standard deviations are a good start,
  but they measure fold-to-fold variation, not uncertainty for a deployment period.
- **Baseline: partial.** Two models were compared and prevalence was quoted, but there
  was no comparison with a simple rule such as "previous DNA ≥ 1".
- **Subgroups: not done.** This is a serious gap, because the feature set included
  ethnicity, postcode geography and mental-health flags. That is exactly
  where a fairness audit is needed.

**Verdict:** the most operationally honest analysis of the five, and the one where the
missing checks matter most.

---

## What the audit says about me, not just the models

**First, external evaluation beats good intentions.** The only model that passes is
the one an outside organiser scored blind. Where I set my own tests, I sometimes
skipped them (entry 1), mis-summarised them (entry 2) or compared the wrong things
(entry 3). For anything that matters, **find a way to be evaluated by someone who
doesn't share your hopes for the model**: a challenge, a held-out set you can't touch,
or a colleague's review.

**Second, chance and baselines are the most-skipped line, and the cheapest.** In three
entries, simply stating the chance level would have changed how the results read. It
costs one sentence.

**Third, I've never broken a model down by subgroup.** Not by class, not by patient
group, not by country or sex, including when the research question was explicitly
about a subgroup. That has to become a default, especially for health data.

> **"The habits you skip on coursework are the ones you'll skip under hackathon
> pressure. Build them while the stakes are low."**

## The evaluation backlog

What I'd do, in priority order, if I picked these up again:

| Priority | Model | Action | What it would show |
|---:|---|---|---|
| 1 | DNA risk model | Re-run with a temporal, patient-grouped split; recalibrate (isotonic or Platt); report precision@k, calibration and recall by ethnicity, deprivation, age and sex; compare with a "previous DNA" rule | Whether the model is fair and better than a one-line rule, the two questions that decide deployment |
| 2 | Suicide-rate regression | De-duplicate the merge, drop one sex dummy, hold out later years or whole countries, report MAE against a median baseline, and break error down by sex and age | Whether the model predicts anything at all, and for the group the question is about |
| 3 | CitySAT | Bootstrap 95% intervals on test NDCG@5/@10; per-category and per-ontology-branch accuracy | Whether the version differences are real, and where the errors concentrate |
| 4 | SVM vs MLP | Report chance levels; per-class accuracy; validation curves for the MLP; three or more seeds | A fair comparison across tasks, and a stopping point for training |
| 5 | NB vs LR | Correct the conclusion; add 95% intervals on test accuracy | A poster whose conclusion matches its table |

## Register format I'll use from now on

For every new model, one entry with these fields, stored next to the code:

```text
Model:            name, version, date, repository
Question:         the decision it supports, in one sentence
Data:             source, period, size, positive rate, exclusions
Validation:       split design (temporal / grouped / external), leakage checks
Discrimination:   AUROC or task metric, with 95% CI, against chance and a simple baseline
Operating point:  precision@k / recall@k (or the threshold) at real capacity
Calibration:      slope, intercept, reliability plot (if scores are shown as probabilities)
Subgroups:        the metrics above, by the groups that matter for the question
Known issues:     what this register entry found, and what was done about it
```

It's essentially a lightweight model card. The point isn't the template; it's
committing in advance to the questions, so the answers can't be skipped quietly.

## Further reading on this site

- [**What does an AUROC of 0.75 actually mean?**](/2026/10/04/field-guide-to-evaluating-predictive-models/)
  — the checklist used for this audit.
- [**Predicting missed outpatient appointments: two case studies and what the evidence says**](/2026/10/04/predicting-missed-appointments-case-studies/)
  — entry 5 in full, with the published evidence.
- [**Accuracy matters, but usefulness matters more**](/2026/04/28/accuracy-matters-usefulness-more/)
