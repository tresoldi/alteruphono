"""Python reference for the parity harness.

Run with alteruphono 1.x on sys.path (a checkout of tag v1.0.0rc1-simultaneous
with tresoldi/alteruphono 3fdb52b applied; see tests/parity/README.md):

    PYTHONPATH=<oracle checkout> python -I tests/parity/oracle.py [--features 1x|merkmal] [--quantifiers 1x|fixed]

It reads the same lines as tools/cli.c ("F\\t<rule>\\t<seq>" or "B\\t...") and
writes the same output format.

--features merkmal replaces 1.x's feature table with the `alteruphono-1`
projection of merkmal's `descriptive` system (docs/v2/DESIGN.md 4.1), written
here independently of the C code. The C engine must agree with
`--features merkmal --quantifiers fixed` exactly; the differences between that
and `--features 1x` are the feature changes listed for Tiago.

--quantifiers fixed replaces 1.x's quantified-rule branch of forward (bugs Q1,
Q2) with the simultaneous semantics of DESIGN 5, again written independently
of the C code.
"""

from __future__ import annotations

import argparse
import sys
import unicodedata

import alteruphono
from alteruphono import backward, forward, parse_rule, parse_sequence
from alteruphono import forward as forward_module_func  # noqa: F401
from alteruphono.features import get_system
from alteruphono.features import ipa
from alteruphono.match import _match_one, build_syllable_map
from alteruphono.modifiers import apply_modifiers
from alteruphono.types import (
    BackRefToken,
    Boundary,
    BoundaryToken,
    EmptyToken,
    QuantifiedToken,
    SegmentToken,
    SetToken,
    Sound,
)

TONES = {
    (4, 3, 2): "with_falling_tone",
    (3, 3, 3): "with_mid_tone",
    (2, 2, 2): "with_low_tone",
    (4, 4, 4): "with_high_tone",
    (2, 3, 4): "with_rising_tone",
}


def merkmal_projection() -> dict[str, frozenset[str]]:
    """grapheme -> labels, over 1.x's grapheme universe, from merkmal."""
    import merkmal
    from alteruphono import resources

    vocab = set(ipa.FEATURE_CATEGORIES) | set(ipa._TONE_VALUES)
    finer_places = {k for k, v in ipa.FEATURE_CATEGORIES.items() if v == "place"} - {"labial"}
    table: dict[str, frozenset[str]] = {}
    for g in resources.load_sounds():
        try:
            labels = merkmal.get_features(g, "descriptive")
        except Exception:  # noqa: BLE001 - merkmal does not know it: None
            continue
        tone = {}
        out = set()
        for lab in labels:
            for part in ("onset", "mid", "offset"):
                pre = f"tone-{part}-"
                if lab.startswith(pre) and lab[len(pre):].isdigit() and len(lab) == len(pre) + 1:
                    tone[part] = int(lab[len(pre):])
            if lab in vocab:
                out.add(lab)
        if "tone-present" in labels:
            name = TONES.get((tone.get("onset"), tone.get("mid"), tone.get("offset")))
            if name:
                out.add(name)
        if "labial" in out and out & finer_places:
            out.discard("labial")
        if out:
            table[g] = frozenset(out)
    return table


def install_merkmal_features() -> None:
    table = merkmal_projection()
    reverse: dict[frozenset[str], str] = {}
    for g, f in table.items():
        reverse.setdefault(f, g)
    ipa._build_grapheme_table = lambda: table
    ipa._build_features_to_grapheme = lambda: reverse


# ---- fixed quantified forward ------------------------------------------------


