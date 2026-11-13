"""M4 calibration gate (DESIGN 10), on the held-out families of TRAINING_SPLIT.md.

    python -m alteruphono.model.gate <lexibank.tsv> <wiktionary.tsv> <diachronica.json> <model.json> <out.json>

Gate, fixed in DESIGN 10 before any fit:
  1. the fitted model's log-loss is lower than every baseline's, and the
     paired 95% interval against the best baseline excludes 0 (it is below
     0), on each held-out family;
  2. the ECE of P(change) is below 0.05 on each held-out family;
  3. reported, not a pass/fail condition: the l/r asymmetry
     eta(l->r) - eta(r->l), between vowels, has an interval covering 0.
The baselines' scalars are refitted on all four fitting families. Intervals
bootstrap cognate sets (two held-out families: a family bootstrap would mean
nothing). The fitted model predicts a held-out branch with its offset at 0.
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict

import numpy as np

from alteruphono.model import calibrate as cal
from alteruphono.model.fit import FIT_FAMILIES, HELD_OUT, Design, layout, load


def main(lexibank, wiktionary, diachronica, model_path, out):
    rows = load(lexibank) + load(wiktionary)
    inv = defaultdict(set)
    for r in rows:
        if r["reflex"] != "-":
            inv[r["branch"]].add(r["reflex"])
    pack = json.load(open(model_path, encoding="utf-8"))
    theta = np.array(pack["theta"])
    cov = np.load(model_path.replace(".json", "_cov.npy"))
    names, idx, _ = layout(len(pack["branches"]))
    assert names == pack["parameters"]
    rules = json.load(open(diachronica, encoding="utf-8"))["rules"]
    fit_rows = [r for r in rows if r["family"] in FIT_FAMILIES]
    pi = cal.fit_uniform(fit_rows, inv)
    pi_d, T_d = cal.fit_distance(fit_rows, inv)
    historia = cal.make_historia()
    report = {"model": {k: pack[k] for k in ("sigma", "cv_log_loss", "n_opportunities", "converged")},
              "lam": [theta[idx["lam"]], math.sqrt(max(cov[idx["lam"], idx["lam"]], 0))],
              "beta": [theta[idx["beta"]], math.sqrt(max(cov[idx["beta"], idx["beta"]], 0))],
              "baselines_fitted_on": list(FIT_FAMILIES),
              "baseline_scalars": {"uniform_pi": pi, "distance_pi": pi_d, "distance_T": T_d},
              "families": {}, "gate": {}}
    gate_ok = True
    for fam in HELD_OUT:
        sub = [r for r in rows if r["family"] == fam]
        leave = set(cal.EXCLUDED_SECTIONS)
        if cal.FAMILY_SECTION.get(fam):
            leave.add(cal.FAMILY_SECTION[fam])
        cat = cal.Catalogue(rules, leave)
        d = Design(sub, inv, {fam: cat}, {}, names, idx)
        lp = d.logprobs(theta)
        preds = {}
        for o, r in enumerate(sub):
            C = sorted(inv[r["branch"]] | {r["source"], "-"})
            vals = np.exp(lp[d.offsets[o]:d.offsets[o + 1]])
            preds[id(r)] = dict(zip(C, vals))
        res = {
            "fitted": cal.score(sub, inv, lambda r, C: preds[id(r)]),
            "uniform": cal.score(sub, inv, lambda r, C: cal.p_uniform(r, C, pi)),
            "distance": cal.score(sub, inv, lambda r, C: cal.p_distance(r, C, pi_d, T_d)),
            "catalogue": cal.score(sub, inv, lambda r, C, cat=cat: cal.p_catalogue(r, C, cat)),
            "historia": cal.score(sub, inv, historia),
        }
        base = {k: v for k, v in res.items() if k != "fitted"}
        best = min(base, key=lambda k: base[k]["log_loss"])
        res["paired_fitted_minus"] = {k: cal.paired(res["fitted"], res[k]) for k in base}
        c1 = all(res["fitted"]["log_loss"] < v["log_loss"] for v in base.values()) \
            and res["paired_fitted_minus"][best]["95ci"][1] < 0
        c2 = res["fitted"]["ece_change"] < 0.05
        report["gate"][fam] = {"best_baseline": best, "log_loss_condition": bool(c1), "ece_condition": bool(c2)}
        gate_ok = gate_ok and c1 and c2
        for v in res.values():
            if isinstance(v, dict):
                v.pop("_ll", None)
                v.pop("_sets", None)
        report["families"][fam] = res
        print(fam, {k: round(v["log_loss"], 3) for k, v in res.items() if "log_loss" in v},
              "ECE fitted", round(res["fitted"]["ece_change"], 3), report["gate"][fam], file=sys.stderr)
    # l/r asymmetry between vowels, generic catalogue (only the excluded sections out)
    generic = cal.Catalogue(rules, set(cal.EXCLUDED_SECTIONS))
    syn = [{"source": "l", "left": "a", "right": "a", "branch": "__syn", "family": "g", "reflex": "r"},
           {"source": "r", "left": "a", "right": "a", "branch": "__syn", "family": "g", "reflex": "l"}]
    sinv = defaultdict(set, {"__syn": {"l", "r"}})
    ds = Design(syn, sinv, {"g": generic}, {}, names, idx)
    x_lr = ds.X[ds.chosen[0]].toarray().ravel()
    x_rl = ds.X[ds.chosen[1]].toarray().ravel()
    g = x_lr - x_rl
    a = float(g @ theta)
    se = math.sqrt(max(float(g @ cov @ g), 0))
    report["asymmetry_l_r_between_vowels"] = {"eta_l_to_r_minus_r_to_l": a, "se": se,
                                              "95ci": [a - 1.96 * se, a + 1.96 * se],
                                              "covers_0": bool(a - 1.96 * se <= 0 <= a + 1.96 * se)}
    report["gate"]["passed"] = bool(gate_ok)
    json.dump(report, open(out, "w", encoding="utf-8"), indent=1)
    print("gate passed:", gate_ok, "| l/r asymmetry", report["asymmetry_l_r_between_vowels"], file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:6])
