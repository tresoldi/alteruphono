"""M4: the fitted change model (DESIGN 6, as revised after M3).

After M3, Tiago approved one design change: phonetic distance is the base
shape of change, and the catalogue is a correction with a learned weight.
For an opportunity (source s, proto-neighbours L, R, branch b), over the
candidates C (as in calibrate.py):

  eta(s)    = 0                                              (stay)
  eta(y)    = a_sub + alpha_b + g_sub.x(s) + v_sub.psi(L,R)
              - beta * d(s, y)                               (distance base)
              + w.phi(s->y)                                  (directed displacement)
              + z.chi(s, y, L, R)                            (assimilation)
              + lam * log(1 + n_cat(s->y | L, R))            (catalogue)
  eta(del)  = a_del + alpha_b + g_del.x(s) + v_del.psi(L,R)
              + lam * log(1 + n_cat(s->del | L, R))
  P(y) = softmax over C.

Terms:
  x(s)      merkmal `descriptive` feature vector of s (62 dimensions)
  phi       per dimension, did y move up or down from s (directional:
            d up and d down are different parameters)
  chi       per dimension, y took the left (right) neighbour's value where s
            differed from it
  psi       left is #, left is a vowel, right is #, right is a vowel
  alpha_b   per-branch offset (time depth, granularity); at prediction for a
            new branch, 0 (the population mean)
  n_cat     catalogue weight of rules turning s into y in "# L s R #"
            (2.0 engine), with the opportunity's own family section left out
            (P_typo^(-family)), as for the held-out families

Penalized maximum likelihood: Gaussian penalty 1/(2 sigma^2) on g, v, w,
z and alpha; a, beta, lam unpenalized. sigma is chosen by leave-one-family-
out log-loss over the four fitting families (grid SIGMAS). Uncertainty: the
Laplace approximation (inverse Hessian of the penalized objective) at the
mode. The insertion stream is not modelled here.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from functools import cache

import merkmal
import numpy as np
from scipy import optimize, sparse

from alteruphono.model.calibrate import EXCLUDED_SECTIONS, FAMILY_SECTION, Catalogue
from alteruphono.model.extract import GAP, dist

SYSTEM = "descriptive"
SIGMAS = (0.01, 0.03, 0.1, 0.3, 1.0, 3.0)  # 0.01, 0.03 added: 0.1, the first grid's edge, won
FIT_FAMILIES = ("Uto-Aztecan", "Uralic", "Japonic", "Turkic")
HELD_OUT = ("Austroasiatic", "Bora-Muinane")


@cache
def vec(g: str) -> np.ndarray:
    if g in ("#", "-"):
        return np.zeros(WIDTH)
    try:
        return np.array(merkmal.feature_vector(g, SYSTEM), dtype=float)
    except Exception:  # noqa: BLE001 - unknown to merkmal: no features
        return np.zeros(WIDTH)


WIDTH = len(merkmal.vector_labels(SYSTEM))
LABELS = list(merkmal.vector_labels(SYSTEM))
VOWEL_DIM = LABELS.index("vocoid")


def is_vowel(g: str) -> bool:
    return g not in ("#", "-") and vec(g)[VOWEL_DIM] > 0


# ---- feature layout -----------------------------------------------------------

def layout(n_branches: int):
    names = ["a_sub", "a_del", "beta", "lam"]
    names += [f"g_sub:{l}" for l in LABELS] + [f"g_del:{l}" for l in LABELS]
    env = ["L=#", "L=V", "R=#", "R=V"]
    names += [f"v_sub:{e}" for e in env] + [f"v_del:{e}" for e in env]
    names += [f"w:{l}:up" for l in LABELS] + [f"w:{l}:down" for l in LABELS]
    names += [f"z:{l}:left" for l in LABELS] + [f"z:{l}:right" for l in LABELS]
    names += [f"alpha:{i}" for i in range(n_branches)]
    idx = {n: i for i, n in enumerate(names)}
    penalized = np.array([not (n in ("a_sub", "a_del", "beta", "lam")) for n in names])
    return names, idx, penalized


class Design:
    """Sparse candidate-row design for a set of opportunities."""

    def __init__(self, rows, inv, catalogues, branch_index, names, idx):
        data, ri, ci = [], [], []
        group, chosen, n_rows = [], [], 0
        offsets = [0]
        for o, r in enumerate(rows):
            s, L, R = r["source"], r["left"], r["right"]
            C = sorted(inv[r["branch"]] | {s, "-"})
            cat = catalogues[r["family"]].reflexes(L, s, R)
            xs, xl, xr = vec(s), vec(L), vec(R)
            env = [L == "#", is_vowel(L), R == "#", is_vowel(R)]
            b = branch_index.get(r["branch"])
            for y in C:
                feats = {}
                if y == s:
                    pass
                elif y == "-":
                    feats[idx["a_del"]] = 1.0
                    for d in np.nonzero(xs)[0]:
                        feats[idx[f"g_del:{LABELS[d]}"]] = xs[d]
                    for k, e in enumerate(env):
                        if e:
                            feats[idx[f"v_del:{['L=#', 'L=V', 'R=#', 'R=V'][k]}"]] = 1.0
                    feats[idx["lam"]] = math.log1p(cat.get("-", 0.0))
                    if b is not None:
                        feats[idx[f"alpha:{b}"]] = 1.0
                else:
                    xy = vec(y)
                    feats[idx["a_sub"]] = 1.0
                    for d in np.nonzero(xs)[0]:
                        feats[idx[f"g_sub:{LABELS[d]}"]] = xs[d]
                    for k, e in enumerate(env):
                        if e:
                            feats[idx[f"v_sub:{['L=#', 'L=V', 'R=#', 'R=V'][k]}"]] = 1.0
                    feats[idx["beta"]] = -dist(s, y)
                    diff = xy - xs
                    for d in np.nonzero(np.abs(diff) > 1e-9)[0]:
                        feats[idx[f"w:{LABELS[d]}:{'up' if diff[d] > 0 else 'down'}"]] = 1.0
                        if L != "#" and abs(xy[d] - xl[d]) < 1e-9:
                            feats[idx[f"z:{LABELS[d]}:left"]] = 1.0
                        if R != "#" and abs(xy[d] - xr[d]) < 1e-9:
                            feats[idx[f"z:{LABELS[d]}:right"]] = 1.0
                    feats[idx["lam"]] = math.log1p(cat.get(y, 0.0))
                    if b is not None:
                        feats[idx[f"alpha:{b}"]] = 1.0
                for c, v in feats.items():
                    if v != 0.0:
                        ri.append(n_rows)
                        ci.append(c)
                        data.append(v)
                group.append(o)
                if y == r["reflex"]:
                    chosen.append(n_rows)
                n_rows += 1
            offsets.append(n_rows)
        self.X = sparse.csr_matrix((data, (ri, ci)), shape=(n_rows, len(names)))
        self.group = np.array(group)
        self.chosen = np.array(chosen)
        self.offsets = np.array(offsets)
        self.n_opp = len(rows)
        # opportunity-by-row membership, to sum over candidates
        self.G = sparse.csr_matrix((np.ones(n_rows), (self.group, np.arange(n_rows))), shape=(self.n_opp, n_rows))

    def subset(self, opp_ids):
        """The design restricted to some opportunities (rows kept in order)."""
        new = object.__new__(Design)
        opp_ids = np.asarray(sorted(opp_ids))
        rows = np.concatenate([np.arange(self.offsets[o], self.offsets[o + 1]) for o in opp_ids])
        remap = np.full(self.X.shape[0], -1)
        remap[rows] = np.arange(len(rows))
        new.X = self.X[rows]
        sizes = self.offsets[opp_ids + 1] - self.offsets[opp_ids]
        new.offsets = np.concatenate([[0], np.cumsum(sizes)])
        new.group = np.repeat(np.arange(len(opp_ids)), sizes)
        new.chosen = remap[self.chosen[opp_ids]]
        new.n_opp = len(opp_ids)
        new.G = sparse.csr_matrix((np.ones(len(rows)), (new.group, np.arange(len(rows)))), shape=(new.n_opp, len(rows)))
        return new

    def logprobs(self, theta):
        eta = self.X @ theta
        m = np.maximum.reduceat(eta, self.offsets[:-1])
        e = np.exp(eta - m[self.group])
        z = self.G @ e
        logz = np.log(z) + m
        return eta - logz[self.group]


def objective(theta, design, penalized, sigma):
    lp = design.logprobs(theta)
    p = np.exp(lp)
    nll = -lp[design.chosen].sum()
    # gradient: sum over opportunities of (E_p[x] - x_chosen)
    grad = design.X.T @ p - np.asarray(design.X[design.chosen].sum(axis=0)).ravel()
    pen = penalized / (sigma ** 2)
    return nll + 0.5 * float((pen * theta ** 2).sum()), grad + pen * theta


def fit(design, n_params, penalized, sigma, theta0=None):
    theta0 = np.zeros(n_params) if theta0 is None else theta0
    res = optimize.minimize(objective, theta0, args=(design, penalized, sigma), jac=True,
                            method="L-BFGS-B", options={"maxiter": 2000})
    return res.x, res


def hessian(theta, design, penalized, sigma):
    """Exact Hessian of the penalized NLL (multinomial logit)."""
    p = np.exp(design.logprobs(theta))
    X = design.X
    first = (X.T @ sparse.diags(p) @ X).toarray()
    M = design.G @ sparse.diags(p) @ X  # per-opportunity E_p[x]
    second = (M.T @ M).toarray()
    return first - second + np.diag(penalized / (sigma ** 2))


def load(path):
    return [r for r in csv.DictReader(open(path, encoding="utf-8"), delimiter="\t") if r["stream"] == "substitution"]


def main(lexibank, wiktionary, diachronica, out):
    rows = load(lexibank) + load(wiktionary)
    inv = defaultdict(set)
    for r in rows:
        if r["reflex"] != "-":
            inv[r["branch"]].add(r["reflex"])
    rules = json.load(open(diachronica, encoding="utf-8"))["rules"]
    catalogues = {}
    for fam in FIT_FAMILIES + HELD_OUT:
        leave = set(EXCLUDED_SECTIONS)
        if FAMILY_SECTION.get(fam):
            leave.add(FAMILY_SECTION[fam])
        catalogues[fam] = Catalogue(rules, leave)
    fit_rows = [r for r in rows if r["family"] in FIT_FAMILIES]
    branches = sorted({r["branch"] for r in fit_rows})
    bidx = {b: i for i, b in enumerate(branches)}
    names, idx, penalized = layout(len(branches))
    print(f"{len(fit_rows)} fitting opportunities, {len(branches)} branches, {len(names)} parameters", file=sys.stderr)

    # leave-one-family-out choice of sigma: one design, sliced per fold. A
    # held-out family's branch offsets get no data in its fold, so the
    # penalty keeps them at 0: the prediction for an unseen branch.
    dall = Design(fit_rows, inv, catalogues, bidx, names, idx)
    fam_of = np.array([r["family"] for r in fit_rows])
    cv = {}
    for sigma in SIGMAS:
        total = 0.0
        for fam in FIT_FAMILIES:
            tr = dall.subset(np.nonzero(fam_of != fam)[0])
            te = dall.subset(np.nonzero(fam_of == fam)[0])
            theta, _ = fit(tr, len(names), penalized, sigma)
            total += -te.logprobs(theta)[te.chosen].sum()
        cv[sigma] = total / len(fit_rows)
        print(f"sigma {sigma}: leave-one-family-out log-loss {cv[sigma]:.4f}", file=sys.stderr)
    sigma = min(cv, key=cv.get)
    theta, res = fit(dall, len(names), penalized, sigma)
    H = hessian(theta, dall, penalized, sigma)
    cov = np.linalg.pinv(H)
    pack = {
        "format_version": 1, "kind": "alteruphono change model", "variant": "full",
        "merkmal_system": SYSTEM, "feature_labels": LABELS, "parameters": names,
        "theta": theta.tolist(), "se": np.sqrt(np.clip(np.diag(cov), 0, None)).tolist(),
        "sigma": sigma, "cv_log_loss": cv, "fit_families": list(FIT_FAMILIES),
        "branches": branches, "n_opportunities": len(fit_rows),
        "converged": bool(res.success), "message": str(res.message),
        "gap": GAP,
    }
    json.dump(pack, open(out, "w", encoding="utf-8"))
    np.save(out.replace(".json", "_cov.npy"), cov)
    print(f"chosen sigma {sigma}; lam = {theta[idx['lam']]:.3f} ± {math.sqrt(max(cov[idx['lam'], idx['lam']], 0)):.3f}; "
          f"beta = {theta[idx['beta']]:.3f}; converged {res.success}", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:5])
