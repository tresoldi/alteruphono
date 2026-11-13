"""Speed of an alteruphono Python API on the catalogue stream (as bench_engine.c).

    PYTHONPATH=<alteruphono checkout> python -I bench/bench_python.py <repo root> [pairs]

Run it against the 1.x oracle checkout for the baseline, and against 2.0 for
the bindings. Prints one JSON line.
"""

import csv
import json
import random
import sys
import time
from pathlib import Path

import alteruphono
from alteruphono import backward, forward, parse_rule, parse_sequence


def main(root: str, pairs: int = 20000) -> None:
    with (Path(root) / "resources" / "sound_changes.tsv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    texts = [r["RULE"] for r in rows]
    wtexts = ["# " + r["TEST_ANTE"] + " #" for r in rows]
    for t in texts:  # warm caches, as the C benchmark does
        parse_rule(t)
    t0 = time.perf_counter()
    rules = [parse_rule(t) for t in texts]
    t_parse = (time.perf_counter() - t0) / len(rules)
    t0 = time.perf_counter()
    words = [parse_sequence(w) for w in wtexts]
    t_seq = (time.perf_counter() - t0) / len(words)
    rng = random.Random(20261113)
    sample = [(rng.randrange(len(rules)), rng.randrange(len(words))) for _ in range(pairs)]
    for r, w in sample[:2000]:
        forward(words[w], rules[r])
    t0 = time.perf_counter()
    for r, w in sample:
        forward(words[w], rules[r])
    t_fwd = (time.perf_counter() - t0) / pairs
    nb = pairs // 10
    t0 = time.perf_counter()
    for r, w in sample[:nb]:
        backward(words[w], rules[r])
    t_bwd = (time.perf_counter() - t0) / nb
    print(json.dumps({
        "engine": f"python {alteruphono.__version__}", "rules": len(rules), "pairs": pairs,
        "mean_word_len": sum(len(words[w]) for _, w in sample) / pairs,
        "parse_rule_us": round(t_parse * 1e6, 3), "parse_sequence_us": round(t_seq * 1e6, 3),
        "forward_us": round(t_fwd * 1e6, 4), "backward_us": round(t_bwd * 1e6, 3),
    }))


if __name__ == "__main__":
    main(sys.argv[1], *map(int, sys.argv[2:]))