def _quant_forward(sequence, rule, system_name=None):
    sys_ = get_system(system_name)
    n = len(sequence)
    ante = rule.ante
    total = len(ante)
    left_n, right_n = rule.left_len, rule.right_len
    smap = build_syllable_map(sequence, system_name) if any(
        type(t).__name__ == "SyllableCondToken" for t in ante
    ) else None

    def one(pos, tok):
        return _match_one(sequence[pos], tok, sys_, smap, pos)

    out = []
    idx = 0
    while idx < n:
        spans = [(0, 0)] * total
        bound = {}

        def fwd(ti, edge):
            if ti >= total:
                return True
            tok = ante[ti]
            if isinstance(tok, QuantifiedToken):
                k = 0
                while edge + k < n and one(edge + k, tok.inner) is not None:
                    k += 1
                if tok.quantifier == "?":
                    spans[ti] = (edge, 0)
                    if fwd(ti + 1, edge):
                        return True
                    if k >= 1:
                        bound[edge] = one(edge, tok.inner)
                        spans[ti] = (edge, 1)
                        return fwd(ti + 1, edge + 1)
                    return False
                for take in range(k, 0, -1):
                    for p in range(edge, edge + take):
                        bound[p] = one(p, tok.inner)
                    spans[ti] = (edge, take)
                    if fwd(ti + 1, edge + take):
                        return True
                return False
            if edge >= n:
                return False
            m = one(edge, tok)
            if m is None:
                return False
            bound[edge] = m
            spans[ti] = (edge, 1)
            return fwd(ti + 1, edge + 1)

        def back(ti, edge):
            if ti < 0:
                return fwd(left_n, idx)
            tok = ante[ti]
            if isinstance(tok, QuantifiedToken):
                k = 0
                while edge - 1 - k >= 0 and one(edge - 1 - k, tok.inner) is not None:
                    k += 1
                if tok.quantifier == "?":
                    spans[ti] = (edge, 0)
                    if back(ti - 1, edge):
                        return True
                    if k >= 1:
                        bound[edge - 1] = one(edge - 1, tok.inner)
                        spans[ti] = (edge - 1, 1)
                        return back(ti - 1, edge - 1)
                    return False
                for take in range(k, 0, -1):
                    for p in range(edge - take, edge):
                        bound[p] = one(p, tok.inner)
                    spans[ti] = (edge - take, take)
                    if back(ti - 1, edge - take):
                        return True
                return False
            if edge <= 0:
                return False
            m = one(edge - 1, tok)
            if m is None:
                return False
            bound[edge - 1] = m
            spans[ti] = (edge - 1, 1)
            return back(ti - 1, edge - 1)

        ok = back(left_n - 1, idx) if left_n > 0 else fwd(0, idx)
        if not ok:
            out.append(sequence[idx])
            idx += 1
            continue
        sets = [
            bound[p]
            for ti in range(total)
            for p in range(spans[ti][0], spans[ti][0] + spans[ti][1])
            if isinstance(bound[p], int)
        ]
        set_iter = iter(sets)
        for tok in rule.post[left_n: len(rule.post) - right_n]:
            if isinstance(tok, EmptyToken):
                continue
            if isinstance(tok, SegmentToken):
                out.append(tok.sound)
            elif isinstance(tok, SetToken):
                i = next(set_iter, None)
                if i is None or i >= len(tok.choices):
                    raise ValueError("Set correspondence mismatch")
                if isinstance(tok.choices[i], SegmentToken):
                    out.append(tok.choices[i].sound)
            elif isinstance(tok, BackRefToken):
                if not (0 <= tok.index < total) or spans[tok.index][1] == 0:
                    continue
                start, count = spans[tok.index]
                elem = sequence[start + count - 1]
                if tok.modifier and isinstance(elem, Sound) and elem.features:
                    feats = apply_modifiers(elem.features, tok.modifier, sys_)
                    g = sys_.features_to_grapheme(feats)
                    if g:
                        from alteruphono.features import normalize_output

                        g = normalize_output(g)
                    out.append(Sound(grapheme=g or elem.grapheme, features=feats))
                else:
                    out.append(elem)
            elif isinstance(tok, BoundaryToken):
                out.append(Boundary())
        focus = sum(spans[t][1] for t in range(left_n, total - right_n))
        if focus > 0:
            idx += focus
        else:
            out.append(sequence[idx])
            idx += 1
    return tuple(out)


def fixed_forward(sequence, rule, system_name=None):
    if len(rule.ante) == 0 or len(sequence) == 0:
        return sequence
    if any(isinstance(t, QuantifiedToken) for t in rule.ante):
        return _quant_forward(sequence, rule, system_name)
    return forward(sequence, rule, system_name)


# ---- output ------------------------------------------------------------------


def fmt_elem(e) -> str:
    if isinstance(e, Boundary):
        return "#\x1e\x1e0"
    return f"{e.grapheme}\x1e{','.join(sorted(e.features))}\x1e{1 if e.partial else 0}"


def fmt_seq(seq) -> str:
    return "\x1f".join(fmt_elem(e) for e in seq)


MAX_BACKWARD_CANDIDATES = 100000  # ap_context_options default


class _CappedItertools:
    """1.x backward has no cap on its products; the C engine refuses a product
    of more than MAX_BACKWARD_CANDIDATES (AP_ERR_LIMIT). Same rule here."""

    def __getattr__(self, name):
        import itertools

        return getattr(itertools, name)

    @staticmethod
    def product(*iterables):
        import itertools
        import math

        lists = [list(it) for it in iterables]
        if math.prod(len(x) for x in lists) > MAX_BACKWARD_CANDIDATES:
            raise OverflowError("backward candidates over the cap")
        return itertools.product(*lists)


def main() -> None:
    import resource

    # not "import alteruphono.backward as _bw": the package rebinds that name
    # to the backward() function, and the shim would land on the function
    sys.modules["alteruphono.backward"].itertools = _CappedItertools()
    resource.setrlimit(resource.RLIMIT_AS, (2 << 30, 2 << 30))
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", choices=("1x", "merkmal"), default="1x")
    ap.add_argument("--quantifiers", choices=("1x", "fixed"), default="fixed")
    args = ap.parse_args()
    if args.features == "merkmal":
        install_merkmal_features()
    fwd = fixed_forward if args.quantifiers == "fixed" else forward
    sys.stderr.write(f"oracle: alteruphono {alteruphono.__version__} from {alteruphono.__file__}\n")
    for line in sys.stdin:
        line = line.rstrip("\n")
        op, _, rest = line.partition("\t")
        rule_text, _, seq_text = rest.partition("\t")
        try:
            rule = parse_rule(rule_text)
            seq = parse_sequence(seq_text)
            if op == "F":
                res = "OK\t" + fmt_seq(fwd(seq, rule))
            else:
                res = "OK\t" + "\x1d".join(fmt_seq(c) for c in backward(seq, rule))
        except (RecursionError, MemoryError) as e:
            res = f"ERR\t{type(e).__name__}"
        except Exception as e:  # noqa: BLE001
            res = f"ERR\t{type(e).__name__}"
        sys.stdout.write(res + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    unicodedata.normalize("NFD", "")  # fail early if unicodedata is missing
    main()
