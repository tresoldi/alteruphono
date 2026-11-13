# Parity harness: the C engine against alteruphono 1.x

Results are recorded in [`docs/v2/PARITY.md`](../../docs/v2/PARITY.md).

## The oracle

The reference is Python 1.x at tag `v1.0.0rc1-simultaneous` (= `b466d90`), with the two fixes of tresoldi/alteruphono `3fdb52b` applied: `backward` keeps every alternative, and a choice in the output is a parse error (DESIGN D2). Set it up outside the repository:

```bash
git worktree add --detach /tmp/oracle1x v1.0.0rc1-simultaneous
```

```bash
git -C /tmp/oracle1x cherry-pick -n 3fdb52b
```

`oracle.py` runs on that checkout. It has two switches:
- `--features merkmal` replaces 1.x's feature table with the `alteruphono-1` projection of merkmal. That projection is written there independently of the C code (DESIGN 4.1).
- `--quantifiers fixed` replaces 1.x's quantified-rule branch of `forward` with the simultaneous semantics of DESIGN 5, again written independently (bugs Q1, Q2).

The oracle caps `backward` products at 100,000 candidates, as the C engine does by default. 1.x has no cap.

## Running

```bash
cmake -S . -B build/parity -DCMAKE_BUILD_TYPE=Release -DAP_BUILD_TESTS=OFF
```

```bash
cmake --build build/parity --target alteruphono-cli
```

```bash
python tests/parity/run_parity.py --cli build/parity/alteruphono-cli --oracle /tmp/oracle1x --random 200000 --blindrec-cases cases.tsv --out parity-report.json
```

`cases.tsv` is blindrec's own rule stream, the 50,000 applications of its gate G1. It is written by `make_blindrec_cases.py`, run from blindrec's directory. That needs Index Diachronica (CC BY-NC-SA, fetched by blindrec's `scripts/fetch_data.sh`, never committed), NorthEuraLex's `parameters.csv` and two Concepticon lists.

## The three comparisons

| comparison | meaning | required |
|---|---|---|
| engine: C vs oracle(merkmal, fixed) | the C port of the 1.x engine | 0 disagreements |
| features: oracle(merkmal, fixed) vs oracle(1x, fixed) | what moving to merkmal's features changes | every case listed and explained |
| quantifiers: oracle(1x, fixed) vs oracle(1x, 1x) | what fixing Q1/Q2 changes | only rules with top-level `+`/`?` |

Two results agree when both are OK with identical output (graphemes, sorted features, and the partial flag of every element), or when both are errors of any kind.

merkmal must be the branch `claude/alteruphono-support` (it adds `mk_system_inventory` and `mk_unicode_normalize`), checked out next to this repository.
