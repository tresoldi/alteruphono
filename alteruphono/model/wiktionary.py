"""Proto->proto pairs from Wiktionary (kaikki dumps), TRAINING_SPLIT.md 3.

    python -m alteruphono.model.wiktionary <data dir> <out.tsv>

Fixed before the first fit of a Wiktionary family (M4):
- Pairs: a reconstruction and its nearest reconstructed ancestor (a starred
  form) in a descendant tree, both proto-languages (code ending "-pro") of
  the same family. Family membership is by Wiktionary language code: Uralic
  urj-/syd-/smi-/fiu-/ugr- plus sel-pro (Selkup), chm-pro (Mari), kca-pro
  (Khanty), mns-pro (Mansi); Japonic jpx-; Turkic trk-. Cross-family
  "descendants" (loans) and starred forms of attested languages (Volga
  Bulgar, Mator, ...) are dropped. (A first version used prefixes only and
  dropped Proto-Selkup, -Mari, -Khanty and -Mansi; caught before any fit.)
- Notation to IPA: the tables below, one per family, applied to the NFD
  form. Hyphens (morpheme or stem boundaries) are removed. A form is dropped
  (and counted), not guessed, when it contains a character the table does
  not map, an archiphoneme capital, an optional segment "(...)", an
  alternative "~" or "/", a question mark, or a segment merkmal's
  `descriptive` system does not resolve.
- Alignment and opportunities: as alteruphono.model.extract (same aligner,
  gap cost and ambiguity rule).

The tables follow common practice for each tradition (Uralic phonetic
alphabet as used on Wiktionary; Turkological transcription; Japonic
reconstructions in phonemic letters). They are approximations: a convention
mapped wrongly is wrong consistently on both sides of a pair, which biases
the learned changes less than a random error would, but does bias them.
"""

from __future__ import annotations

import csv
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import merkmal

from alteruphono.model.extract import align

FILES = {
    "Uralic": ["ProtoUralic", "ProtoSamoyedic", "ProtoFinnic", "ProtoSami", "ProtoPermic"],
    "Japonic": ["ProtoJaponic", "ProtoRyukyuan"],
    "Turkic": ["ProtoTurkic"],
}
CODES = {
    "Uralic": ("urj", "syd", "smi", "fiu", "ugr", "sel-pro", "chm-pro", "kca-pro", "mns-pro"),
    "Japonic": ("jpx",),
    "Turkic": ("trk",),
}
ROOT_CODE = {
    "ProtoUralic": "urj-pro", "ProtoSamoyedic": "syd-pro", "ProtoFinnic": "urj-fin-pro",
    "ProtoSami": "smi-pro", "ProtoPermic": "urj-prm-pro", "ProtoJaponic": "jpx-pro",
    "ProtoRyukyuan": "jpx-ryu-pro", "ProtoTurkic": "trk-pro",
}

COMB_ACUTE, COMB_CARON, COMB_MACRON, COMB_DIAER = "́", "̌", "̄", "̈"
COMB_BREVE_BELOW, COMB_DOT_ABOVE, COMB_DOT_BELOW = "̮", "̇", "̣"
COMB_BREVE, COMB_RING = "\u0306", "\u030a"

# base letters shared by the three tables (IPA-valued letters map to themselves)
BASE = {c: c for c in "abdefghijklmnopqrstuvwxz"}
BASE.update({"y": "j", "ŋ": "ŋ", "ə": "ə", "ǝ": "ə", "ɣ": "ɣ", "γ": "ɣ", "δ": "ð", "θ": "θ", "ʒ": "ʒ",
             "ʔ": "ʔ", "ɨ": "ɨ", "ɛ": "ɛ", "ɔ": "ɔ", "ʌ": "ʌ", "ɬ": "ɬ", "χ": "χ", "c": "ts"})

