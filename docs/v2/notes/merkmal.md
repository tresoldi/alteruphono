# Design note: merkmal changes proposed for alteruphono 2.0

Read against merkmal master `60d1897` (0.9.0) and the branch
`claude/abstract-segments` (`2b4cf24`). Nothing here has been implemented.
Items marked *small* are candidates for a branch in merkmal with tests; the
rest are proposals for Tiago.

## What alteruphono needs and merkmal already has

- `mk_system_grapheme_features`: privative labels per grapheme. Measured: `descriptive` resolves 7,353 of the 7,356 graphemes in alteruphono 1.x's `sounds.tsv`. For 6,359 of them, the labels equal alteruphono's once merkmal's are intersected with alteruphono's vocabulary. The remaining differences are listed in [DESIGN.md §4.1](../DESIGN.md).
- `mk_system_feature_vector`: the numeric encoding used for the change model's displacement terms.
- `mk_system_semantic_fingerprint`: recorded in every alteruphono context and model pack.
- `mk_normalize_grapheme`: the boundary normalisation.

## Proposed changes

1. **List a system's inventory** (*small*). alteruphono must render a feature set back to a grapheme by exact lookup. merkmal says, correctly, that its compatible-grapheme ranking is display-only. An exact lookup needs the list of graphemes the system knows, and master has no call that returns it.

   Proposal: `mk_status mk_system_inventory(const mk_system *sys, mk_string_list **out)`. It would return the compiled inventory in its fixed (UTF-8 byte) order, plus the graphemes of runtime models. It would not include graphemes the resolver synthesizes from diacritics, because those are unbounded.

   Tests: count and order per built-in system, and that every entry resolves. ABI: an addition only.

2. **Bring the `mk_bundle` API and `AbstractSegment` to master** (*large*, Tiago's call). On `claude/abstract-segments` the bundle API is an orphan commit cut from an older tree. Merging it would revert master's compiled-in Unicode normalisation, the `cc-by` data profile and `wheels.yml`. It has to be **ported** onto master (`src/bundle.c`, `tests/c/test_bundle.c`, `MK_ERR_UNKNOWN_FEATURE` appended, the header block, the Python `AbstractSegment`), not merged.

   alteruphono's abstract segments (DESIGN §4.5) wait for this. Points to settle in the port:
   - `AbstractSegment.covering` exists only in Python. A C `mk_bundle_covering(sys, graphemes, n, out)` would let historia build covering bundles without Python. Its empty-cell result, when no value applies, should become an explicit error or `0`, not an empty string.
   - The branch makes the numeric feature vector lossless (`Node=label` one-hot, `NaN` for `?`). That is a breaking change to `mk_system_feature_vector`. It needs a version bump and a note, or a new function with the old one kept.
   - Bundles are reparsed from text on every Python call. That is acceptable for merkmal's own use, but alteruphono will hold its own `mk_bundle *` per interned segment, so the C API is what matters.

3. **Version macros in the header** (*small*). merkmal exposes no `MK_VERSION_*` or ABI integer; there is only the CMake SOVERSION. alteruphono, like regulae, records merkmal's version for provenance, and today it has to lift it from CMake.

   Proposal: `MK_VERSION_MAJOR/MINOR/PATCH/STRING`, `MK_ABI_VERSION`, and `mk_version_string()` / `mk_abi_version()` in regulae's style. Tests: the header and runtime values agree.

4. **Document thread safety** (*small*, docs only). The survey found no mutable file-scope statics in `src/`, and `mk_registry_add_model_*` does not invalidate system pointers. A sentence in `docs/c-api.md` would turn this into a contract. The sentence would say that concurrent reads of one `mk_system` are safe, and that adding a model must not overlap other use of the registry. alteruphono's own guarantee (one thread per context, immutable models shared) depends on it.

5. **`mk_sound_distance` ignores unknown labels on master** (already fixed on the branch, `MK_ERR_UNKNOWN_FEATURE`). This should be ported with item 2. alteruphono will not call `mk_sound_distance` on label sets it builds itself, so this does not block anything.

## What alteruphono will not ask of merkmal

- **Sound classes.** The constitution (§6.4) puts classes in versioned packs relative to an inventory, so they stay in alteruphono's class pack.
- **Caching.** alteruphono interns segments itself, once per grapheme per context.
- **A probability of change.** merkmal's README is explicit that its dissimilarity is not one. The change model is a separate object in alteruphono.
