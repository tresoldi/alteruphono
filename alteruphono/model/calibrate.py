"""M3: the catalogue-only change model and its calibration (DESIGN 6, 10).

    python -m alteruphono.model.calibrate <opportunities.tsv> <diachronica_rules.json> <out.json>

Every opportunity is one proto-segment s, with proto-neighbours (L, R), on a
branch proto>daughter, observed with its reflex y (a segment, or "-" for
deletion). A model gives P(y | s, L, R) over a candidate set C: the
daughter's segment inventory in that dataset, plus s and "-". The candidate
set is part of the question (DESIGN 6.2), and is the same for every model.

Models (all fixed before looking at the held-out families):
  uniform      P(stay) = pi, the rest uniform over C; pi fitted on the fitting
               families
  distance     P(stay) = pi; y != s weighted exp(-d(s, y) / T), with merkmal's
               descriptive dissimilarity, and deletion at d = GAP; pi and T
               fitted on the fitting families (grid search, maximum likelihood)
  catalogue    the M3 model: P(stay) = 0.8, stipulated (DESIGN 6.4); given a
               change, y is weighted by the summed weight of the catalogue
               rules that, applied by the 2.0 engine to "# L s R #", turn s
               into y, plus KAPPA times the distance kernel above at
               T = T_CAT; leave-out per TRAINING_SPLIT.md 4, plus the
               evaluated family's own section
  historia     blindrec's incumbent p(y | x) (blindrec/historia/direction.py:
               identity 0.6, Index Diachronica counts smoothed toward a
               feature kernel), restricted to C and renormalised; it uses
               every Index Diachronica rule, so it has seen Austroasiatic

The stipulated constants (P_STAY_CAT, KAPPA, T_CAT) are named and are not
estimates. M4 replaces them with fitted parameters.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import Counter, defaultdict
from functools import cache

import numpy as np

from alteruphono import forward, parse_rule, parse_sequence
from alteruphono.model.extract import GAP, dist
from alteruphono.resources import load_sound_changes

P_STAY_CAT = 0.8
KAPPA = 1.0
T_CAT = 0.15
EXCLUDED_SECTIONS = {
    "Indo-European", "Austronesian", "Niger-Congo", "Sino-Tibetan", "Trans-New Guinea",
    "Macro-Arawakan", "Totozoquean", "Vowel Shifts", "Most-Wanted Sound Changes",
}
FAMILY_SECTION = {"Austroasiatic": "Austroasiatic", "Uto-Aztecan": "Uto-Aztecan", "Uralic": "Uralic",
                  "Turkic": "Altaic", "Japonic": "Altaic", "Bora-Muinane": None}
FIT = ("Uto-Aztecan",)  # the M3 fitting families available (Wiktionary families come in M4)
HELD_OUT = ("Austroasiatic", "Bora-Muinane")


def load(path):
    rows = [r for r in csv.DictReader(open(path, encoding="utf-8"), delimiter="\t") if r["stream"] == "substitution"]
    inv = defaultdict(set)
    for r in rows:
        if r["reflex"] != "-":
            inv[r["branch"]].add(r["reflex"])
    return rows, inv


def candidates(r, inv):
    return sorted(inv[r["branch"]] | {r["source"], "-"})


def kernel(s, y, T):
    return math.exp(-(GAP if y == "-" else dist(s, y)) / T)


# ---- the catalogue ------------------------------------------------------------


class Catalogue:
    def __init__(self, diachronica_rules, leave_out_sections, keep_sections=None):
        """keep_sections, if given, restricts Index Diachronica to those
        sections (the half-A catalogue of blindrec's v16 plan)."""
        self.rules = []
        for row in load_sound_changes():
            self.rules.append((row["RULE"], float(row["WEIGHT"] or 1)))
        for r in diachronica_rules:
            if r["section"] in leave_out_sections:
                continue
            if keep_sections is not None and r["section"] not in keep_sections:
                continue
            self.rules.append((r["rule"], 1.0))
        self.parsed = []
        for text, w in self.rules:
            try:
                self.parsed.append((parse_rule(text), w))
            except (ValueError, OverflowError):
                pass

    @cache  # noqa: B019 - one Catalogue per leave-out set, kept for the run
    def reflexes(self, left, s, right):
        """Summed rule weight per reflex of s in "# L s R #" (L, R may be #)."""
        tokens = ["#"] + ([left] if left != "#" else []) + [s] + ([right] if right != "#" else []) + ["#"]
        seq = parse_sequence(" ".join(tokens))
        mid = 1 if left == "#" else 2
        n = len(seq)
        out = Counter()
        for rule, w in self.parsed:
            try:
                res = forward(seq, rule)
            except (ValueError, IndexError, OverflowError):
                continue
            if len(res) == n:
                y = str(res[mid])
                if y != s:
                    out[y] += w
            elif len(res) == n - 1 and [str(e) for e in res[:mid]] == [str(e) for e in seq[:mid]] \
                    and [str(e) for e in res[mid:]] == [str(e) for e in seq[mid + 1:]]:
                out["-"] += w
        return out


# ---- the models ---------------------------------------------------------------


def p_uniform(r, C, pi):
    k = len(C) - 1
    return {y: (pi if y == r["source"] else (1 - pi) / k) for y in C}


def p_distance(r, C, pi, T):
    s = r["source"]
    w = {y: kernel(s, y, T) for y in C if y != s}
    z = sum(w.values())
    out = {y: (1 - pi) * v / z for y, v in w.items()}
    out[s] = pi
    return out


def p_catalogue(r, C, cat):
    s = r["source"]
    counts = cat.reflexes(r["left"], s, r["right"])
    w = {y: counts.get(y, 0.0) + KAPPA * kernel(s, y, T_CAT) for y in C if y != s}
    z = sum(w.values())
    out = {y: (1 - P_STAY_CAT) * v / z for y, v in w.items()}
    out[s] = P_STAY_CAT
    return out


def make_historia():
    """blindrec's historia/direction.py p(y | x), imported from its checkout."""
    import os

    br = os.environ.get("BLINDREC_DIR", "/home/user/prototypes/blind-reconstruction")
    sys.path.insert(0, br)
    from blindrec.historia import direction  # noqa: PLC0415

    def p(r, C):
        s = r["source"]
        targets = tuple(C)
        w = {y: math.exp(direction.logp(y, s, targets)) for y in C}
        z = sum(w.values()) or 1.0
        return {y: v / z for y, v in w.items()}

    return p


# ---- fitting the baselines' scalars on the fitting families -------------------


def fit_uniform(rows, inv):
    stay = sum(r["reflex"] == r["source"] for r in rows)
    return stay / len(rows)


def fit_distance(rows, inv):
    pi = fit_uniform(rows, inv)
    best = None
    for T in (0.02, 0.05, 0.08, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0):
        ll = 0.0
        for r in rows:
            C = candidates(r, inv)
            ll += math.log(max(p_distance(r, C, pi, T)[r["reflex"]], 1e-300))
        if best is None or ll > best[0]:
            best = (ll, T)
    return pi, best[1]


# ---- scoring ------------------------------------------------------------------


def score(rows, inv, predict, n_bins=10, n_boot=1000, seed=20261115):
    """Log-loss, reliability of P(change) and of P(observed), ECE, with a
    bootstrap over cognate sets (the held-out families are two: a family
    bootstrap would mean nothing)."""
    ll, pch, ch, pobs = [], [], [], []
    ll_rate, ll_shape = [], []
    cand_p, cand_hit = [], []
    sets = []
    for r in rows:
        C = candidates(r, inv)
        p = predict(r, C)
        y = r["reflex"]
        ll.append(-math.log(max(p[y], 1e-300)))
        stay = p[r["source"]]
        # the log-loss splits exactly into "did it change" and "where to, given a change"
        ll_rate.append(-math.log(max(stay if y == r["source"] else 1 - stay, 1e-300)))
        if y != r["source"]:
            ll_shape.append(-math.log(max(p[y] / max(1 - stay, 1e-300), 1e-300)))
        pch.append(1.0 - p[r["source"]])
        ch.append(float(y != r["source"]))
        pobs.append(p[y])
        sets.append((r["family"], r["cogset"]))
        for cand, pc in p.items():
            cand_p.append(pc)
            cand_hit.append(float(cand == y))
    ll, pch, ch = np.array(ll), np.array(pch), np.array(ch)
    bins = np.minimum((pch * n_bins).astype(int), n_bins - 1)
    curve = []
    ece = 0.0
    for b in range(n_bins):
        m = bins == b
        if m.any():
            curve.append({"bin": b, "n": int(m.sum()), "mean_predicted": float(pch[m].mean()),
                          "observed": float(ch[m].mean())})
            ece += m.sum() / len(pch) * abs(pch[m].mean() - ch[m].mean())
    # multiclass calibration: every candidate's probability against whether it
    # was the observed reflex, in bins (log-spaced: most candidates are small)
    cp, chit = np.array(cand_p), np.array(cand_hit)
    edges = [0, 0.001, 0.003, 0.01, 0.03, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0000001]
    cand_curve = []
    ece_c = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (cp >= lo) & (cp < hi)
        if m.any():
            cand_curve.append({"from": lo, "to": min(hi, 1.0), "n": int(m.sum()),
                               "mean_predicted": float(cp[m].mean()), "observed": float(chit[m].mean())})
            ece_c += m.sum() / len(cp) * abs(cp[m].mean() - chit[m].mean())
    uniq = sorted(set(sets))
    idx = defaultdict(list)
    for i, k in enumerate(sets):
        idx[k].append(i)
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(uniq), len(uniq))
        ii = [i for j in pick for i in idx[uniq[j]]]
        boots.append(ll[ii].mean())
    return {
        "opportunities": len(rows), "log_loss": float(ll.mean()),
        "log_loss_rate": float(np.mean(ll_rate)), "log_loss_shape_given_change": float(np.mean(ll_shape)),
        "changed": len(ll_shape),
        "log_loss_95ci": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
        "observed_change_rate": float(ch.mean()), "mean_predicted_change": float(pch.mean()),
        "ece_change": float(ece), "reliability_change": curve,
        "ece_candidates": float(ece_c), "reliability_candidates": cand_curve,
        "mean_p_observed": float(np.mean(pobs)),
        "_ll": ll.tolist(), "_sets": [list(s) for s in sets],
    }


