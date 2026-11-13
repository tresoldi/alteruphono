"""Write blindrec's own rule stream as parity cases.

This is the stream of blindrec's gate G1 (`scripts/check_soundengine.py`,
PREREG "Simulator v5: plan"): rules from `changegen.sample_mixture` (Index
Diachronica plus alteruphono's catalogue), each applied to 25 words of a
simulated proto-lexicon (`synth4.Simulator4(Params4(seed))`). The same random
calls are made in the same order, so with the defaults the cases are exactly
the 50,000 applications of that gate.

Run from blindrec's directory, with Index Diachronica fetched locally
(`scripts/fetch_data.sh`; CC BY-NC-SA, never committed):

    cd prototypes/blind-reconstruction
    python <alteruphono>/tests/parity/make_blindrec_cases.py 2000 800 > cases.tsv
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from blindrec import config  # noqa: E402,F401  (vendored alteruphono first)
from alteruphono.resources import load_sound_changes  # noqa: E402
from blindrec import changegen, soundengine, synth4  # noqa: E402


def main(n_rules: int = 2000, seed: int = 800) -> None:
    sim = synth4.Simulator4(synth4.Params4(seed=seed))
    lang = sim.proto("CHECK", paradigms=False)
    words = [w.segs for w in lang.words()]
    cons, vows = sim.current_inventory(lang)
    rules = changegen.load_rules()
    model = changegen.ChangeModel().fit(rules)
    exclude = {" ".join(r["RULE"].split()) for r in load_sound_changes()}
    rng = random.Random(seed)
    out = sys.stdout
    for _ in range(n_rules):
        rule, _ = changegen.sample_mixture(rng, cons, vows, 0.5, model=model, rules=rules, exclude=exclude)
        try:
            soundengine.parse(rule)
        except soundengine.RuleError:
            continue  # the gate skips these too, before sampling words
        for segs in rng.sample(words, 25):
            out.write(f"F\t{rule}\t# {' '.join(segs)} #\n")


if __name__ == "__main__":
    main(*map(int, sys.argv[1:]))
