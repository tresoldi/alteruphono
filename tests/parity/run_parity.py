"""Differential parity between the C engine and alteruphono 1.x.

    python tests/parity/run_parity.py --cli <build>/alteruphono-cli \\
        --oracle <checkout of v1.0.0rc1-simultaneous + 3fdb52b> \\
        [--blindrec-cases cases.tsv] [--random 200000] [--seed 20261113] [--out report.json]

Case streams:
  catalogue   every rule of resources/sound_changes.tsv on its TEST_ANTE (forward)
              and its TEST_POST (backward), wrapped in "# ... #"
  regression  the simultaneous-application cases (upstream and blindrec)
  blindrec    a file of "F\\t<rule>\\t<seq>" lines made by make_blindrec_cases.py
  random      rules drawn from a grammar of the whole notation, on words from
              the catalogue's test forms (forward and backward)

Comparisons:
  engine      C  vs  oracle(--features merkmal --quantifiers fixed)   must be 0
  features    oracle(merkmal, fixed)  vs  oracle(1x, fixed)            listed
  quantifiers oracle(1x, fixed)  vs  oracle(1x, 1x)                    listed

Two results agree when both are OK with identical output (graphemes, sorted
features and the partial flag of every element), or when both are errors.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
ORACLE = Path(__file__).resolve().parent / "oracle.py"

REGRESSION = [
    ("p > b / V _ V", "# a p a p a #"),
    ("S > @1[+voiced] / V _ V", "# k i t a p e k #"),
    ("{p|t} > {b|d} / V _ V", "# a p a t a #"),
    ("t > :null: / t _", "# a t t t a #"),
    ("V s > @1 z @1 / # p|b r _ t|d", "# p r e s t o #"),
]


def catalogue_cases() -> list[str]:
    out = []
    with (ROOT / "resources" / "sound_changes.tsv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            out.append(f"F\t{row['RULE']}\t# {row['TEST_ANTE']} #")
            out.append(f"B\t{row['RULE']}\t# {row['TEST_POST']} #")
    return out


def regression_cases() -> list[str]:
    return [f"F\t{r}\t{s}" for r, s in REGRESSION]


# ---- random rules from a grammar of the notation ------------------------------

CLASSES = ["V", "C", "N", "S", "SV", "SVL", "F", "L", "R", "P", "K", "E", "B", "H", "Q", "A", "CV", "VN", "VL"]
ODD = ["é", "g", "ɡ", "t'", "tʼ", "ʘ", "x̃ʷ", "", "aː", "ʈʂː", "ǃǃ", "â", "ê̞", "bʱ"]
MODS = [
    "+voiced", "-voiced,+voiceless", "+voiceless,-voiced", "+fricative", "+nasalized", "+long",
    "+plosive", "-stop", "+velar", "+palatalized", "+front", "+rounded", "voiced", "+labial",
    "+aspirated", "+with_high_tone", "+bogus", "-vowel",
]


def segment_pool() -> list[str]:
    seen = Counter()
    with (ROOT / "resources" / "sound_changes.tsv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            seen.update(row["TEST_ANTE"].split())
            seen.update(row["TEST_POST"].split())
    return sorted(seen)


def words() -> list[str]:
    out = []
    with (ROOT / "resources" / "sound_changes.tsv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            out.append(row["TEST_ANTE"].split())
            out.append(row["TEST_POST"].split())
    return out


class Grammar:
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.segs = segment_pool()

    def seg(self) -> str:
        r = self.rng.random()
        if r < 0.45:
            return self.rng.choice(self.segs)
        if r < 0.9:
            return self.rng.choice(CLASSES)
        return self.rng.choice(ODD)

    def simple(self) -> str:
        r = self.rng.random()
        if r < 0.7:
            return self.seg()
        if r < 0.85:
            return "|".join(self.seg() for _ in range(self.rng.randint(2, 3)))
        return "#"

    def match_atom(self) -> str:
        r = self.rng.random()
        if r < 0.55:
            return self.simple()
        if r < 0.65:
            return "{" + "|".join(self.seg() for _ in range(self.rng.randint(2, 3))) + "}"
        if r < 0.75:
            return "!" + self.simple()
        if r < 0.88:
            return self.seg() + self.rng.choice("+?")
        if r < 0.93:
            return self.rng.choice(["_.onset", "_.nucleus", "_.coda"])
        return self.rng.choice(["@1", "{}", "a||b", "!", "{p|b}+", "@0"])

    def rule(self) -> str:
        rng = self.rng
        ante = [self.match_atom() for _ in range(rng.randint(1, 3))]
        post = []
        n_sets = sum(1 for a in ante if a.startswith("{") and a.endswith("}"))
        for _ in range(rng.randint(0, 3)):
            r = rng.random()
            if r < 0.35:
                post.append(self.seg())
            elif r < 0.65:
                k = rng.randint(0, len(ante) + 1)
                post.append(f"@{k}" + (f"[{rng.choice(MODS)}]" if rng.random() < 0.5 else ""))
            elif r < 0.75:
                post.append(":null:")
            elif r < 0.85 and n_sets:
                post.append("{" + "|".join(self.seg() for _ in range(rng.randint(2, 3))) + "}")
                n_sets -= 1
            elif r < 0.9:
                post.append("#")
            else:
                post.append(self.seg())
        if not post:
            post = [":null:"]
        text = " ".join(ante) + rng.choice([" > ", " -> ", " → ", ">"]) + " ".join(post)
        if rng.random() < 0.7:
            left = [self.match_atom() for _ in range(rng.choice([0, 0, 1, 1, 2]))]
            right = [self.match_atom() for _ in range(rng.choice([0, 0, 1, 1, 2]))]
            text += " / " + " ".join(left + ["_"] + right)
        return text

    def word(self, pool: list[list[str]]) -> str:
        w = list(self.rng.choice(pool))
        if self.rng.random() < 0.2 and w:
            w[self.rng.randrange(len(w))] = self.seg() or "a"
        if self.rng.random() < 0.9:
            return "# " + " ".join(w) + " #"
        return " ".join(w)


def random_cases(n: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    g = Grammar(rng)
    pool = words()
    out = []
    for i in range(n):
        op = "B" if i % 5 == 4 else "F"
        out.append(f"{op}\t{g.rule()}\t{g.word(pool)}")
    return out


# ---- running -----------------------------------------------------------------


def run(cmd: list[str], lines: list[str], env=None) -> list[str]:
    proc = subprocess.run(
        cmd, input="\n".join(lines) + "\n", capture_output=True, text=True, encoding="utf-8", env=env,
        check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr[-2000:])
        raise SystemExit(f"{cmd[0]} failed with {proc.returncode}")
    out = proc.stdout.split("\n")
    if out and out[-1] == "":
        out.pop()
    if len(out) != len(lines):
        raise SystemExit(f"{cmd} returned {len(out)} lines for {len(lines)}")
    return out


def oracle(lines, checkout, features, quantifiers):
    env = dict(os.environ, PYTHONPATH=str(checkout), PYTHONHASHSEED="0")
    return run([sys.executable, str(ORACLE), "--features", features, "--quantifiers", quantifiers], lines, env)


def agree(a: str, b: str) -> bool:
    if a.startswith("ERR") and b.startswith("ERR"):
        return True
    return a == b


def render(res: str) -> str:
    if not res.startswith("OK\t"):
        return res
    cands = res[3:].split("\x1d")
    return " || ".join(" ".join(e.split("\x1e")[0] for e in c.split("\x1f")) for c in cands)


def compare(name, lines, a, b, limit=40):
    diffs = [(l, x, y) for l, x, y in zip(lines, a, b, strict=True) if not agree(x, y)]
    kinds = Counter(
        "one side errors" if x.startswith("ERR") != y.startswith("ERR")
        else "same graphemes, different features" if render(x) == render(y)
        else "different graphemes"
        for _, x, y in diffs
    )
    return {
        "comparison": name,
        "cases": len(lines),
        "disagreements": len(diffs),
        "kinds": dict(kinds),
        "examples": [
            {"case": l.replace("\t", " | "), "left": render(x), "right": render(y),
             "left_raw": x[:400], "right_raw": y[:400]}
            for l, x, y in diffs[:limit]
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", required=True)
    ap.add_argument("--oracle", required=True)
    ap.add_argument("--blindrec-cases")
    ap.add_argument("--random", type=int, default=200000)
    ap.add_argument("--seed", type=int, default=20261113)
    ap.add_argument("--out", default="parity-report.json")
    args = ap.parse_args()

    streams = {"catalogue": catalogue_cases(), "regression": regression_cases()}
    if args.blindrec_cases:
        streams["blindrec"] = Path(args.blindrec_cases).read_text(encoding="utf-8").splitlines()
    if args.random:
        streams["random"] = random_cases(args.random, args.seed)

    report = {"seed": args.seed, "streams": {}}
    for name, lines in streams.items():
        c = run([args.cli], lines)
        om = oracle(lines, args.oracle, "merkmal", "fixed")
        o1 = oracle(lines, args.oracle, "1x", "fixed")
        oq = oracle(lines, args.oracle, "1x", "1x")
        ops = Counter(l[0] for l in lines)
        report["streams"][name] = {
            "forward": ops["F"],
            "backward": ops["B"],
            "c_errors": sum(1 for x in c if x.startswith("ERR")),
            "engine": compare("C vs oracle(merkmal, fixed)", lines, c, om),
            "features": compare("oracle(merkmal) vs oracle(1x)", lines, om, o1, limit=200),
            "quantifiers": compare("oracle(1x, fixed) vs oracle(1x, 1x)", lines, o1, oq),
        }
        s = report["streams"][name]
        print(f"{name:10s} cases={len(lines):7d}  engine={s['engine']['disagreements']} {s['engine']['kinds']}  "
              f"features={s['features']['disagreements']} {s['features']['kinds']}  quantifiers={s['quantifiers']['disagreements']}  "
              f"c_errors={s['c_errors']}", flush=True)
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
