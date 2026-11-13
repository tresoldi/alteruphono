"""Change-model packs: export from the fitter, load into the C scorer.

A pack is text (see include/alteruphono.h): the merkmal system's
feature-vector labels, the parameters (branch offsets are dropped: a
consumer passes its own), and the catalogue rules with their weights. A pack
built with Index Diachronica carries its rules verbatim: keep it under the
git-ignored data/, never commit it (DESIGN D6).
"""

from __future__ import annotations

from alteruphono import _core, _native

MAGIC = "alteruphono-change-model\t1"


def export(path, names, theta, rules, system="descriptive", note=""):
    """rules: (text, weight) pairs, in order (the fitter's Catalogue.rules)."""
    import merkmal  # only the exporter needs merkmal's Python package

    lines = [MAGIC, f"system\t{system}", "labels\t" + "\t".join(merkmal.vector_labels(system))]
    if note:
        lines.append("% " + note.replace("\n", " "))
    for n, v in zip(names, theta):
        if not n.startswith("alpha:"):
            lines.append(f"param\t{n}\t{float(v)!r}")
    for text, w in rules:
        if "\t" in text or "\n" in text:
            continue
        lines.append(f"rule\t{float(w)!r}\t{text}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


class ChangeModel:
    """A loaded pack, scored by the C engine (one thread at a time)."""

    def __init__(self, path):
        with open(path, encoding="utf-8") as f:
            self._model = _native.model_load(_core.context(), f.read())

    def eta(self, source, left, right, candidates, branch_offset=0.0):
        return _native.model_eta(_core.context(), self._model, source, left, right, list(candidates), branch_offset)

    def logprob(self, source, left, right, candidates, branch_offset=0.0):
        return _native.model_logprob(_core.context(), self._model, source, left, right, list(candidates), branch_offset)

    def relative_rates(self, source, left, right, candidates):
        """exp(eta) for every candidate other than the source (the source gets 0):
        the rows of a rate matrix whose overall rate the consumer sets."""
        import math

        eta = self.eta(source, left, right, candidates)
        return [0.0 if y == source else math.exp(e) for y, e in zip(candidates, eta)]