def paired(a, b, seed=20261116, n_boot=1000):
    """Paired bootstrap over cognate sets of the per-opportunity log-loss difference a - b."""
    la, lb = np.array(a["_ll"]), np.array(b["_ll"])
    sets = [tuple(s) for s in a["_sets"]]
    uniq = sorted(set(sets))
    idx = defaultdict(list)
    for i, k in enumerate(sets):
        idx[k].append(i)
    rng = np.random.default_rng(seed)
    d = la - lb
    boots = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(uniq), len(uniq))
        ii = [i for j in pick for i in idx[uniq[j]]]
        boots.append(d[ii].mean())
    return {"mean": float(d.mean()), "95ci": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]}


def main(opps, diachronica, out):
    rows, inv = load(opps)
    fit = [r for r in rows if r["family"] in FIT]
    pi = fit_uniform(fit, inv)
    pi_d, T_d = fit_distance(fit, inv)
    rules = json.load(open(diachronica, encoding="utf-8"))["rules"]
    historia = make_historia()
    report = {"fitted": {"uniform_pi": pi, "distance_pi": pi_d, "distance_T": T_d,
                         "fit_opportunities": len(fit)},
              "stipulated": {"P_STAY_CAT": P_STAY_CAT, "KAPPA": KAPPA, "T_CAT": T_CAT},
              "families": {}}
    for fam in HELD_OUT:
        sub = [r for r in rows if r["family"] == fam]
        leave = set(EXCLUDED_SECTIONS)
        if FAMILY_SECTION.get(fam):
            leave.add(FAMILY_SECTION[fam])
        cat = Catalogue(rules, leave)
        res = {
            "uniform": score(sub, inv, lambda r, C: p_uniform(r, C, pi)),
            "distance": score(sub, inv, lambda r, C: p_distance(r, C, pi_d, T_d)),
            "catalogue": score(sub, inv, lambda r, C, cat=cat: p_catalogue(r, C, cat)),
            "historia": score(sub, inv, historia),
        }
        res["paired_catalogue_minus"] = {k: paired(res["catalogue"], res[k]) for k in ("uniform", "distance", "historia")}
        res["catalogue_rules_used"] = len(cat.parsed)
        report["families"][fam] = res
        print(fam, {k: round(v["log_loss"], 4) for k, v in res.items() if isinstance(v, dict) and "log_loss" in v},
              file=sys.stderr)
    for fam in report["families"].values():
        for k, v in fam.items():
            if isinstance(v, dict):
                v.pop("_ll", None)
                v.pop("_sets", None)
    json.dump(report, open(out, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:4])
