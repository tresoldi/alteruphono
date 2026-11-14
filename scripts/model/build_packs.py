"""The two change-model packs of blindrec's v16 (PREREG, "Learned relative
rates in stage 5 (v16)"): F2 (sigma_src = sigma_rest = 0.03, chosen in M4b)
fitted on the four fitting families of TRAINING_SPLIT.md.

  sim   catalogue = Index Diachronica half A (the sections in id_halves.json)
        plus alteruphono's catalogue; the simulator of the fresh test
        families uses half B only
  real  catalogue = Index Diachronica minus the excluded sections
        (TRAINING_SPLIT.md 4) plus alteruphono's catalogue

In fitting, each family's own section is left out of the catalogue its
opportunities see, as in M4. Packs carry Index Diachronica rules verbatim:
written under the git-ignored data/, never committed.

    python scripts/model/build_packs.py <data/derived>
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from alteruphono.model import calibrate as cal
from alteruphono.model.fit import FIT_FAMILIES, Design, fit, layout, load
from alteruphono.model.m4b import sigma_vector
from alteruphono.model.pack import export

SIGMA = (0.03, 0.03)


def main(derived):
    d = Path(derived)
    rows = load(d / "lexibank_opportunities.tsv") + load(d / "wiktionary_opportunities.tsv")
    inv = defaultdict(set)
    for r in rows:
        if r["reflex"] != "-":
            inv[r["branch"]].add(r["reflex"])
    rules = json.load(open(d / "diachronica_rules.json", encoding="utf-8"))["rules"]
    halves = json.load(open(d / "id_halves.json", encoding="utf-8"))
    fit_rows = [r for r in rows if r["family"] in FIT_FAMILIES]
    branches = sorted({r["branch"] for r in fit_rows})
    bidx = {b: i for i, b in enumerate(branches)}
    names, idx, penalized = layout(len(branches))
    for kind in ("sim", "real"):
        keep = set(halves["A"]) if kind == "sim" else None
        base_leave = set() if kind == "sim" else set(cal.EXCLUDED_SECTIONS)
        cats = {fam: cal.Catalogue(rules, base_leave | {cal.FAMILY_SECTION[fam]}, keep) for fam in FIT_FAMILIES}
        design = Design(fit_rows, inv, cats, bidx, names, idx)
        theta, res = fit(design, len(names), penalized, sigma_vector(names, *SIGMA))
        final = cal.Catalogue(rules, base_leave, keep)
        out = d / f"v16_{kind}.pack"
        export(out, names, theta, final.rules,
               note=f"blindrec v16 {kind} pack; F2 sigma {SIGMA}; fitted on {', '.join(FIT_FAMILIES)}; "
                    f"converged {res.success}")
        print(kind, "lam", round(float(theta[idx["lam"]]), 4), "beta", round(float(theta[idx["beta"]]), 3),
              "rules", len(final.rules), "converged", res.success, "->", out, file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1])
