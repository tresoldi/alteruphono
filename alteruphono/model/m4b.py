"""M4b: the shape-only gate (Q1) and rate modelling (Q2), as docs/v2/PLAN_M4b.md.

    python -m alteruphono.model.m4b <lexibank.tsv> <wiktionary.tsv> <diachronica.json> <out.json>
"""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict

import numpy as np
from scipy import optimize

from alteruphono.model import calibrate as cal
from alteruphono.model.fit import SIGMAS, Design, fit, layout, load

FIT3 = ("Uto-Aztecan", "Uralic", "Japonic")
FRESH = "Turkic"
POST_HOC = ("Austroasiatic", "Bora-Muinane")
SRC_PREFIXES = ("g_sub:", "g_del:", "v_sub:", "v_del:")
GRID_SRC = (0.03, 0.1, 0.3, 1.0, 3.0)
GRID_REST = (0.01, 0.03, 0.1)


def sigma_vector(names, s_src, s_rest):
    return np.array([s_src if n.startswith(SRC_PREFIXES) else s_rest for n in names])


def lofo(dall, fam_of, names, penalized, sigma):
    total = 0.0
    for fam in FIT3:
        tr = dall.subset(np.nonzero(fam_of != fam)[0])
        te = dall.subset(np.nonzero(fam_of == fam)[0])
        theta, _ = fit(tr, len(names), penalized, sigma)
        total += -te.logprobs(theta)[te.chosen].sum()
    return total / len(fam_of)


def grouped_logprobs(eta, design):
    m = np.maximum.reduceat(eta, design.offsets[:-1])
    e = np.exp(eta - m[design.group])
    return eta - (np.log(design.G @ e) + m)[design.group]


def split_halves(rows):
    """Per branch, cognate sets shuffled with seed 20261118: first half A."""
    by_branch = defaultdict(set)
    for r in rows:
        by_branch[r["branch"]].add(r["cogset"])
    half = {}
    for b, sets in by_branch.items():
        s = sorted(sets)
        random.Random(20261118).shuffle(s)
        k = len(s) // 2  # an odd count gives E the extra set
        for c in s[:k]:
            half[(b, c)] = "A"
        for c in s[k:]:
            half[(b, c)] = "E"
    return [half[(r["branch"], r["cogset"])] for r in rows]


def shape_ll(rows, preds):
    out, sets = [], []
    for r in rows:
        y, s = r["reflex"], r["source"]
        if y == s:
            continue
        p = preds[id(r)]
        out.append(-math.log(max(p[y] / max(1 - p[s], 1e-300), 1e-300)))
        sets.append((r["family"], r["cogset"]))
    return np.array(out), sets


def paired_boot(a, b, sets, seed):
    d = a - b
    uniq = sorted(set(sets))
    idx = defaultdict(list)
    for i, k in enumerate(sets):
        idx[k].append(i)
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(1000):
        pick = rng.integers(0, len(uniq), len(uniq))
        ii = [i for j in pick for i in idx[uniq[j]]]
        boots.append(d[ii].mean())
    return {"mean": float(d.mean()), "95ci": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]}


def evaluate_family(fam, rows, inv, rules, names, idx, models, base):
    sub = [r for r in rows if r["family"] == fam]
    halves = split_halves(sub)
    leave = set(cal.EXCLUDED_SECTIONS)
    if cal.FAMILY_SECTION.get(fam):
        leave.add(cal.FAMILY_SECTION[fam])
    cat = cal.Catalogue(rules, leave)
    d = Design(sub, inv, {fam: cat}, {}, names, idx)
    cands = [sorted(inv[r["branch"]] | {r["source"], "-"}) for r in sub]
    nonstay = np.concatenate([[y != r["source"] for y in C] for r, C in zip(sub, cands)]).astype(float)
    opp_branch = [r["branch"] for r in sub]
    branch_rows = defaultdict(list)
    for o, r in enumerate(sub):
        branch_rows[r["branch"]].append(o)

    def preds_from(eta):
        lp = grouped_logprobs(eta, d)
        return {id(r): dict(zip(cands[o], np.exp(lp[d.offsets[o]:d.offsets[o + 1]]))) for o, r in enumerate(sub)}

    def adapt(theta):
        """alpha_b MAP on each branch's A half (prior N(0,1)), other parameters fixed."""
        eta0 = d.X @ theta
        alpha = {}
        for b, opps in branch_rows.items():
            a_opps = [o for o in opps if halves[o] == "A"]
            if not a_opps:
                alpha[b] = 0.0
                continue

            def nll(a):
                lp = grouped_logprobs(eta0 + a * nonstay, d)
                return -sum(lp[d.chosen[o]] for o in a_opps) + 0.5 * a * a

            alpha[b] = float(optimize.minimize_scalar(nll, bounds=(-6, 6), method="bounded").x)
        shift = np.concatenate([[alpha[opp_branch[o]]] * len(cands[o]) for o in range(len(sub))])
        return eta0 + shift * nonstay, alpha

    out = {"opportunities_E": sum(h == "E" for h in halves), "models": {}}
    preds = {}
    for name, theta in models.items():
        preds[name] = preds_from(d.X @ theta)
        eta_ad, alpha = adapt(theta)
        preds[name + "-adapted"] = preds_from(eta_ad)
        out.setdefault("alpha", {})[name] = alpha
    # distance and uniform baselines, plain and adapted
    pi_b = {}
    for b, opps in branch_rows.items():
        a_opps = [sub[o] for o in opps if halves[o] == "A"]
        pi_b[b] = (sum(r["reflex"] == r["source"] for r in a_opps) + 1) / (len(a_opps) + 2)
    preds["distance"] = {id(r): cal.p_distance(r, C, base["pi_d"], base["T_d"]) for r, C in zip(sub, cands)}
    preds["distance-adapted"] = {id(r): cal.p_distance(r, C, pi_b[r["branch"]], base["T_d"]) for r, C in zip(sub, cands)}
    preds["uniform"] = {id(r): cal.p_uniform(r, C, base["pi"]) for r, C in zip(sub, cands)}
    E = [r for r, h in zip(sub, halves) if h == "E"]
    scored = {}
    for name, p in preds.items():
        s = cal.score(E, inv, lambda r, C, p=p: p[id(r)])
        sh, sets = shape_ll(E, p)
        s["shape_E"] = float(sh.mean())
        scored[name] = (s, sh, sets)
        s2 = dict(s)
        s2.pop("_ll", None)
        s2.pop("_sets", None)
        out["models"][name] = s2
    q1 = {m: paired_boot(scored[m][1], scored["distance"][1], scored[m][2], 20261119) for m in ("F1", "F2")}
    q2_ll = cal.paired(scored["F2-adapted"][0], scored["distance-adapted"][0], seed=20261120)
    out["Q1_shape_minus_distance"] = q1
    out["Q2_F2adapted_minus_distanceadapted"] = q2_ll
    out["Q1_pass"] = bool(q1["F1"]["95ci"][1] < 0)
    out["Q2_pass"] = bool(out["models"]["F2-adapted"]["ece_change"] < 0.05 and q2_ll["95ci"][1] < 0)
    return out


