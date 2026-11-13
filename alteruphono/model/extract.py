"""Proto->daughter pairs and opportunities from Lexibank (TRAINING_SPLIT.md 3).

    python -m alteruphono.model.extract <data dir> <out.tsv>

Rules, fixed before the first fit:
- A doculect is a proto-language if its Glottocode is a Glottolog subgroup
  node (Level "family"), or if it has none (Proto-Bora-Muinane, the root of
  its dataset's family).
- Each doculect is paired with its nearest proto ancestor in the same
  dataset: the proto whose Glottocode is deepest on the doculect's Glottolog
  classification path. Doculects outside every proto's subtree (Khmu, Jahai
  in sidwellvietic) are not paired.
- Within a pair, the two forms of one cognate set are used; a set with
  several forms on a side uses each combination (rare).
- Segments: Lexibank's "source/normalized" tokens give the normalized part;
  morpheme boundaries "+" and "_" and a leading "!" are removed; tone tokens
  (digits and tone letters only) are dropped: tone is outside this model.
- Alignment: Needleman-Wunsch with substitution cost = merkmal's
  `descriptive` dissimilarity (0 for identity, 1 when merkmal cannot compare)
  and gap cost GAP. A pair with more than one optimal alignment that differ
  in their segment pairing is dropped (counted), not guessed.
- Every proto segment is an opportunity: its reflex is a segment, or "-"
  (deletion). Daughter segments aligned to no proto segment are insertions,
  recorded in their own stream.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from functools import cache
from pathlib import Path

import merkmal

GAP = 0.55
SYSTEM = "descriptive"
TONE_CHARS = set("0123456789¹²³⁴⁵⁶⁷⁸⁹⁰˥˦˧˨˩/")
DATASETS = {
    "lionnetyotonahua": "Uto-Aztecan",
    "pharaocoracholaztecan": "Uto-Aztecan",
    "davletshinaztecan": "Uto-Aztecan",
    "seifartecheverriboran": "Bora-Muinane",
    "sidwellvietic": "Austroasiatic",
}


def clean_segments(text: str) -> list[str]:
    out = []
    for tok in text.split():
        if tok in ("+", "_", "#"):
            continue
        tok = tok.lstrip("!")
        if "/" in tok:
            tok = tok.split("/", 1)[1]
        if not tok or all(ch in TONE_CHARS for ch in tok):
            continue
        out.append(tok)
    return out


@cache
def dist(a: str, b: str) -> float:
    if a == b:
        return 0.0
    try:
        return float(merkmal.distance(a, b, SYSTEM))
    except Exception:  # noqa: BLE001 - not comparable
        return 1.0


def align(p: list[str], d: list[str]) -> list[tuple[str | None, str | None]] | None:
    """Optimal alignment, or None if the optimum is not unique in its pairing."""
    n, m = len(p), len(d)
    cost = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        cost[i][0] = i * GAP
    for j in range(1, m + 1):
        cost[0][j] = j * GAP
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost[i][j] = min(cost[i - 1][j - 1] + dist(p[i - 1], d[j - 1]),
                             cost[i - 1][j] + GAP, cost[i][j - 1] + GAP)

    def moves(i, j):
        out = []
        eps = 1e-9
        if i > 0 and j > 0 and abs(cost[i][j] - cost[i - 1][j - 1] - dist(p[i - 1], d[j - 1])) < eps:
            out.append((i - 1, j - 1))
        if i > 0 and abs(cost[i][j] - cost[i - 1][j] - GAP) < eps:
            out.append((i - 1, j))
        if j > 0 and abs(cost[i][j] - cost[i][j - 1] - GAP) < eps:
            out.append((i, j - 1))
        return out

    # walk one optimal path; at every branching point check whether the other
    # optimal branch would pair segments differently
    path = []
    i, j = n, m
    while i > 0 or j > 0:
        ms = moves(i, j)
        if len(ms) > 1:
            return None
        pi, pj = ms[0]
        path.append((p[i - 1] if pi < i else None, d[j - 1] if pj < j else None))
        i, j = pi, pj
    path.reverse()
    return path


def load_glottolog(gdir: Path):
    level = {r["ID"]: r["Level"] for r in csv.DictReader((gdir / "languages.csv").open(encoding="utf-8"))}
    path = {}
    with (gdir / "values.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Parameter_ID"] == "classification":
                path[r["Language_ID"]] = r["Value"].split("/") if r["Value"] else []
    return level, path


def pairs_for(ds_dir: Path, level, gpath):
    langs = list(csv.DictReader((ds_dir / "cldf" / "languages.csv").open(encoding="utf-8")))
    glot = {l["ID"]: l["Glottocode"] for l in langs}
    protos = [l["ID"] for l in langs if not glot[l["ID"]] or level.get(glot[l["ID"]]) == "family"]
    roots = [p for p in protos if not glot[p]]

    def lineage(doculect):
        g = glot[doculect]
        return (gpath.get(g, []) + [g]) if g else []

    parent = {}
    for doc in [l["ID"] for l in langs]:
        line = lineage(doc)
        best, depth = None, -1
        for p in protos:
            if p == doc:
                continue
            gp = glot[p]
            if gp and gp in line[:-1] and line.index(gp) > depth:
                best, depth = p, line.index(gp)
        if best is None and roots and doc not in roots:
            best = roots[0]  # a proto with no Glottocode is its dataset's root
        if best is not None:
            parent[doc] = best
    forms = {r["ID"]: r for r in csv.DictReader((ds_dir / "cldf" / "forms.csv").open(encoding="utf-8"))}
    cogs = defaultdict(lambda: defaultdict(list))
    cfile = ds_dir / "cldf" / "cognates.csv"
    if cfile.exists():
        for r in csv.DictReader(cfile.open(encoding="utf-8")):
            f = forms.get(r["Form_ID"])
            if f is not None and r["Cognateset_ID"]:
                cogs[r["Cognateset_ID"]][f["Language_ID"]].append(f)
    else:
        for f in forms.values():
            key = f.get("ProtoSet") or f.get("Cognacy")
            if key:
                cogs[key][f["Language_ID"]].append(f)
    for cs, by_lang in cogs.items():
        for doc, proto in parent.items():
            for pf in by_lang.get(proto, []):
                for df in by_lang.get(doc, []):
                    yield cs, proto, doc, clean_segments(pf["Segments"]), clean_segments(df["Segments"])


def main(data: str, out: str) -> None:
    data_dir = Path(data)
    level, gpath = load_glottolog(data_dir / "glottolog")
    stats = Counter()
    with open(out, "w", encoding="utf-8", newline="") as fo:
        w = csv.writer(fo, delimiter="\t", lineterminator="\n")
        w.writerow(["family", "dataset", "cogset", "branch", "stream", "position", "source", "left", "right", "reflex"])
        for ds, family in DATASETS.items():
            for cs, proto, doc, p, d in pairs_for(data_dir / "lexibank" / ds, level, gpath):
                stats[(ds, "pairs")] += 1
                if not p or not d:
                    stats[(ds, "empty")] += 1
                    continue
                al = align(p, d)
                if al is None:
                    stats[(ds, "ambiguous")] += 1
                    continue
                stats[(ds, "aligned")] += 1
                branch = f"{ds}:{proto}>{doc}"
                pos = 0
                for k, (a, b) in enumerate(al):
                    if a is None:
                        w.writerow([family, ds, cs, branch, "insertion", pos, "", p[pos - 1] if pos > 0 else "#",
                                    p[pos] if pos < len(p) else "#", b])
                        continue
                    left = p[pos - 1] if pos > 0 else "#"
                    right = p[pos + 1] if pos + 1 < len(p) else "#"
                    w.writerow([family, ds, cs, branch, "substitution", pos, a, left, right, b if b is not None else "-"])
                    pos += 1
                    stats[(ds, "opportunities")] += 1
    for k in sorted(stats):
        print(*k, stats[k], sep="\t", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:3])
