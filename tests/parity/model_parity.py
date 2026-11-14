"""The C change-model scorer against the Python reference (fit.py's Design).

    python tests/parity/model_parity.py <lexibank.tsv> <wiktionary.tsv> <diachronica.json> <model.json> <pack dir>

For each held-out family: export a pack with that family's catalogue
(leave-out as in the gate), score every opportunity in C and in Python, and
report the largest absolute difference of log-probabilities, and the time
per opportunity of each.
"""

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from alteruphono.model import calibrate as cal
from alteruphono.model.fit import HELD_OUT, Design, layout, load
from alteruphono.model.pack import ChangeModel, export


def main(lexibank, wiktionary, diachronica, model_path, pack_dir):
    rows = load(lexibank) + load(wiktionary)
    inv = defaultdict(set)
    for r in rows:
        if r["reflex"] != "-":
            inv[r["branch"]].add(r["reflex"])
    pack = json.load(open(model_path, encoding="utf-8"))
    theta = np.array(pack["theta"])
    names, idx, _ = layout(len(pack["branches"]))
    rules = json.load(open(diachronica, encoding="utf-8"))["rules"]
    worst = 0.0
    for fam in HELD_OUT:
        sub = [r for r in rows if r["family"] == fam]
        leave = set(cal.EXCLUDED_SECTIONS)
        if cal.FAMILY_SECTION.get(fam):
            leave.add(cal.FAMILY_SECTION[fam])
        cat = cal.Catalogue(rules, leave)
        path = Path(pack_dir) / f"parity_{fam}.pack"
        export(path, names, theta, cat.rules, note=f"parity pack, catalogue for {fam}")
        t0 = time.perf_counter()
        d = Design(sub, inv, {fam: cat}, {}, names, idx)
        lp = d.logprobs(theta)
        t_py = time.perf_counter() - t0
        model = ChangeModel(path)
        t0 = time.perf_counter()
        out = []
        for r in sub:
            C = sorted(inv[r["branch"]] | {r["source"], "-"})
            out.extend(model.logprob(r["source"], r["left"], r["right"], C))
        t_c_cold = time.perf_counter() - t0
        t0 = time.perf_counter()
        for r in sub:
            C = sorted(inv[r["branch"]] | {r["source"], "-"})
            model.logprob(r["source"], r["left"], r["right"], C)
        t_c_warm = time.perf_counter() - t0
        diff = float(np.max(np.abs(np.array(out) - lp)))
        worst = max(worst, diff)
        print(f"{fam}: {len(sub)} opportunities, {len(out)} candidate scores; max |C - Python| = {diff:.3e}; "
              f"Python design {t_py / len(sub) * 1e6:.0f} us/opp (catalogue cache warm), "
              f"C cold {t_c_cold / len(sub) * 1e6:.0f} us/opp, C warm {t_c_warm / len(sub) * 1e6:.1f} us/opp")
    print("max difference over all:", f"{worst:.3e}")
    return 0 if worst < 1e-9 else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:6]))