# (base, diacritic) -> IPA, per family; applied before BASE
URALIC = {
    ("s", COMB_CARON): "ʃ", ("z", COMB_CARON): "ʒ", ("c", COMB_CARON): "tʃ", ("ʒ", COMB_CARON): "dʒ",
    ("s", COMB_ACUTE): "sʲ", ("z", COMB_ACUTE): "zʲ", ("c", COMB_ACUTE): "tsʲ", ("n", COMB_ACUTE): "ɲ",
    ("l", COMB_ACUTE): "ʎ", ("r", COMB_ACUTE): "rʲ", ("t", COMB_ACUTE): "tʲ", ("d", COMB_ACUTE): "dʲ",
    ("ð", COMB_ACUTE): "ðʲ", ("δ", COMB_ACUTE): "ðʲ", ("t", COMB_CARON): "tʲ", ("d", COMB_CARON): "dʲ",
    ("a", COMB_DIAER): "æ", ("o", COMB_DIAER): "ø", ("u", COMB_DIAER): "y", ("e", COMB_DIAER): "ɤ",
    ("i", COMB_DIAER): "ɨ",
    ("a", COMB_BREVE_BELOW): "ɑ", ("e", COMB_BREVE_BELOW): "ɤ", ("i", COMB_BREVE_BELOW): "ɨ",
    ("o", COMB_BREVE_BELOW): "ɤ", ("u", COMB_BREVE_BELOW): "ɯ",
    ("x", ""): "x", ("w", ""): "w",
    # added after the first extraction run, before any fit (counted failures):
    # å is an open back rounded vowel; the breve marks a reduced (extra-short)
    # vowel, which IPA writes the same way; ľ is the palatal lateral; dotted
    # u, o are centralized
    ("a", COMB_RING): "ɔ", ("ɜ", ""): "ɜ", ("l", COMB_CARON): "ʎ",
    ("u", COMB_DOT_ABOVE): "ʉ", ("o", COMB_DOT_ABOVE): "ɵ",
    **{(v, COMB_BREVE): v + COMB_BREVE for v in "aeiou"},
    ("a", COMB_DIAER + COMB_BREVE): "æ" + COMB_BREVE, ("u", COMB_DIAER + COMB_BREVE): "y" + COMB_BREVE,
}
TURKIC = {
    ("s", COMB_CARON): "ʃ", ("z", COMB_CARON): "ʒ", ("c", COMB_CARON): "tʃ", ("g", COMB_CARON): "dʒ",
    ("j", COMB_CARON): "dʒ", ("a", COMB_DIAER): "æ", ("o", COMB_DIAER): "ø", ("u", COMB_DIAER): "y",
    ("i", COMB_DIAER): "ɯ", ("e", COMB_DOT_BELOW): "e", ("ı", ""): "ɯ", ("q", ""): "q",
    ("y", ""): "j", ("x", ""): "x", ("ŋ", ""): "ŋ",
    # Proto-Turkic *ŕ, *ĺ (r2, l2) and *ń: palatalized r, palatal l and n by
    # the usual reading; added after the first extraction run, before any fit
    ("r", COMB_ACUTE): "rʲ", ("l", COMB_ACUTE): "ʎ", ("n", COMB_ACUTE): "ɲ",
}
JAPONIC = {("y", ""): "j", ("w", ""): "w", ("z", ""): "z", ("ə", ""): "ə", ("ǝ", ""): "ə", ("ɨ", ""): "ɨ"}
TABLES = {"Uralic": URALIC, "Turkic": TURKIC, "Japonic": JAPONIC}
VOWELS = set("aeiouæøyɤɨɯɑəɛɔʌ")


class Unmapped(Exception):
    pass


def convert(form: str, family: str) -> list[str]:
    """IPA segments of a reconstruction, or Unmapped."""
    f = unicodedata.normalize("NFD", form.strip().lstrip("*").replace("-", ""))
    if not f or any(ch in f for ch in "()~/?,‹›") or any(ch.isupper() for ch in f):
        raise Unmapped(form)
    table = TABLES[family]
    segs: list[str] = []
    i = 0
    while i < len(f):
        base = f[i]
        i += 1
        marks = ""
        while i < len(f) and unicodedata.combining(f[i]):
            marks += f[i]
            i += 1
        long_ = COMB_MACRON in marks
        marks = marks.replace(COMB_MACRON, "")
        if (base, marks) in table:
            seg = table[(base, marks)]
        elif marks == "" and base in BASE:
            seg = BASE[base]
        else:
            raise Unmapped(form)
        if long_:
            if seg[-1] not in VOWELS:
                raise Unmapped(form)
            seg += "ː"
        # a doubled letter is two segments (a geminate or a long vowel written twice)
        segs.append(seg)
    for s in segs:
        if not merkmal.is_segment(s, "descriptive"):
            raise Unmapped(form)
    return segs


def pairs(data_dir: Path, family: str, stats: Counter):
    seen = set()
    for name in FILES[family]:
        for line in (data_dir / "kaikki" / f"{name}.jsonl").open(encoding="utf-8"):
            e = json.loads(line)
            root = (ROOT_CODE[name], "*" + e["word"].lstrip("*"))

            def walk(ds, parent):
                for d in ds or []:
                    w, code = d.get("word"), d.get("lang_code") or ""
                    here = parent
                    if w and w.startswith("*"):
                        if code.endswith("-pro") and code.startswith(CODES[family]):
                            key = (parent, (code, w))
                            if key not in seen:
                                seen.add(key)
                                yield parent, (code, w)
                            here = (code, w)
                        else:
                            stats[(family, "cross-family descendant dropped")] += 1
                    yield from walk(d.get("descendants"), here)

            yield from walk(e.get("descendants"), root)


def main(data: str, out: str) -> None:
    data_dir = Path(data)
    stats = Counter()
    with open(out, "w", encoding="utf-8", newline="") as fo:
        w = csv.writer(fo, delimiter="\t", lineterminator="\n")
        w.writerow(["family", "dataset", "cogset", "branch", "stream", "position", "source", "left", "right", "reflex"])
        for family in FILES:
            for (pcode, pform), (dcode, dform) in pairs(data_dir, family, stats):
                stats[(family, "pairs")] += 1
                try:
                    p = convert(pform, family)
                    d = convert(dform, family)
                except Unmapped:
                    stats[(family, "unmapped form")] += 1
                    continue
                al = align(p, d)
                if al is None:
                    stats[(family, "ambiguous")] += 1
                    continue
                stats[(family, "aligned")] += 1
                branch = f"wiktionary:{pcode}>{dcode}"
                cs = f"{pcode}:{pform}"
                pos = 0
                for a, b in al:
                    if a is None:
                        w.writerow([family, "wiktionary", cs, branch, "insertion", pos, "",
                                    p[pos - 1] if pos > 0 else "#", p[pos] if pos < len(p) else "#", b])
                        continue
                    w.writerow([family, "wiktionary", cs, branch, "substitution", pos, a,
                                p[pos - 1] if pos > 0 else "#", p[pos + 1] if pos + 1 < len(p) else "#",
                                b if b is not None else "-"])
                    pos += 1
                    stats[(family, "opportunities")] += 1
    for k in sorted(stats):
        print(*k, stats[k], sep="\t", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:3])
