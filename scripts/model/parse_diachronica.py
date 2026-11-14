"""Index Diachronica rules with their top-level family section.

blindrec's changegen.parse_tex, replayed line by line with one addition: the
current `\\section{...}` (the family chapter) is recorded with each rule, so
that leave-out can be done by family (TRAINING_SPLIT.md 4). Run from
blindrec's directory (it uses blindrec's vendored alteruphono 1.x to decide
which segments are recognised, as changegen does):

    cd prototypes/blind-reconstruction
    python <alteruphono>/scripts/model/parse_diachronica.py <out.json>

The output is derived from Index Diachronica (CC BY-NC-SA): write it under
alteruphono's git-ignored data/ and never commit it.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from blindrec import changegen as cg  # noqa: E402

SECTION = re.compile(r"\\section\*?\{")


def main(out: str) -> None:
    section, src = "", ""
    rules, seen = [], set()
    for line in open(cg.TEX, encoding="utf-8"):
        s = line.strip()
        if SECTION.match(s):
            title, _ = cg._group(s, s.index("{"))
            section = re.sub(r"\s+", " ", cg.tex_to_text(title).replace(cg.IPA_ON, "").replace(cg.IPA_OFF, "")).strip()
        m = cg.HEADING.match(s)
        if m:
            title, _ = cg._group(s, m.end() - 1)
            src = re.sub(r"\s+", " ", cg.tex_to_text(title).replace(cg.IPA_ON, "").replace(cg.IPA_OFF, "")).strip()
            continue
        if ("\\change" not in line and "\\textrightarrow" not in line) or "\\newcommand" in line:
            continue
        for r in cg.parse_line(line, src):
            key = (r["src"], r["inputs"][0], r["outputs"][0], r["left"], r["right"])
            if key in seen:
                continue
            seen.add(key)
            if cg._recognised(r):
                r["section"] = section
                r["rule"] = cg.rule_string(r)
                rules.append(r)
    Path(out).write_text(json.dumps({"rules": rules}, ensure_ascii=False), encoding="utf-8")
    from collections import Counter

    print(len(rules), "rules;", Counter(r["section"] for r in rules).most_common(40))


if __name__ == "__main__":
    main(sys.argv[1])
