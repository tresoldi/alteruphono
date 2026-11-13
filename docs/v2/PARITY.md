# Parity of alteruphono 2.0 with 1.x

This file records what the parity checks found, as they were run. Method: [`tests/parity/README.md`](../../tests/parity/README.md). Design: [DESIGN.md §8](DESIGN.md).

## M1: the C engine (2026-11-13)

**Reference.** Python 1.x at tag `v1.0.0rc1-simultaneous` (`b466d90`), with `3fdb52b` applied (D2). merkmal is branch `claude/alteruphono-support` (`af81477`), system `descriptive`. The harness seed is 20261113, and 7 for the sanity rerun.

### Engine: the C port of the engine against the Python reference

The Python reference here runs with merkmal's features and the fixed quantifier semantics: `--features merkmal --quantifiers fixed`.

| stream | cases | forward | backward | disagreements |
|---|---|---|---|---|
| catalogue: every `sound_changes.tsv` rule, TEST_ANTE forward and TEST_POST backward | 1,602 | 801 | 801 | **0** |
| regression: simultaneous application (tresoldi/alteruphono#1, blindrec's test) | 5 | 5 | 0 | **0** |
| blindrec: gate G1's rule stream (2,000 rules × 25 words, seed 800) | 50,000 | 50,000 | 0 | **0** |
| random: grammar over the whole notation, on catalogue words | 200,000 | 160,000 | 40,000 | **0** |

In the random stream, 3,057 cases are errors on both sides: unparseable rules, set mismatches, out-of-range back-references, and the backward cap. They count as agreements. They are not hidden: the C side's error count is in the report.

The C catalogue test (`tests/c/test_catalogue.c`) also checks all 801 test pairs directly: **801 of 801**.

### Features: what moving to merkmal changes (D1)

These are the differences between 1.x's own feature table and merkmal's labels, projected onto 1.x's vocabulary with the rules of DESIGN §4.1.

**By grapheme.** Over the 7,356 graphemes of 1.x's `sounds.tsv`:
- merkmal resolves 7,353 of them;
- for **7,342**, the projected labels equal 1.x's;
- the other 11 differ:

| grapheme(s) | 1.x | merkmal (projected) | reason |
|---|---|---|---|
| `ê̞ː ê̞ˑ ô̞ ô̞ː ô̞ˑ ø̞̂ ø̞̂ˑ ɤ̞̟̃` (8) | `mid` | `close-mid`, `lowered` | different description of lowered close-mid vowels |
| `ʈʂː` | `voiced` | `voiceless` | a 1.x data error |
| `ǃǃ` | `click consonant retroflex voiceless` | `consonant` only | merkmal reads the doubled grapheme as a two-click cluster; its per-click labels (`n1-…`, `n2-…`) are outside 1.x's vocabulary |
| `ⁿgǃ` | `nasal-click` | `click` | different click description |
| `k` + U+F268, `k` + U+F268 + `ʼ`, `oz̻` | (1.x labels) | not resolved | a private-use code point; a cluster; 1.x's behaviour for an unknown grapheme applies (no features) |

**By case.**
- catalogue: **0** differences;
- blindrec stream: **0** differences;
- random stream: 789 of 200,000.
  - 785 change only the features carried by some output element.
  - 4 change graphemes, because `ʈʂː` no longer matches the class `CV` (voiced consonant).

  Every one of the 789 involves `ʈʂː` or `ǃǃ`, which the random grammar draws on purpose.

**A mistake of mine, caught by this comparison.** The first projection rule dropped merkmal's `labial` everywhere. That also removed the only place label of the 42 bilabial clicks (`ʘ`, `gʘ`, `ŋʘ`, …), for which 1.x uses `labial` as the place. It showed up as feature-only differences on `ʘ`. The rule now drops `labial` only when a finer place label is present (DESIGN §4.1).

### Quantifiers: what fixing Q1/Q2 changes (D2)

There are 3,066 differences in the random stream, every one on a rule with a top-level `+` or `?`. None of the 801 catalogue rules, and none in blindrec's stream, has a quantifier. The fixed semantics are implemented twice, independently (C, and `oracle.py`), and the two agree on every case.

### Not yet covered (M2)

- the 233 upstream Python tests, which need the Python bindings;
- blindrec's pipeline outputs on the development tracks.

### A weakness of 1.x, reproduced rather than fixed

`backward` undoes `@1[+voiced]` by applying `-voiced`, which removes voicing without adding voicelessness. The "undone" `d` keeps its grapheme and is deduplicated away. So `S > @1[+voiced] / V _ V` does not reconstruct `*t` from `d`; with `@1[-voiced,+voiceless]` written out, it does. 2.0 reproduces this, because a fix would change results (`tests/c/test_backward.c`). Should it be fixed? That is a question for Tiago.

## Speed, C level (M1)

Machine: this session's container. Both engines run on the same stream: 801 catalogue rules, and 200,000 C / 20,000 Python seeded pairs of (rule, catalogue word), mean 8.9 segments. Caches are warm on both sides. Scripts: `bench/bench_engine.c` and `bench/bench_python.py`. Three C runs and two Python runs:

| operation | Python 1.x (µs) | C (µs) | ratio | target (DESIGN §9) |
|---|---|---|---|---|
| forward | 25.0–27.0 | 0.14–0.19 | about 130–190× | ≥ 100×: **met** |
| backward | 31–37 | 0.98–1.3 | about 25–35× | ≥ 20×: met |
| parse a sequence | 12–19 | 0.9–1.3 | about 10–20× | (none) |
| parse a rule | 12–18 | 1.3–1.8 | about 8–13× | ≥ 20×: **not met** |

DESIGN §9's parse target was set against a cold-cache figure (68.9 µs) that I measured carelessly. Against the cold figure, the C parser is about 40× faster; against warm 1.x, which is the fair comparison, it is about 10×. Rule parsing is not on any hot path in blindrec. The Python-API numbers come in M2.
