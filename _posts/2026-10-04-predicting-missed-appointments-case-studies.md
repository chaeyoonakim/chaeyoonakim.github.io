---
layout: post
type: reflection
title: "Predicting missed outpatient appointments: two case studies and what the evidence says"
date: 2026-10-04
summary: "A long-overdue write-up of my No. 10 hackathon DNA model, set alongside a review of a first-pass DNA model and the published evidence: what to check before trusting a score, what performance to expect, and how to pilot targeted calls safely."
categories: [machine-learning, healthcare, case-study]
tags: [nhs, outpatients, dna, class-imbalance, target-leakage, calibration, uplift, responsible-ai, governance]
---

> **Summary.** Predicting who will miss an outpatient appointment ("Did Not Attend", or
> DNA) is achievable but modest: published NHS general-outpatient models reach an AUROC
> of about **0.71–0.77**. Phoning high-risk patients does reduce DNAs (median **RR 0.61**
> across three RCTs). What hasn't yet been shown in an NHS setting is that
> *model-targeted* calls beat simpler targeting.
>
> This post brings together two case studies: a model I built at a No. 10 hackathon in
> September 2025, and a recent review of a first-pass DNA model on a synthetic trust
> extract. The same lessons came up in both. **Define the target carefully, hunt for
> leakage before reading any metric, validate the way the model will actually be used,
> and limit the score to supportive purposes.**

This write-up is about a year overdue. In the meantime I've spent more time with the DNA
literature and reviewed another team's first model. I've combined both into one report
rather than writing a retro that only tells half the story.

## Contents

1. Why DNAs matter, and how they're counted
2. Case study A: a hackathon model (September 2025)
3. Case study B: reviewing a first-pass DNA model (2026)
4. What the evidence says
5. Lessons across both cases
6. From model to pilot
7. Ethics and governance
8. Caveats
9. References

---

## 1. Why DNAs matter, and how they're counted

NHS England Digital reports **146.1 million outpatient appointments in 2024-25**, with a
DNA rate of **5.6%**, down from 5.9% in 2023-24 and 6.2% in 2019-20. The 2025-26
release puts it at **5.4% (8.2 million)**. Rates vary by specialty: in 2023-24,
cardiology (8.9%), ophthalmology (8.8%) and trauma & orthopaedics (7.9%) were among the
highest.

NHS England's outpatient guidance frames the opportunity: for an average-sized hospital,
a 1 percentage point reduction equates to about 7,500 fewer missed appointments a year.
It also notes that around 5% of patients, typically those on several concurrent
pathways, account for almost a quarter of all DNAs.

**Before quoting any DNA rate, check the definition.** The national definition is:

- **Numerator:** attendance status 3 ("did not attend – no advance warning") plus
  status 7 ("arrived late and could not be seen").
- **Denominator:** appointments excluding cancellations.

Using all booked appointments as the denominator understates the rate. Using a
different numerator overstates it. Local figures that look "well above average" often
turn out to use a different definition.

---

## 2. Case study A: a hackathon model (September 2025)

