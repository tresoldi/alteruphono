# Design note: yvyra and alteruphono 2.0

yvyra (a MrBayes fork for discrete linguistic characters) already supports asymmetric rate matrices and directional cost templates per character ("loss, lenition, grammaticalization", 23 built-in templates). blindrec's v8 reconstructs on yvyra's dated tree. Nothing here has been implemented.

## Where the change model could meet yvyra

The templates are stipulated. A "lenition" template says that one direction is cheaper, but not by how much, or in which environment. alteruphono's change model produces exactly that number, with an interval and a provenance: relative directional rates per (source, reflex, environment).

A sound-correspondence character (one column, states = proto-segments or reflexes) could take its rate matrix, or a prior on it, from a model pack instead of a template.

## Proposals (all for Tiago; none is small)

1. **Rate-matrix prior from a file.**
   - yvyra would accept, per character or per character class, a fixed relative rate matrix, or a Dirichlet or log-normal prior centred on one, read from YAML.
   - alteruphono would write that YAML from a pack (`ap_model_rates` over the column's states and environment).
   - The coupling is a file, not linking: yvyra stays free of alteruphono.
2. **Uncertainty.**
   - The prior's spread should come from the pack's posterior intervals, not be fixed at a narrow value.
   - Otherwise the tree inherits false confidence from a point estimate. The constitution's §1.3: "False confidence is worse than `unidentified`".
3. **Ablation.**
   - Any yvyra run that uses a pack-derived prior must be rerun with the template or flat prior.
   - A topology or root that moves under that ablation is reported as `typo_dominated`.

## Caution

Cognate-class characters, which are what yvyra mostly analyses, are not sound-change characters. The change model says nothing about lexical replacement. Proposal 1 applies only to characters whose states are segments, and to my knowledge blindrec does not currently build such characters for yvyra. This note is a design option, not a request for work.
