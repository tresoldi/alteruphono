# Design note: regulae and alteruphono 2.0

Read against regulae master (ABI 46). alteruphono 2.0 takes regulae as its house style: CMake layout, `rg_`-style ABI conventions, caller-owned diagnoses, sanitizer and fuzz builds, `scripts/check.sh`, clang-tidy at zero findings. Nothing here has been implemented in regulae.

## Where alteruphono deliberately differs

- **Python boundary.** regulae's extension speaks JSON in and JSON out, so that ABI bumps never reach Python. That suits one training call per corpus. alteruphono's `forward` is called per word, hundreds of thousands of times in blindrec's simulators. A JSON crossing per call would cost more than the 1.x Python engine it replaces.

  The alteruphono extension therefore wraps handles (context, rule, model) as Python objects and passes integer id arrays. It uses JSON only for the rule's token tree and for model packs.

## How the change model could use regulae

regulae's correspondence output (`surface_relationship_model` JSON, `format_version` 2) has two things the change model's training needs:
- aligned proto→daughter segment pairs, when one "lect" is the proto-language;
- environments, as one slot per axis with `{feature, value}` predicates.

Using regulae as the aligner for training pairs (DESIGN §6.6, point 3) avoids a home-made aligner whose phonetic-distance costs would bias the model toward small changes.

This is consistent with regulae's scope. regulae describes correspondences and asserts no direction, so pairs it aligns are still bidirectional relations. alteruphono's model then adds direction, as a prior (`06_asymmetry.md`: "correspondences are bidirectional relations; the priors used to evaluate them may be directional").

## Proposed changes to regulae

1. **Export per-opportunity alignment rows** (*small to medium*). For training, alteruphono needs every aligned position, unchanged ones included, with its environment. That is exposure: the denominator a catalogue cannot give. regulae's model aggregates counts.

   Proposal: an export (C and JSON) of the aligned rows of one lect pair. Each row would be (cognate id, position, source segment, target segment or gap, left and right source neighbours). The aggregation already sees these rows, so this exposes an intermediate rather than adding analysis.

   Tests: the row counts sum to the existing pair counts on `testdata/` corpora. ABI: an addition.

2. **Install a CMake package config** (*small*). regulae consumes merkmal with `find_package(... CONFIG)`, but it installs no `regulaeConfig.cmake` of its own. historia, and alteruphono if it links regulae for training, would want `find_package(regulae CONFIG)`.

   Proposal: `install(EXPORT)` plus a config file, mirroring merkmal's `cmake/merkmal-config.cmake.in`. Tests: a ctest that configures a tiny consumer against the install tree.

3. **A note on the merkmal version floor** (docs). regulae asks for `find_package(merkmal 1.0 CONFIG)`, while merkmal master is 0.9.0, so installed merkmal is never picked up and the `add_subdirectory` fallback is always used. This is probably intended, but it is worth one line in the README, or the floor should be lowered.

No change to regulae's scope is proposed. Direction, sound laws and proto-forms stay out of it, as its README and the constitution's proposal shelf (§4.1) require.