**Setting.** A hackathon challenge set by the No. 10 data science team: predict which
hospital outpatient appointments would be missed, so that support could reach patients
in time. The dataset had just under **500,000 appointment rows** and around 300 columns.
The code is on
[GitHub](https://github.com/chaeyoonakim/hack-the-state-reduce-non-attended-hospital-appointments).

**Target.** Of seven `DNA_DESCRIPTION` values, "Seen" and "Arrived late but was seen"
became *attended*, and "Did not attend" and "Arrived late and could not be seen" became
*missed*. Hospital cancellations, patient cancellations and future appointments were
dropped, which removed about **123,000 rows (a quarter of the data)**. This matched the
national definition, more by luck than by design. We made the decision in five minutes.

**What happened.**

| Model | Accuracy | Missed appointments caught | Note |
|---|---:|---:|---|
| Random Forest | 91% | **37 of 6,612 (0.6%)** | Predicted "attended" for almost everyone |
| Logistic regression (balanced weights) | 56% | 60% | Flagged over 30,000 patients who attended |

With **8.8%** of appointments missed, a model that predicts "everyone attends" is 91%
accurate before learning anything. The notebook still printed "READY FOR DEPLOYMENT".
It also reported an average precision of 0.94, but that was for the *attended* class,
whose baseline is 0.91. For missed appointments the baseline was 0.088.

**What worked: ranking.** Cross-validated ROC-AUC was about **0.62**, which is weak.
But using the score to prioritise rather than classify told a better story:

| Targeting | Patients | Missed rate | Share of all missed |
|---|---:|---:|---:|
| Everyone (baseline) | 75,170 | 8.8% | 100% |
| Top 10% by risk | 7,883 | **16.3%** | **19.5%** |
| Top 5% by risk | 4,030 | **18.4%** | 11.2% |

**What didn't: calibration.** The model ranked correctly but was over-confident at the
top. The "very high" bucket was predicted at **34.6%** but actually missed **20.3%**.

**Other issues we found.**

- **Leakage.** Payment-by-Results and HRG coding columns are assigned after the
  activity is coded, so they partly encode whether the patient was seen. We removed
  them. High-cardinality codes such as provider, site and borough were target-encoded
  with out-of-fold means and smoothing.
- **A synthetic demo that flattered the model.** The repo's synthetic data generator
  assigns attendance with a hand-written formula. Models trained on it scored about
  85–90% accuracy, because they were rediscovering our own assumptions. Real data gave
  0.62.
- **Model drift within the project.** A training script, a pipeline module and a
  notebook each ended up with a different model.

---

## 3. Case study B: reviewing a first-pass DNA model (2026)

**Setting.** A first DNA model built on a synthetic 12-month outpatient extract of about
6,000 appointments and roughly 600 DNAs (about 10%), across six specialties. The aim was
to give a booking team a weekly list of patients to call 7–14 days before their
appointment. I was asked to review it and to suggest how to pilot it.

I didn't assess the code line by line. I built a **checklist**, because the same failure
modes come up in almost every DNA model. My headline advice was that **an AUROC well
above 0.80 on this kind of data should be read as a warning sign, not a win**.

### What to check before reading any metric

**Target and cohort**
- **Hospital cancellations:** exclude them. The patient never had the chance to attend
  or miss, so coding these rows as "not DNA" mislabels them.
- **Patient cancellations:** exclude them to match the national definition, or model
  them as a separate class. Operationally, a cancellation with notice is a *success*
  for a reminder call, because the slot can be reused.
- **Cohort:** only appointments still booked at the weekly scoring time. Appointments
  booked after the scoring run can't be acted on.

**Leakage: three fields to interrogate**
- **`follow_up_booked`:** this is known only after the appointment, and is almost
  impossible after a DNA. Remove it. If it ranks near the top of feature importance,
  treat the performance figures as invalid.
- **`previous_dna_count`:** it must count only DNAs strictly before the scoring date.
  Red flags:
  - every DNA row has a count of at least 1, which means the current appointment is
    included;
  - values computed at the date of the extract;
  - counts that rise within a single week.
- **`reminder_sent`:** this is an *intervention*, not a patient trait. If texts go out
  about 5 days ahead, the flag isn't known 7–14 days ahead. If texts are suppressed for
  cancelled appointments, the flag encodes the outcome. If texts go only to patients
  with a mobile number, it's really a contact-data proxy.

**Validation**
- **Avoid random row splits.** The same patient's later appointments end up in
  training.
- **Split by time:** for example, train on September to May and test on June to August.
  Better still, run a rolling weekly backtest that rebuilds every feature as of each
  scoring date.
- **Tuning:** use grouped cross-validation by patient. Never use `patient_id` as a
  feature.
- **Confidence intervals:** repeat patients shrink the effective sample size, so
  bootstrap by patient.

**Data quality**
- **`imd_decile = -1`:** this is a sentinel code, not a decile. Used as a number, it
  reads as "more deprived than decile 1". Recode it to missing with an indicator, then
  look at who is unmatched. Likely groups:
  - Welsh or Scottish postcodes
  - new-build addresses
  - people of no fixed abode
  - overseas visitors

  Several of these are vulnerable groups, so the missingness may itself be predictive.
  Also check the IMD version: IoD 2025 has replaced IoD 2019, and their deciles aren't
  comparable.
- **Blank distances:** check how far they overlap with unmatched IMD.
- **Dates:** look for negative or very long lead times, and duplicate appointments from
  rebooking.

**Metrics**
- **Imbalance:** about 10% prevalence isn't severe. Avoid SMOTE or undersampling, which
  distort probabilities, unless you recalibrate afterwards.
- **What to report:**
  - AUROC with a confidence interval
  - PR-AUC against a no-skill baseline of about 0.10
  - **precision@k and recall@k at the real weekly call capacity**
  - calibration and Brier score
- **Baselines to beat:** a "previous DNA ≥ 1" rule, a "longest lead time" rule, and a
  logistic regression with splines on lead time and age. If gradient boosting can't
  clearly beat the spline regression on precision@k, use the regression for
  transparency.
- **Sample size:** about 600 events is small for flexible ML. Riley et al.'s
  minimum-sample-size criteria are a useful check on how many predictor parameters it
  can support.

**Risk is not benefit**
A risk model ranks patients by P(DNA). A booking team actually wants to rank by how much
a call *reduces* P(DNA). The highest-risk patients include people who are unreachable,
people who no longer need the appointment, and people who will miss it regardless.
Moderate-risk patients may gain more per call. Only randomised data can estimate that
uplift, which shapes the pilot design in section 6.

---

## 4. What the evidence says

### Realistic performance

| Setting | AUROC | Source | Note |
|---|---:|---|---|
| Guy's and St Thomas' (GSTT), general outpatient, 9.4 million appointments | **0.768** (0.75 on a later COVID-era test) | medRxiv preprint | Six predictors gave 0.75; untuned logistic regression scored 0.63 |
| Royal Berkshire, general outpatient | 0.71 | Cited in the GSTT preprint | Neural network |
| UCLH MRI only | 0.852 | *npj Digital Medicine* | Narrower task; not a general benchmark |
| My hackathon model | ~0.62 | Case study A | Fewer history features |

Precision at the very top of the ranking can still be useful when AUROC is modest. The
GSTT model flagged only 1.8% of appointments as likely DNAs, and over half of those were
correct.

### Predictors

| Predictor | Evidence | Practical note |
|---|---|---|
| Previous DNAs / attendance history | Consistently the strongest. NHS England calls it "a leading factor" | Compute it as of the scoring date and exclude the current appointment |
| Lead time (booking to appointment) | Strong. The top GSTT predictor | Watch for rebooking artefacts |
| Deprivation (IMD) | Consistent in UK data | The main equity question (section 7) |
| Age | Younger adults DNA more; non-linear | Use splines or bands |
| Sex | Weak and context-dependent | Hard to justify for allocation; keep it for auditing |
| Distance | Mixed findings | A crude proxy for travel burden |
| Time of day / day of week | Small effects | Use buckets |

A systematic review of 50 no-show model papers (Carreras-García et al., 2020) found that
previous no-shows were reported as the most significant predictor.

### Interventions

- **Model-targeted phone calls.** A JAMIA rapid review (Oikonomidi et al., 2022) found a
  **median RR of 0.61** across three RCTs, rated moderate certainty.
  - In Shah et al. (2016), no-shows were 22.8% with a call against 29.2% without, among
    2,247 patients with a predicted risk of at least 15%. That is about **16
    appointments assigned to a call per no-show prevented**, on an intention-to-treat
    basis (my calculation).
  - **Reach limits the effect.** Only about 65–73% of patients were successfully
    called across trials.
- **SMS.** SMS reminders work and perform about as well as calls (RR 0.99, Cochrane
  2013), at lower cost. Model-targeted SMS gave RR 0.91.
- **Message wording.** At Barts Health, adding the cost of a missed appointment to the
  SMS cut DNAs from 11.1% to 8.4% (Hallsworth et al., 2015), at no extra cost.
- **Overbooking.** The effect is uncertain. Combining ML no-show prediction with
  overbooking systematically gave Black patients worse waiting times (Samorani et al.,
  2022).
- **Vendor and press-release claims.** One example is the Mid and South Essex pilot,
  which reported a 30% fall in DNAs. These figures aren't peer-reviewed controlled
  evaluations. They show the idea can work in the NHS, but say little about the likely
  effect size.
- **The gap.** Whether *targeted* outreach beats *non-targeted* outreach, and its
  effects on equity and cost, remain under-studied.

---

## 5. Lessons across both cases

1. **The target is a policy decision.** Cancellations, late arrivals and future
   appointments all need a deliberate choice, made with the people who run the clinics
   and aligned with the national definition.
2. **Suspicious performance is a leakage signal.** A modest AUROC of 0.62 hid nothing,
   but a score above 0.80 on DNA data should prompt a hunt for post-appointment fields.
3. **Validate the way you'll deploy.** Use point-in-time features, a temporal split,
   patient-grouped folds, and a weekly backtest at the real call capacity.
4. **Report against capacity, not accuracy.** The useful questions are "DNAs captured
   per 100 calls" and "precision at top-k". Always state which class a metric is about.
5. **Calibrate before a score becomes a percentage on a screen.** Both cases needed it.
6. **A synthetic demo only reflects your assumptions.** Keep its metrics clearly
   separate from real-data results, or leave them out.
7. **Rank by benefit eventually, not just risk.** Design pilots so they produce the
   randomised data an uplift model needs.
8. **Prefer the transparent model when performance is close.** A well-specified
   logistic regression with splines is a strong baseline that is hard to beat on small
   data.

---

## 6. From model to pilot

A one-month pilot should be framed as a **feasibility study with a built-in control**,
not a rollout.

**Weekly workflow**
- Each Monday, score all live appointments 7–14 days ahead.
- Take the top **2 × C** appointments, where C is call capacity.
- Randomise **at patient level**, 1:1, to *call plus usual SMS* or *usual SMS only*.
  Stratify by specialty and risk band.
- If capacity allows, a third arm that calls the top 2 × C by a simple rule (previous
  DNA, then longest lead time) tests whether the model beats simple targeting, which is
  the gap the evidence identifies.

**The call** is a scripted, supportive conversation. It confirms the appointment, offers
easy cancellation or rebooking, and covers transport, interpreter, carer and access
needs.

**Outcomes**
- **Primary:** DNA (status 3 or 7), analysed by intention to treat.
- **Secondary:**
  - cancellations with at least 48 hours' notice, and whether the slot was refilled
  - reach rate
  - staff minutes per DNA prevented
  - reasons captured
  - post-DNA discharge rates, which should not rise

**Power.** Suppose the top-risk group has a 25% baseline DNA rate.
- Detecting 25% → 15% (RR ≈ 0.61) at 80% power and α = 0.05 needs about **250
  randomised appointments per arm**.
- A Shah-sized effect (25% → about 19.5%) needs about **900 per arm**.

At low volumes a month is underpowered for effectiveness, so say so up front.

**Approvals.** Check the plan with the HRA "Is my study research?" tool. Randomisation
can tip a project into research. A regression-discontinuity comparison around the
capacity cut-off, which needs no randomisation, is one fallback.

---

## 7. Ethics and governance

**The same score can help or harm.** A call is supportive and low-burden. Steering calls
towards deprived patients, who miss more appointments, could *reduce* inequalities. A US
safety-net RCT found model-driven phone outreach narrowed the no-show gap for Black
patients (36% vs 42%). The same score becomes harmful if it's used to overbook,
deprioritise, or discharge after a DNA.

NHS England's DNA guidance warns that low DNA rates are "not always indicative of an
accessible service design" where services discharge patients most likely to DNA. Write a
**purpose limitation** into the DPIA and the standard operating procedure: the score is
used only to offer support.

**Sensitive features**
- **IMD:** keep it. Dropping it won't remove its effect, because distance and history act
  as proxies. Document the reasoning and audit what happens.
- **Sex:** drop it unless it materially improves calibration, but keep auditing by sex.
- **Age:** keep it, and audit outcomes for older patients.

**Fairness checks** for a beneficial, capacity-limited intervention, by IMD quintile
(including unmatched), age band, sex and specialty:
- calibration within each group;
- recall at k, i.e. the share of each group's DNAs that were flagged;
- each group's share of calls compared with its share of DNAs.

**UK frameworks**
- **UK GDPR and ICO guidance on AI:** complete a DPIA before the pilot. The likely lawful
  bases are Article 6(1)(e) and Article 9(2)(h). Article 22 shouldn't apply, because a
  human decides whether to call.
- **DCB0129 / DCB0160:** an in-house model puts the trust in both the manufacturer and
  deployer roles. Keep it proportionate: name a Clinical Safety Officer and keep a short
  hazard log.
- **NICE Evidence Standards Framework:** a Tier A system service. Standard 4, on
  inequalities and bias, still applies.
- **TRIPOD+AI:** use it to document development and validation, even for internal work.
- **Algorithmic Transparency Recording Standard:** probably not mandatory for an NHS
  trust, but publishing a record is good practice.
- **EHIA:** complete an equality and health inequalities impact assessment alongside the
  DPIA.

---

## 8. Caveats

- **Synthetic data.** Case study B used a synthetic extract, and the hackathon included
  synthetic demo data. Repeat every check on real data under IG approval.
- **Where the trials come from.** Most targeted-call trials are from outside the UK and
  from settings with higher baseline no-show rates (18–29%). Relative effects may shrink
  in NHS clinics with lower DNA rates and existing SMS reminders.
- **Evidence quality.** The GSTT model is a preprint. The vendor and press-release
  figures aren't peer-reviewed.
- **My own calculations.** The calls-per-DNA figure and the power calculations are my
  derivations from published numbers. Treat them as planning estimates.
- **Local interpretation.** The governance points depend on local interpretation.
  Confirm them with the DPO, CSO and R&D office.

---

## 9. References

- NHS England Digital — [Hospital Outpatient Activity 2024-25](https://digital.nhs.uk/data-and-information/publications/statistical/hospital-outpatient-activity/2024-25/summary-reports) and [2025-26](https://digital.nhs.uk/data-and-information/publications/statistical/hospital-outpatient-activity/2025-26)
- NHS England — [Reducing did not attends (DNAs) in outpatient services](https://www.england.nhs.uk/long-read/reducing-did-not-attends-dnas-in-outpatient-services/)
- NHS England — [NHS AI expansion to help tackle missed appointments](https://www.england.nhs.uk/2024/03/nhs-ai-expansion-to-help-tackle-missed-appointments-and-improve-waiting-times/)
- GSTT DNA prediction model — [medRxiv preprint](https://www.medrxiv.org/content/10.1101/2022.01.24.22269733.full.pdf)
- UCLH MRI no-show prediction — [*npj Digital Medicine*](https://www.nature.com/articles/s41746-019-0103-3)
- Carreras-García et al. (2020) — [Patient no-show prediction: a systematic literature review](https://pmc.ncbi.nlm.nih.gov/articles/PMC7517206/)
- Oikonomidi et al. (2022), JAMIA — [Predictive model-based interventions to reduce outpatient no-shows: a rapid systematic review](https://pmc.ncbi.nlm.nih.gov/articles/PMC9933067)
- Shah et al. (2016), J Gen Intern Med — [Targeted reminder phone calls to patients at high risk of no-show](https://link.springer.com/article/10.1007/s11606-016-3813-0)
- Gurol-Urganci et al. (2013), Cochrane — [Mobile phone messaging reminders for attendance at healthcare appointments](https://cochranelibrary.com/cdsr/doi/10.1002/14651858.CD007458.pub2/abstract)
- Hallsworth et al. (2015), PLoS ONE — Stating appointment costs in SMS reminders reduces missed hospital appointments
- Samorani et al. (2022), MSOM — [Overbooked and overlooked: machine learning and racial bias in medical appointment scheduling](https://www.researchgate.net/publication/353993892_Overbooked_and_Overlooked_Machine_Learning_and_Racial_Bias_in_Medical_Appointment_Scheduling)
- J Gen Intern Med (2023) — [Model-driven phone outreach and racial disparities in no-shows](https://pmc.ncbi.nlm.nih.gov/articles/PMC10150669/)
- Imperial College Healthcare — [Using volunteers to reduce DNA rates among the most deprived](https://www.imperial.nhs.uk/about-us/blog/using-volunteers-to-reduce-did-not-attend-rate-amongst-the-most-deprived)
- ICO — [Guidance on AI and data protection: accountability and governance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/guidance-on-ai-and-data-protection/what-are-the-accountability-and-governance-implications-of-ai/)
- NICE — [Evidence Standards Framework for digital health technologies](https://www.nice.org.uk/corporate/ecd7/chapter/section-c-evidence-standards-tables)
- Collins et al. (2024), BMJ — [TRIPOD+AI](https://discovery.ucl.ac.uk/id/eprint/10191161/)
- UK Government — [Algorithmic Transparency Recording Standard hub](https://www.gov.uk/government/collections/algorithmic-transparency-recording-standard-hub)
- GIRFT — [Clinically-led general surgery outpatient guide](https://gettingitrightfirsttime.co.uk/wp-content/uploads/2023/07/ClinicallyledGeneralSurgeryOutpatientGuideJuly23FINAL-V1.pdf)

## Further reading on this site

- [**Accuracy matters, but usefulness matters more**](/2026/04/28/accuracy-matters-usefulness-more/)
- [**From Guardrails to Governance**](/2026/07/23/from-guardrails-to-governance/)
