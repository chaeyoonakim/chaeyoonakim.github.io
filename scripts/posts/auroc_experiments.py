"""Experiments and figures for the post "What does an AUROC of 0.75 actually mean?".

Run from the repository root:
    pip install numpy scipy scikit-learn matplotlib
    python scripts/posts/auroc_experiments.py

Prints every number quoted in the post and writes figures to assets/img/auroc/.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu, norm
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, brier_score_loss,
                             precision_recall_curve, roc_auc_score, roc_curve)

OUT = "assets/img/auroc"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#111111", "#52514e", "#e6e3df"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": MUTED,
    "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.8, "lines.linewidth": 2,
    "legend.frameon": False, "figure.dpi": 150, "savefig.bbox": "tight",
})
rng = np.random.default_rng(42)


def precision_at_k(y, s, k):
    top = np.argsort(-s)[:k]
    return y[top].mean()


def binormal(n, prevalence, d, sigma_pos=1.0, rng=rng):
    y = (rng.random(n) < prevalence).astype(int)
    s = np.where(y == 1, rng.normal(d, sigma_pos, n), rng.normal(0, 1, n))
    return y, s


# --- 1. Worked example -------------------------------------------------------
y = np.array([1, 0, 1, 0, 0, 1, 0, 0, 0, 0])
s = np.array([0.90, 0.80, 0.60, 0.50, 0.40, 0.30, 0.20, 0.15, 0.10, 0.05])
u = mannwhitneyu(s[y == 1], s[y == 0]).statistic
print("[1] AUROC", round(roc_auc_score(y, s), 3),
      "| U/(n1*n0)", round(u / (3 * 7), 3),
      "| AP", round(average_precision_score(y, s), 3),
      "| Brier", round(brier_score_loss(y, s), 3),
      "| Brier(prevalence)", round(brier_score_loss(y, np.full(10, 0.3)), 3))

fig, ax = plt.subplots(1, 2, figsize=(8, 3.6))
fpr, tpr, _ = roc_curve(y, s)
ax[0].plot([0, 1], [0, 1], color=MUTED, lw=1, ls="--", label="Chance (0.50)")
ax[0].step(fpr, tpr, where="post", color=BLUE, label="Model (AUROC 0.81)")
ax[0].fill_between(fpr, tpr, step="post", color=BLUE, alpha=0.12)
ax[0].set(xlabel="False positive rate", ylabel="True positive rate (recall)",
          title="ROC curve", xlim=(0, 1), ylim=(0, 1.02))
ax[0].legend(loc="lower right")
p, r, _ = precision_recall_curve(y, s)
ax[1].axhline(0.3, color=MUTED, lw=1, ls="--", label="Chance = prevalence (0.30)")
ax[1].step(r, p, where="post", color=ORANGE, label="Model (AP 0.72)")
ax[1].set(xlabel="Recall", ylabel="Precision", title="Precision–recall curve",
          xlim=(0, 1.02), ylim=(0, 1.05))
ax[1].legend(loc="lower left")
fig.savefig(f"{OUT}/worked-example-roc-pr.png")
plt.close(fig)

# --- 2. Prevalence: AUROC stays put, AP does not -----------------------------
d = np.sqrt(2) * norm.ppf(0.75)  # binormal equal-variance AUROC = Phi(d / sqrt(2))
print(f"[2] separation d = {d:.3f}")
fig, ax = plt.subplots(1, 2, figsize=(8, 3.6))
for prev, colour in [(0.5, BLUE), (0.1, ORANGE), (0.01, AQUA)]:
    yy, ss = binormal(200_000, prev, d)
    auc, ap = roc_auc_score(yy, ss), average_precision_score(yy, ss)
    k = int(0.1 * len(yy))
    lift = precision_at_k(yy, ss, k) / yy.mean()
    print(f"    prevalence {prev:>5.0%}: AUROC {auc:.3f}  AP {ap:.3f}  "
          f"AP/prevalence {ap / yy.mean():.1f}x  precision@top10% {precision_at_k(yy, ss, k):.3f}"
          f"  lift@10% {lift:.2f}x")
    f, t, _ = roc_curve(yy, ss)
    ax[0].plot(f, t, color=colour, label=f"{prev:.0%} prevalence")
    pp, rr, _ = precision_recall_curve(yy, ss)
    ax[1].plot(rr, pp, color=colour, label=f"{prev:.0%}: AP {ap:.2f}")
ax[0].plot([0, 1], [0, 1], color=MUTED, lw=1, ls="--")
ax[0].set(xlabel="False positive rate", ylabel="True positive rate",
          title="ROC: unchanged by prevalence", xlim=(0, 1), ylim=(0, 1.02))
ax[0].legend(loc="lower right")
ax[1].set(xlabel="Recall", ylabel="Precision",
          title="PR: sinks as positives get rarer", xlim=(0, 1), ylim=(0, 1.02))
ax[1].legend(loc="upper right")
fig.savefig(f"{OUT}/prevalence-roc-vs-pr.png")
plt.close(fig)

# --- 3. Same AUROC, different top of the list --------------------------------
sigma_b = 1.5
d_b = d * np.sqrt(1 + sigma_b**2) / np.sqrt(2)
print(f"[3] model B: d = {d_b:.3f}, sigma_pos = {sigma_b}")
fig, ax = plt.subplots(figsize=(4.6, 3.8))
for name, dd, sg, colour in [("Model A", d, 1.0, BLUE), ("Model B", d_b, sigma_b, ORANGE)]:
    yy, ss = binormal(200_000, 0.10, dd, sg)
    auc = roc_auc_score(yy, ss)
    p1 = precision_at_k(yy, ss, int(0.01 * len(yy)))
    p5 = precision_at_k(yy, ss, int(0.05 * len(yy)))
    p30 = precision_at_k(yy, ss, int(0.30 * len(yy)))
    print(f"    {name}: AUROC {auc:.3f}  precision@1% {p1:.3f}  @5% {p5:.3f}  @30% {p30:.3f}")
    f, t, _ = roc_curve(yy, ss)
    ax.plot(f, t, color=colour, label=f"{name} (AUROC {auc:.2f})")
ax.axvspan(0, 0.05, color=GRID, alpha=0.6, lw=0)
ax.text(0.06, 0.06, "the region a team\nwith finite capacity\nactually uses", color=MUTED, fontsize=8)
ax.plot([0, 1], [0, 1], color=MUTED, lw=1, ls="--")
ax.set(xlabel="False positive rate", ylabel="True positive rate",
       title="Same AUROC, different early retrieval", xlim=(0, 1), ylim=(0, 1.02))
ax.legend(loc="lower right")
fig.savefig(f"{OUT}/same-auroc-different-top.png")
plt.close(fig)

# --- 4. Calibration: ranking survives, probabilities do not ------------------
n = 60_000
X = rng.normal(size=(n, 3))
logit = -2.6 + X @ np.array([0.9, 0.6, 0.4])
yy = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
tr, ca, te = slice(0, 30_000), slice(30_000, 45_000), slice(45_000, n)
lr = LogisticRegression().fit(X[tr], yy[tr])
z_ca, z_te = lr.decision_function(X[ca]), lr.decision_function(X[te])
over = lambda z: 1 / (1 + np.exp(-(2.0 * z + 1.5)))  # overconfident, shifted up
raw = lr.predict_proba(X[te])[:, 1]
bad_ca, bad_te = over(z_ca), over(z_te)
iso = IsotonicRegression(out_of_bounds="clip").fit(bad_ca, yy[ca])
fixed = iso.predict(bad_te)


def cal_slope_intercept(y_, p_):
    lo = np.log(np.clip(p_, 1e-6, 1 - 1e-6) / np.clip(1 - p_, 1e-6, 1))
    m = LogisticRegression(C=1e6).fit(lo.reshape(-1, 1), y_)
    return m.coef_[0][0], m.intercept_[0]


print(f"[4] prevalence {yy[te].mean():.3f}")
for name, pr in [("well specified", raw), ("distorted", bad_te), ("isotonic-recalibrated", fixed)]:
    sl, ic = cal_slope_intercept(yy[te], pr)
    print(f"    {name:<22} AUROC {roc_auc_score(yy[te], pr):.3f}  Brier {brier_score_loss(yy[te], pr):.4f}"
          f"  mean p {pr.mean():.3f}  slope {sl:.2f}  intercept {ic:.2f}")
print(f"    Brier(always prevalence) {brier_score_loss(yy[te], np.full(len(yy[te]), yy[tr].mean())):.4f}")

fig, ax = plt.subplots(figsize=(4.6, 3.8))
for name, pr, colour in [("Distorted", bad_te, ORANGE), ("Recalibrated", fixed, BLUE)]:
    order = np.argsort(pr, kind="stable")
    groups = np.array_split(order, 10)  # ten equal-sized groups by predicted risk
    mp = [pr[g].mean() for g in groups]
    ob = [yy[te][g].mean() for g in groups]
    ax.plot(mp, ob, marker="o", ms=5, color=colour, label=name)
ax.plot([0, 1], [0, 1], color=MUTED, lw=1, ls="--", label="Perfect calibration")
ax.set(xlabel="Mean predicted risk (decile)", ylabel="Observed rate",
       title="Reliability diagram", xlim=(0, 0.65), ylim=(0, 0.65))
ax.legend(loc="upper left")
fig.savefig(f"{OUT}/reliability-diagram.png")
plt.close(fig)

# --- 5. Sampling uncertainty: bootstrap AUROC CIs -----------------------------
for n_rows in (600, 6_000, 60_000):
    yy5, ss5 = binormal(n_rows, 0.10, d)
    boots = []
    for _ in range(1_000):
        i = rng.integers(0, n_rows, n_rows)
        if yy5[i].min() != yy5[i].max():
            boots.append(roc_auc_score(yy5[i], ss5[i]))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    print(f"[5] n = {n_rows:>6} ({yy5.sum()} positives): AUROC {roc_auc_score(yy5, ss5):.3f}"
          f"  95% CI {lo:.3f}–{hi:.3f}  (width {hi - lo:.3f})")

# --- 6. Decision curve: net benefit vs treat-all / treat-none ------------------
yy6, ss6 = binormal(100_000, 0.10, d)
prob6 = LogisticRegression().fit(ss6.reshape(-1, 1), yy6).predict_proba(ss6.reshape(-1, 1))[:, 1]
ths = np.linspace(0.02, 0.40, 39)
N = len(yy6)
nb_model = [((prob6 >= t) & (yy6 == 1)).sum() / N - ((prob6 >= t) & (yy6 == 0)).sum() / N * t / (1 - t) for t in ths]
nb_all = [yy6.mean() - (1 - yy6.mean()) * t / (1 - t) for t in ths]
for t in (0.05, 0.10, 0.20):
    i = int(np.argmin(abs(ths - t)))
    print(f"[6] threshold {t:.2f}: net benefit model {nb_model[i]:.4f}  treat-all {nb_all[i]:.4f}")
fig, ax = plt.subplots(figsize=(4.6, 3.8))
ax.plot(ths, nb_model, color=BLUE, label="Model")
ax.plot(ths, nb_all, color=ORANGE, label="Call everyone")
ax.axhline(0, color=MUTED, lw=1, ls="--", label="Call no one")
ax.set(xlabel="Threshold probability", ylabel="Net benefit",
       title="Decision curve", xlim=(0.02, 0.40), ylim=(-0.03, 0.10))
ax.legend(loc="upper right")
fig.savefig(f"{OUT}/decision-curve.png")
plt.close(fig)
print("figures written to", OUT)