def main(lexibank, wiktionary, diachronica, out_path):
    rows = load(lexibank) + load(wiktionary)
    inv = defaultdict(set)
    for r in rows:
        if r["reflex"] != "-":
            inv[r["branch"]].add(r["reflex"])
    rules = json.load(open(diachronica, encoding="utf-8"))["rules"]
    catalogues = {}
    for fam in FIT3:
        leave = set(cal.EXCLUDED_SECTIONS) | {cal.FAMILY_SECTION[fam]}
        catalogues[fam] = cal.Catalogue(rules, leave)
    fit_rows = [r for r in rows if r["family"] in FIT3]
    branches = sorted({r["branch"] for r in fit_rows})
    bidx = {b: i for i, b in enumerate(branches)}
    names, idx, penalized = layout(len(branches))
    dall = Design(fit_rows, inv, catalogues, bidx, names, idx)
    fam_of = np.array([r["family"] for r in fit_rows])
    report = {"fit_families": list(FIT3), "fresh": FRESH, "n_fit": len(fit_rows), "cv_F1": {}, "cv_F2": {}}
    for s in SIGMAS:
        report["cv_F1"][str(s)] = lofo(dall, fam_of, names, penalized, s)
        print("F1", s, report["cv_F1"][str(s)], file=sys.stderr)
    s1 = float(min(report["cv_F1"], key=report["cv_F1"].get))
    for a in GRID_SRC:
        for b in GRID_REST:
            report["cv_F2"][f"{a},{b}"] = lofo(dall, fam_of, names, penalized, sigma_vector(names, a, b))
            print("F2", a, b, report["cv_F2"][f"{a},{b}"], file=sys.stderr)
    best2 = min(report["cv_F2"], key=report["cv_F2"].get)
    a2, b2 = map(float, best2.split(","))
    theta1, _ = fit(dall, len(names), penalized, s1)
    theta2, _ = fit(dall, len(names), penalized, sigma_vector(names, a2, b2))
    report["F1_sigma"] = s1
    report["F2_sigma"] = [a2, b2]
    report["lam"] = {"F1": float(theta1[idx["lam"]]), "F2": float(theta2[idx["lam"]])}
    pi = cal.fit_uniform(fit_rows, inv)
    pi_d, T_d = cal.fit_distance(fit_rows, inv)
    base = {"pi": pi, "pi_d": pi_d, "T_d": T_d}
    report["baselines"] = base
    report["families"] = {}
    for fam in (FRESH,) + POST_HOC:
        res = evaluate_family(fam, rows, inv, rules, names, idx, {"F1": theta1, "F2": theta2}, base)
        res["status"] = "primary (fresh)" if fam == FRESH else "post hoc (seen in M4)"
        res.pop("alpha", None)
        report["families"][fam] = res
        print(fam, res["status"], "Q1", res["Q1_pass"], res["Q1_shape_minus_distance"], "Q2", res["Q2_pass"],
              "ECE F2-adapted", round(res["models"]["F2-adapted"]["ece_change"], 3), res["Q2_F2adapted_minus_distanceadapted"],
              file=sys.stderr)
    json.dump(report, open(out_path, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:5])
