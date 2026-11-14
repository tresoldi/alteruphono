# alteruphono 2.0 — design (M0)

Status: **draft for approval** (2026-11-13). Nothing in this document has been
implemented. The numbers quoted as "measured" were measured on this branch's
starting point (`master` = `b466d90`) and on the repositories as checked out
on 2026-11-13; every other number is a target or an estimate and says so.

Per-library notes: [merkmal](notes/merkmal.md), [regulae](notes/regulae.md),
[yvyra](notes/yvyra.md), [blindrec](notes/blindrec.md),
[historia](notes/historia.md).

Decisions that are Tiago's are collected in §11. Until they are answered,
the default stated next to each one is what M1 would do.

---

## 1. Scope and what 2.0 is not

alteruphono 2.0 has three parts:

1. a **C99 rule engine** (parser, matcher, `forward`, `backward`) behind a stable C ABI, on merkmal;
2. **Python bindings** that keep the 1.x public API (`parse_rule`, `parse_sequence`, `forward`, `backward`, `resources.load_sound_changes`, `features.get_system` with the methods blindrec uses);
3. a **change model**: a directional, environment-conditioned, exposure-normalised probability of a reflex given a proto-segment, with the catalogue as a prior and fitted on real proto→daughter correspondences by empirical Bayes. It is exposed through scoring and sampling calls.

Rule application stays deterministic. The model never alters what `forward` returns. It is a separate object that scores and samples.

In the vocabulary of `framework/CONSTITUTION.md`, the fitted model is a **versioned `P_typo` pack** with provenance (§6.10). It is a prior, not evidence `D`, and nothing in alteruphono authors a direction or a proto-form. A consumer that lets the pack decide a reconstruction must be able to rerun with the pack ablated (`P_typo^(-family)`, catalogue-only, data-only; §6.6 below). A result that changes under that ablation is `typo_dominated`.

Not in 2.0:
- metathesis, and change payloads spanning more than one proto-segment in the model (the rule engine keeps multi-segment rules);
- a multi-step (CTMC) fit of the model (§6.3 explains the one-step approximation and how it is checked);
- the `comparative/` module (alignment, Fitch/Sankoff, NJ/UPGMA). blindrec does not use it. It stays in Python, unchanged, on top of the new bindings.

The `engine/` module (ordering, gradient) and `prosody.py` also stay in Python on top of the bindings. They are ported to C only if a consumer needs them.

## 2. What exists, measured

| item | value |
|---|---|
| upstream tests at `b466d90` | **233 pass** (the prompt's "219+"; 219 was the count when blindrec vendored `607b9f5`) |
| catalogue rules with test pairs | **801**; all 801 reproduce `TEST_ANTE → TEST_POST` when the test forms are wrapped in `# … #` (unwrapped: 571 of 801, because boundary rules need the `#`) |
| catalogue rules using quantifiers `+`/`?` | 0 |
| catalogue rules using `!` or `_.onset/_.nucleus/_.coda` | 2 |
| Python `forward`, catalogue rule × catalogue test word (mean 8.9 segments, 20,000 random pairs) | **25.9 µs / application** |
| Python `backward`, same stream (2,000 pairs) | 43.2 µs / application |
| Python `parse_rule` | 68.9 µs / rule |
| Python `parse_sequence` | 20.1 µs / word |
| merkmal grapheme lookup (merkmal `bench/baseline.txt`) | 0.1 µs; merkmal caches nothing |

**1.x bugs found while reading** (all outside the code paths of published results; see §8.3):
- **Q1.** Quantified rules apply in a separate branch of `forward` with different context handling. `p > b / V _ V?` on `# a p a p a #` changes nothing, though it should give `# a b a b a #`.
- **Q2.** `C? p > @1 b / V _` on `# a p a p a #` returns `# a p b a p b a #`, which duplicates segments.
- **Q3.** Two fixes on the unmerged branch `claude/backward-latents` (`3fdb52b`):
  - `backward` drops every alternative of a choice except the first;
  - a choice in the output (`p|t|k > b|d|g`) parses and then deletes every match.
- **Q4.** The `ipa` system gives `ʈʂː` the feature `voiced`. merkmal gives it `voiceless`, which is evidently right.

## 3. C API and ABI

### 3.1 Conventions (regulae house style)

- Prefixes: `ap_` for functions and types, `AP_` for macros and enum values. There is one public header, `include/alteruphono.h`, with `extern "C"` guards and an `AP_API` visibility macro (`-fvisibility=hidden`).
- C99, `CMAKE_C_EXTENSIONS OFF`. Warnings are set directory-wide after merkmal is added: `-Wall -Wextra -Wpedantic -Wconversion -Wshadow -Wstrict-prototypes -Wmissing-prototypes -Wcast-qual`.
- `AP_WERROR` is OFF for consumers and ON in `scripts/check.sh` and CI.
- `AP_ENABLE_SANITIZER` is `address` or `undefined`; UBSan builds use `-fno-sanitize-recover=all`.
- `AP_BUILD_FUZZERS` (clang libFuzzer) instruments alteruphono only, not merkmal.
- merkmal is found with `find_package(merkmal CONFIG)`, falling back to `add_subdirectory(${AP_MERKMAL_SOURCE_DIR})` (default `../merkmal`). The merkmal version is compiled in for provenance.
- `AP_VERSION_{MAJOR,MINOR,PATCH,STRING}` and a separate integer `AP_ABI_VERSION`, which moves on any change to an exported struct layout, enum, signature or ownership rule. Runtime getters: `ap_version_string()` and `ap_abi_version()`.
- All functions return `ap_status`; results come back through out-parameters. Status values are appended, never renumbered:
  ```
  AP_OK = 0, AP_ERR_INVALID_ARGUMENT, AP_ERR_OOM, AP_ERR_PARSE,
  AP_ERR_MERKMAL, AP_ERR_UNKNOWN_GRAPHEME, AP_ERR_UNKNOWN_FEATURE,
  AP_ERR_UNKNOWN_CLASS, AP_ERR_LIMIT, AP_ERR_BUFFER_TOO_SMALL,
  AP_ERR_MODEL_FORMAT, AP_ERR_INCOMPATIBLE
  ```
  `ap_status_string()` returns static text.
- Error detail lives in caller-owned diagnosis structs, never in a process-wide buffer (regulae moved off one at ABI 22 for thread safety):
  ```c
  typedef struct ap_diagnosis { ap_status status; size_t offset; size_t line; char message[256]; } ap_diagnosis;
  ```
  Every parser and loader takes an `ap_diagnosis *` (NULL allowed).
- Strings are NUL-terminated UTF-8, normalised to NFD at the boundary, as 1.x does.

### 3.2 Objects and ownership

| handle | what it owns | lifetime rule |
|---|---|---|
| `ap_context` | a borrowed `const mk_system *`, the segment table, the class pack and the label projection | the merkmal registry must outlive it |
| `ap_rule` | the compiled rule and its lazy modifier cache | the context must outlive it |
| `ap_ruleset` | an ordered array of rules (references, not copies) | the rules must outlive it |
| `ap_candidates` | the result of `backward` | freed by `ap_candidates_free` |
| `ap_model` | a loaded change-model pack (immutable after load) | the context must outlive it |
| `ap_rng` | a **transparent** struct (xoshiro256**) | caller-owned; seeded with `ap_rng_seed(&rng, uint64_t)` |

- An out-pointer belongs to the caller only on `AP_OK`.
- Accessors return borrowed pointers that stay valid while their owner lives.
- There is no global mutable state. The only file-scope data is `const` tables.

**Segments are interned integers.** `ap_seg` is `uint32_t`. Each context keeps a table of segments; a segment is a (grapheme, label bitset, optional merkmal bundle) triple, interned on first use. Two ids are reserved: `AP_SEG_BOUNDARY = 0` and `AP_SEG_DELETION = 1` (the latter is used only by the model). A sequence is a `const ap_seg *` plus a length.

Interning is what makes the engine fast: merkmal is consulted once per grapheme per context, and from then on every class test is a bitset operation. Interning is needed because merkmal caches nothing and a lookup with resolution costs up to three lookups.

**Mutability and threads.** C99 has no portable threads, and alteruphono takes no locks. The rule is:
- A context is used by **one thread at a time**.
- Operations that may intern a new segment take a non-const `ap_context *`: parsing a sequence or rule, and `forward` with a feature modifier, whose output can be a new (grapheme, features) pair, as in 1.x.
- `ap_context_clone()` gives an independent copy for another thread.
- `ap_rule` objects are shareable only between clones of the same context: ids agree between clones up to the clone point, and segments interned later are clone-local.
- An `ap_model` is immutable and shareable across contexts that have the same merkmal system fingerprint.

### 3.3 Calls (sketch; final signatures in M1)

```c
/* context */
ap_status ap_context_new(const mk_system *sys, const ap_context_options *opt,
                         ap_context **out, ap_diagnosis *diag);
void      ap_context_options_init_defaults(ap_context_options *opt);
ap_status ap_context_clone(const ap_context *ctx, ap_context **out);
void      ap_context_free(ap_context *ctx);
/* ap_context_options: projection ("alteruphono-1" | "native"), class pack text
   (NULL = built-in 1.x pack, §4.2), rendering universe (NULL = built-in 1.x
   grapheme list, §4.3), limits (max sequence length, max backward candidates). */

/* segments */
ap_status ap_intern(ap_context *ctx, const char *grapheme, ap_seg *out);
ap_status ap_intern_abstract(ap_context *ctx, const char *name,
                             const char *bundle_text, ap_seg *out, ap_diagnosis *diag);
ap_status ap_seg_grapheme(const ap_context *ctx, ap_seg s, const char **out);   /* borrowed */
ap_status ap_seg_test(const ap_context *ctx, ap_seg s, const char *label, ap_truth *out);
ap_status ap_seg_labels(const ap_context *ctx, ap_seg s, char ***labels, size_t *n); /* ap_strings_free */
typedef enum { AP_FALSE = 0, AP_TRUE = 1, AP_UNKNOWN = 2, AP_INAPPLICABLE = 3 } ap_truth;

/* sequences: caller buffers; AP_ERR_BUFFER_TOO_SMALL reports the needed length */
ap_status ap_parse_sequence(ap_context *ctx, const char *text,
                            ap_seg *buf, size_t cap, size_t *len, ap_diagnosis *diag);
ap_status ap_render_sequence(const ap_context *ctx, const ap_seg *seq, size_t n, char **out);

/* rules */
ap_status ap_rule_parse(ap_context *ctx, const char *text, ap_rule **out, ap_diagnosis *diag);
ap_status ap_rule_to_json(const ap_context *ctx, const ap_rule *r, char **out); /* token tree, for Python */
void      ap_rule_free(ap_rule *r);

/* application */
ap_status ap_forward(ap_context *ctx, const ap_rule *r, const ap_seg *in, size_t n,
                     ap_seg *out, size_t cap, size_t *written);
ap_status ap_forward_ruleset(ap_context *ctx, const ap_ruleset *rs, const ap_seg *in, size_t n,
                             ap_seg *out, size_t cap, size_t *written, ap_trace *trace /*NULL ok*/);
ap_status ap_forward_lexicon(ap_context *ctx, const ap_ruleset *rs,
                             const ap_seg *in, const size_t *offsets, size_t nwords,
                             ap_seg **out, size_t **out_offsets);   /* batch; ap_free */
ap_status ap_backward(ap_context *ctx, const ap_rule *r, const ap_seg *in, size_t n,
                      ap_candidates **out);
size_t    ap_candidates_count(const ap_candidates *c);
ap_status ap_candidates_get(const ap_candidates *c, size_t i, const ap_seg **seq, size_t *n);
void      ap_candidates_free(ap_candidates *c);
```

The model calls are in §6.7.

Every sequence call has a batch form (`*_lexicon`). Over a lexicon, the Python crossing and the allocation are then paid once, not once per word; this is what the speed target in §9 depends on.

### 3.4 Python bindings

The bindings follow regulae: a hand-written CPython extension `alteruphono._native` (abi3, `Py_LIMITED_API 0x030C0000`, Python ≥ 3.12). `setup.py` compiles alteruphono's and merkmal's C sources into it, so no shared library is located at run time.

The two libraries differ in one respect. regulae's boundary is JSON in and JSON out. That suits one training call per corpus, but it would erase the gain on a per-word `forward`. The alteruphono extension therefore exposes the context and rule as Python objects that wrap the handles, and passes sequences as integer id arrays. JSON is used only for the rule's token tree (`ap_rule_to_json`), so that `Rule.ante` and `Rule.post` keep their 1.x token dataclasses.

Python API compatibility:
- `Sound`, `Boundary`, every token class, `Rule` and `MatchResult` stay frozen dataclasses with the same fields, equality and `str()`.
- A `Sound` is interned per (grapheme, features): the binding keeps an id → `Sound` list and stores the id in a private attribute set with `object.__setattr__`. That attribute is not a dataclass field, so equality and hashing are unchanged. Rebuilding the output tuple is then a list lookup.
- `forward(sequence, rule, system_name=None)` returns a tuple of `Sound`/`Boundary`, as before.
- `backward` returns a sorted, deduplicated list, as before.
- `features.get_system(name=None)` returns an object with `grapheme_to_features`, `features_to_grapheme`, `add_features`, `partial_match`, `class_features`, `is_class`, `sound_distance` and `feature_distance`. `features.ipa.FEATURE_CATEGORIES` stays as a dict. `name`s map to merkmal systems (§4.1).
- `resources.load_sound_changes()` returns the same rows. `sound_changes.tsv` is kept: it is a catalogue of rules with test pairs, not a feature table.

**What does not survive.** The `tresoldi` and `distinctive` feature systems of 1.x are alteruphono's own tables, and decision 2 drops them. `get_system("tresoldi")` and `get_system("distinctive")` will raise a `KeyError` that names merkmal's systems. blindrec calls only `get_system()`. The upstream tests that exercise those systems (`test_features.py` and `test_geometry.py` in part) are listed as intended breaks in §8.3. `sound_distance` is a separate problem (§4.4, D3).

## 4. Rule notation on merkmal features

### 4.1 Labels and the projection

merkmal's categorical systems describe a segment as a set of **privative labels**: `voiceless` is a label, `-voice` is not. alteruphono 1.x does the same with its own vocabulary of about 125 labels, grouped into categories (`FEATURE_CATEGORIES`: place, manner, phonation, height, …).

**Measured**, over the 7,356 graphemes of `sounds.tsv`:
- merkmal `descriptive` (and `distinctive`, which has the same labels for these graphemes) resolves 7,353 of them;
- for 7,219, alteruphono's labels are a subset of merkmal's;
- for 6,359, they are identical once merkmal's labels are intersected with alteruphono's vocabulary.

The differences fall into a few classes, and the parity plan in §8 is built on this table:

| class | graphemes | cause | proposed handling in projection `alteruphono-1` |
|---|---|---|---|
| merkmal adds `labial` to labials (`b p f v m w ɸ β ʋ …`) | 860 | merkmal has a hierarchical major-place label; in 1.x `labial` is a place value and replaces `bilabial` under `add_features` | drop `labial` when a finer place label (`bilabial`, `labio-dental`, …) is present; keep it when it is the only place (`ʘ`: see §12) |
| tone: 1.x `with_falling_tone` etc., merkmal `tone-onset-*`/`tone-present` | 131 | different tone encodings | map merkmal's tone labels to the 1.x names in the projection; list any graphemes that do not map |
| `mid` vs `close-mid lowered` (`ê̞ ô̞ ɤ̞̟̃ …`) | 8 | different description of lowered close-mid vowels | accept merkmal; list as diffs |
| `ʈʂː` `voiced` (1.x) vs `voiceless` | 1 | 1.x data error (Q4) | accept merkmal |
| `ǃǃ`, `ⁿgǃ` | 2 | different click descriptions | accept merkmal; list |
| unresolved by merkmal (`k`+private-use char, `oz̻`) | 3 | private-use codepoint; a cluster | unknown grapheme, as 1.x does with unknown graphemes (empty features) |

Twelve graphemes used in catalogue test pairs belong to the `labial` class. That is why the projection matters: without it, `features_to_grapheme` (exact set lookup) would fail for every labial produced by a modifier.

There are two projections:
- **`alteruphono-1`** (the default in 2.0.x): merkmal labels ∩ the 1.x vocabulary, with the adjustments above. It exists to make parity measurable and to keep blindrec's outputs comparable. Its label names are the 1.x names; its values come from merkmal.
- **`native`**: every merkmal label of the chosen system, with categories taken from merkmal's geometry nodes. It is the default from 2.1, if Tiago agrees.

`system_name` maps as follows:
- `"ipa"` (the 1.x default) → merkmal `descriptive` with `alteruphono-1`;
- `"descriptive"`, `"distinctive"`, `"phoible"`, `"pbase-*"` → that merkmal system with `native`.

Every result records the merkmal system's semantic fingerprint (`mk_system_semantic_fingerprint`), as the constitution's §6.10 asks ("Runs label `feature_system`…").

### 4.2 Sound classes

merkmal has no sound-class API. The constitution forbids "anonymous universal natural classes" (§6.4): classes are relative to an inventory and are proposals.

In 2.0 a class is therefore a **named entry in a versioned class pack**: a conjunction of label tests, positive and negative. The built-in pack `alteruphono-1-classes` is the `FEATURES` column of `classes.tsv`:
- `A F H K L N P Q R S SV SVL V VN VL B E C CV`;
- `R = consonant,-stop`;
- the development entry `XXX` is dropped.

The pack is text, so a consumer can load another. `classes.tsv`'s `GRAPHEMES` column is not used: class membership is computed from labels, as 1.x already does (`build_class_table` reads only `FEATURES`).

A class test on a segment is a bitset test: `(labels & pos) == pos && (labels & neg) == 0`.

**Name collision.** The class `H` means "glottal consonant" in this pack. A posited laryngeal written `H` would therefore be read as the class. Abstract segments are written with a sigil (§4.5) so that no collision can arise.

### 4.3 Modifiers and rendering

`@1[+voiced,-voiceless]` applies additions with the category-replacement rule of 1.x (`add_features`), then removes subtractions. In the `alteruphono-1` projection the categories are 1.x's; in `native` they are merkmal's geometry nodes.

Rendering a feature set back to a grapheme (`features_to_grapheme`) needs a **rendering universe**: a list of graphemes whose projected labels are known. merkmal has no exact bundle-to-grapheme function. Its `mk_bundle_compatible_graphemes` is for display only, and its ranking "never decides identity". alteruphono must therefore do its own exact reverse lookup, and the universe has to come from somewhere:
- **`alteruphono-1`:** the grapheme column of `sounds.tsv`, in file order. 1.x takes the first match in that order, and parity needs the same order. Only the graphemes are used; the `NAME` column, which is 1.x's feature table, is dropped.
- **`native`:** merkmal's own inventory. This needs a small merkmal call that lists it ([merkmal note](notes/merkmal.md), item 1).

When no grapheme renders a feature set, 1.x keeps the old grapheme with the new features (`new_grapheme or elem.grapheme`). 2.0 keeps that behaviour, but counts each such event in an `ap_trace` so that it is visible. It is a silent failure in 1.x.

### 4.4 Distances

blindrec's `phon.distance` calls `get_system().sound_distance`, which is the 1.x feature-geometry distance over 1.x labels. blindrec rounds it to 9 decimals because the sum depends on set-iteration order. This distance sets stage-5 substitution costs (`Costs`, `0.5 + 1.5·d`), so replacing it with merkmal's dissimilarity would change every reconstruction.

Proposal (**D3**):
- 2.0 ports the 1.x geometry distance to C as `ap_legacy_geometry_distance`. It is computed over the `alteruphono-1` projection, its summation order is fixed, so it no longer depends on iteration order, and it is clearly marked as a compatibility function.
- `get_system("ipa").sound_distance` keeps returning it.
- Moving blindrec to merkmal's dissimilarity is a separate blindrec decision with its own PREREG entry, not a side-effect of this port.

Either way, merkmal's warning stands: neither function is a metric, and neither is a probability of change (merkmal README: frequent `k>tʃ` scores further apart than rare `k>q`). The change model in §6 exists because a distance cannot answer that question.

### 4.5 Abstract segments

A posited segment, such as a laryngeal that no daughter keeps, is a merkmal bundle with no grapheme as its identity (`framework/08_latent_elements.md`; `interchange.md` §3.7).

- **Notation.** In rules and sequences an abstract segment is written `*Name`, for example `*H > :null: / _ C`. It must be declared beforehand in the context:
  ```
  ap_intern_abstract(ctx, "H", "voice=?;guttural_place=?;…", &id)
  ```
  or, from Python, `context.declare("H", AbstractSegment(...))`. An undeclared `*Name` is a parse error. The `*` sigil keeps abstract segments apart from class names and graphemes; in the 1.x grammar `*` begins no token.
- **Identity.** Identity is the (system fingerprint, canonical bundle text) pair, never the name: the name is a display label. Two declarations with the same bundle are the same segment.
- **Feature tests are three-valued.** A cell may be `+`, `-`, `0` (inapplicable), `?` (unknown but applicable) or `*` (unknown, may be inapplicable). `ap_seg_test` returns `AP_TRUE`, `AP_FALSE`, `AP_UNKNOWN` or `AP_INAPPLICABLE`, and merkmal's distinction between `0` and `?` is kept all the way through. Rule matching has to turn this into yes or no. The policy is fixed, explicit, and recorded in the trace:
  - **`forward` is strict.** A class or feature test matches only on `AP_TRUE`. An abstract segment does not undergo a change it might or might not undergo; that would be inventing evidence.
  - **`backward` is permissive.** `AP_UNKNOWN` counts as a match, so every history the segment could have had is proposed. Candidates are proposals `q(·)` and are labelled so.
  - A test on an `AP_INAPPLICABLE` cell is false in both directions.
- **Modifiers on an abstract segment** set cells (`mk_bundle_set`). The result is a new abstract segment, interned by bundle. It is rendered as `*Name′` with a numbered suffix, or as its compatible graphemes when the caller asks for display.

**Dependency.** merkmal's `mk_bundle` API and `AbstractSegment` exist only on merkmal's branch `claude/abstract-segments`. That branch is an orphan commit cut from an older tree than master; it shares no history with master and lacks master's compiled-in Unicode normalisation and data profiles. Abstract segments in alteruphono therefore wait until the bundle API is on merkmal master ([merkmal note](notes/merkmal.md), item 2; a large change and Tiago's call).

Until then, M1 builds without abstract segments, behind `AP_HAVE_BUNDLES`. Parity does not need them, because 1.x has none.

## 5. Engine semantics (what M1 must reproduce)

- **Rule normal form** (1.x `parse_rule`). `ante = left ++ focus ++ right` and `post = backrefs(left) ++ post ++ backrefs(right)`, with `left_len`/`right_len`; backreference indices are shifted by `left_len`. The parser is a hand-written tokenizer, not regexes. It accepts exactly the 1.x language, including `->` and `→`, `{…}` sets, `|` choices, `!` negation, `+`/`?` quantifiers, `@n[mods]`, `:null:`, `#` and `_.onset|nucleus|coda`.
- **Simultaneous (SPE) application.** For fixed-length rules, contexts are matched against the **input** and never consumed; the focus advances by its own length, and a pure insertion keeps the current element. The five regression cases in blindrec's `tests/test_alteruphono_simultaneous.py` and in upstream `tests/test_simultaneous.py` are part of the suite.
- **Quantified rules.** Q1 and Q2 are bugs, and 2.0 will not reproduce them. The design treats quantified rules with the same simultaneous semantics: contexts are matched, not consumed. Matching is greedy for `+` and tries the shorter option first for `?`, as 1.x intends. Every case where 2.0 and 1.x differ on a quantified rule is listed (§8.3).
- **Matching by grapheme.** A literal segment matches by grapheme identity after NFD and the 1.x equivalences (`ɡ`/`g`, `’`/`'`/`ʼ`). It does not match by features, as in 1.x.
- **Syllable conditions.** These use 1.x's sonority syllabifier, ported to C with the same sonority scale over the projected labels.
- **Backward.** The 1.x algorithm: match the post pattern with modifiers carried back onto the ante, form per-window alternatives, take the product, drop interior boundaries, deduplicate, and sort by string. 2.0 adds a hard cap on the number of candidates (`AP_ERR_LIMIT`, with the cap in the options), because the product is exponential and 1.x has no cap.

  Whether the Q3 fixes are part of the 2.0 reference is **D2**. They also change backward results. The design default is yes: take the fixes and list the affected cases.

  `backward_history` and `rival_orders` from the same unmerged branch are not ported in M1; they belong with abstract segments (§4.5).

## 6. The change model

### 6.1 Why the first two attempts failed, and what follows

- **H4 (v4).** A feature-change direction prior counted on alteruphono's catalogue, keyed by `(features lost, features gained)`, environment-free, with λ = 0.25: −0.0010 [−0.0050, +0.0028]. In effect, nothing.
- **v12.** Index Diachronica directions applied to near-tie columns. It failed its gate on 10 of 10 families and on Polynesian. The reasons were these:
  - near-ties were everywhere (1,819 columns in synth-700, of which v12 changed 903);
  - a context-free override "throws away … the likelihood on the tree and the regularity of the whole correspondence set";
  - Index Diachronica has no l/r preference to find (14 against 15).

  The Polynesian error lay in subgrouping, not in direction.

Four design consequences:

1. **Catalogues record which changes are attested, not how often a change happens per opportunity.** A catalogue count is P(attested | type), weighted by how often the source segment exists and how interesting the change was to the person who reported it. The catalogue therefore may **not** set the probability of change; it may set only the **shape** of where the mass goes once a segment changes. The rate per opportunity comes from data in which unchanged segments are counted (§6.3).
2. **Environment and features interact.** Lenition is intervocalic and devoicing is final; palatalisation is before front vowels. An unconditioned direction averages these away. The model conditions on the environment, through assimilation and position terms that are shared across segments by their features (§6.2).
3. **The model must not act on its own.** v12 failed because it overrode the tree and regularity. In 2.0 the model enters blindrec's existing likelihood as substitution rates, and/or as one term of the v8 objective, weighted by the same machinery. It never post-edits columns (§7).
4. **Some directions are genuinely symmetric.** The model has to be able to say so, and `l/r` is one test: the asymmetry it reports there should have an interval that covers 0. A model that found a strong l/r direction would be suspect.

### 6.2 Parameterisation

**Data unit.** One opportunity is a single occurrence of a proto-segment `s` in an aligned proto→daughter pair on branch `b` (proto-language → daughter lect). It is observed together with its proto-environment `e` (the left and right proto-neighbours, or `#`) and its reflex `y`, which is a segment, `∅` (deletion), or `s` itself (no change). Insertions are a second, separate stream: one opportunity per gap position between proto-segments, with outcome "nothing" or an inserted segment.

**Outcome model** (multinomial logit over a declared candidate set `C`):

```
P(y | s, e, b) = exp η(y) / Σ_{y'∈C} exp η(y'),     η(s) = 0   (staying is the reference)

η(y≠s) = α_b                                    branch propensity to change (random effect)
       + Σ_d γ_d · x_d(s)                       source-feature instability, shared across outcomes
       + Σ_k w_k · φ_k(s→y)                     directed displacement terms
       + Σ_{k,j} v_kj · φ_k(s→y) · ψ_j(e)        displacement × environment
       + Σ_m z_m · χ_m(s→y, e)                  assimilation / dissimilation terms
       + u_{s→y}                                pair residual, prior mean from the catalogue
```

The terms are defined as follows.
- **`x_d(s)`** is the merkmal value of `s` on vector dimension `d` (`mk_system_feature_vector`: `+1` present, `−1` absent, `0` inapplicable).
- **`φ_k(s→y)`** are **directed** displacement indicators: one per (dimension, from-value, to-value), with from ≠ to and both in {+, −, 0}.
  - `[voice: − → +]` and `[voice: + → −]` are different parameters. This is where directionality lives: P(a→b) and P(b→a) share no displacement parameter, only the magnitude term.
  - Deletion is its own outcome, with indicators `[∅ | source has d=+]`.
  - A magnitude term counts the changed dimensions.
- **`ψ_j(e)`** are environment predicates:
  - left or right neighbour is `#`, a vowel, or a consonant;
  - the neighbour's value on a small, declared set of dimensions (voice, continuant, nasal, syllabic, front, high);
  - word-initial and word-final position.

  The set is fixed before fitting and listed in the pack.
- **`χ_m(s→y, e)`** are assimilation terms. `[y_d = neighbour_d ≠ s_d]` marks assimilation to the left or right neighbour on dimension d; `[y_d ≠ neighbour_d = s_d]` marks dissimilation. These carry intervocalic voicing, palatalisation and nasal place assimilation across every segment that shares the features, which is the "share strength through merkmal features" requirement.
- **`u_{s→y}`** is a residual for a specific pair of segments. It lets the data overrule the feature terms for a single well-attested change, such as `k > tʃ`, without changing everything else.

**Candidate set `C`.** `C` is part of the question: a probability is relative to the alternatives. Callers pass it explicitly — in blindrec, the column's candidate states — and the pack records the set used for calibration (training inventory of the daughter ∪ {s, ∅}). The feature terms make every merkmal segment scorable, including ones never seen in training.

### 6.3 Exposure normalisation, branch depth, and the one-step approximation

Every proto-segment occurrence is an opportunity, including those where nothing changed. The model therefore estimates changes **per opportunity**, which no catalogue can supply.

`α_b` absorbs how far each branch has travelled. This covers time depth, the number of intermediate stages, and the granularity of the transcription. Its distribution N(μ_α, σ_α²) is fitted. For a new branch, a consumer either integrates over that distribution or supplies its own offset; blindrec has dated trees and its own fitted rate μ.

A proto→daughter pair is the **net** result of a history (p > f > h). This model describes net reflexes over one branch; it does not model chains of changes. Two consequences:
- In blindrec, which already computes `P = expm(Q·t·μ)` (`recon.py` `Substitution`), the model supplies **relative rates**. These are the off-diagonal `exp η` without `α_b`, rescaled to blindrec's exit rates. It does not supply transition probabilities. Rates estimated from net reflexes are a known approximation of instantaneous rates, and they are biased toward net-common outcomes on long branches.
- Calibration is reported **stratified by `α̂_b`** (how much the branch changed), so that a failure of this approximation on deep branches is visible instead of averaged away (§8.4).

A full CTMC fit (expm inside the likelihood, with the environment changing along the branch) is the principled alternative. It is left out of 2.0 because the environment is not constant along a branch, which makes that likelihood intractable without data augmentation. It is listed as future work, not as done.

### 6.4 Prior (catalogue) and fitting (empirical Bayes)

- **Group priors.** Each block of parameters (γ, w, v, z, u) has a Gaussian prior with its own variance: `w ~ N(0, σ_w²)`, `v ~ N(0, σ_v²)`, and so on. A small σ shrinks a block toward zero, so that an environment interaction is used only where the data support it.
- **Catalogue prior on the residuals:**
  ```
  u_{s→y} ~ N( λ · c̃_{s→y}, σ_u² ),      c̃_{s→y} = log((n_{s→y} + κ) / (n_{s→·} + κ·|C_s|)) − mean
  ```
  where `n_{s→y}` counts catalogue rules taking `s` to `y`, and `n_{s→·}` counts all rules from `s`.
  - The catalogue enters as a **conditional share**: given that `s` changes, where it goes. It sets no rate.
  - Environment-specific catalogue counts enter the same way on `v`, keyed by the environment predicates the rule's context implies, using the same parser blindrec's `changegen.parse_line` uses.
  - Catalogue rules over classes are expanded over the training inventory with weight 1/|class|, so that `C > :null: / _ #` does not count as 50 independent attestations.
- **Empirical Bayes.** The hyperparameters are `(σ_γ, σ_w, σ_v, σ_z, σ_u, λ, κ, μ_α, σ_α)`.
  - They are fitted by **type-II maximum likelihood** on the training families, with a Laplace approximation to the marginal likelihood.
  - They are checked against leave-one-family-out log-loss inside the training set.
  - If the two disagree materially, both are reported, and the cross-validated choice is used, because it is the one closer to the use case.
  - `λ` is the catalogue's weight, learned from the data. **λ̂ ≈ 0 would be a finding:** the catalogue adds nothing once exposure is modelled. It would be reported, not tuned away.
- **Variants fitted.** The constitution asks for ablation paths. Every pack is fitted in three variants with the same code:
  - `full`: catalogue prior plus data;
  - `data-only`: λ fixed at 0;
  - `catalogue-only`: no data, with hyperparameters set by the documented defaults below.

  The `catalogue-only` variant is also the M3 deliverable.
- **Fitter.** The fitter is Python (NumPy and SciPy, an optional `[fit]` extra) and runs offline. It maximises the penalised likelihood with L-BFGS from deterministic initial values, and its seed covers the bootstrap.
  - It writes a pack: JSON with `format_version`, the merkmal system fingerprint, the projection, the list of predicates, the parameters, posterior variances, provenance and checksums.
  - The C core only loads and evaluates packs, so neither historia nor blindrec needs SciPy at run time.

**M3 defaults for `catalogue-only`** (there is no data to set them). Every non-identity term is set from the catalogue, and the stay logit is `η_stay` with P(change) = 0.2. That value is a named, stipulated constant, labelled as such in the pack. The calibration report shows what it does, and it is not presented as an estimate.

### 6.5 Uncertainty

- **Laplace posterior.** The posterior over parameters given hyperparameters is the Laplace approximation at the mode.
  - The pack stores the mode and the **diagonal** of the posterior covariance. A full covariance over about 10⁴ parameters is too large to ship.
  - A low-rank correction (the top 50 eigenvectors of the Hessian) is stored as well, so that sampled parameter vectors keep the main correlations, such as those between `w[voice − → +]` and the `v` interactions it shares a block with.
  - It is an approximation and is labelled `C1-laplace`, in the approximation-tier vocabulary of the constitution's §7.2.
- **Hyperparameter uncertainty.** This comes from a **family bootstrap**: resample training families with replacement and refit, with B = 50 planned. Families are the independent units; cognate sets within a family are not.
- **Exposed outputs.** Every probability the API returns can come with an interval. The asymmetry `A(a,b | e) = η(a→b|e) − η(b→a|e)` is reported with its interval, and the interval is what a consumer must use. The point value is never enough on its own.

### 6.6 Circularity, stated

1. **The training data are reconstructions.** Published proto-languages were made with the comparative method, and so with their authors' beliefs about natural directions: an author who believes k > tʃ before front vowels reconstructs *k. A model fitted on proto→daughter pairs partly learns **those beliefs**, and in the constitution's terms they are Door-2 expert input. Using the model to choose proto-segments then risks confirming the handbook with the handbook. Mitigations:
   - The model is a `P_typo` pack, and its provenance names the datasets.
   - The `data-only` and `catalogue-only` ablations are always available.
   - Where a family has a **documented** ancestor rather than a reconstructed one, its pairs are tagged, and calibration is reported separately on them. This is the only part of the data free of the circularity. The documented-ancestor families used in blindrec (Latin, the Germanic gold) are excluded, so this subset may be small. Its size will be reported.
2. **The catalogue and the simulator share sources.** blindrec's simulators v5 and later draw changes from Index Diachronica and from alteruphono's catalogue (`changegen.sample_mixture`). A model whose prior is the same catalogue, scored on families generated from it, gains partly because the prior *is* the generator. The roadmap's decision 15 keeps the simulator's engine separate from alteruphono's; it says nothing about sharing the catalogue. §7 makes this the subject of **D5**.
3. **Alignment.** Training pairs are aligned with a phonetic-distance aligner, which favours small changes. That biases the fitted model toward small changes, and it is the bias the model exists to correct. Mitigations:
   - Align with regulae's correspondence-aware aligner where it applies.
   - Report the share of training opportunities whose alignment differs between two aligners.
   - Drop cognate pairs whose alignment is ambiguous, rather than guess.

### 6.7 Model API (C)

```c
ap_status ap_model_load(const ap_context *ctx, const char *pack_json, size_t len,
                        ap_model **out, ap_diagnosis *diag);  /* AP_ERR_INCOMPATIBLE on fingerprint mismatch */
void      ap_model_free(ap_model *m);
ap_status ap_model_fingerprint(const ap_model *m, const char **out);  /* borrowed */

typedef struct ap_env { ap_seg left, right; uint32_t flags; } ap_env;   /* flags: initial, final, stressed… */
ap_status ap_env_at(const ap_context *ctx, const ap_seg *seq, size_t n, size_t i, ap_env *out);

/* log P(y | s, e) for every candidate; branch_offset is added to α (0 = population mean) */
ap_status ap_model_logprob(const ap_model *m, const ap_context *ctx, ap_seg s, const ap_env *e,
                           const ap_seg *cands, size_t ncand, double branch_offset, double *out);
/* relative off-diagonal rates for an expm-based consumer (blindrec's Substitution) */
ap_status ap_model_rates(const ap_model *m, const ap_context *ctx, ap_seg s, const ap_env *e,
                         const ap_seg *cands, size_t ncand, double *out);
/* P(any change), with a posterior interval at the requested level */
ap_status ap_model_change_prob(const ap_model *m, const ap_context *ctx, ap_seg s, const ap_env *e,
                               double branch_offset, double level, ap_interval *out);
/* directional asymmetry η(a→b|e) − η(b→a|e), with interval */
ap_status ap_model_asymmetry(const ap_model *m, const ap_context *ctx, ap_seg a, ap_seg b,
                             const ap_env *e, double level, ap_interval *out);
/* draw reflexes; deterministic given rng state */
ap_status ap_model_sample(const ap_model *m, const ap_context *ctx, ap_seg s, const ap_env *e,
                          const ap_seg *cands, size_t ncand, double branch_offset,
                          ap_rng *rng, ap_seg *out, size_t ndraws);
/* draw a parameter vector from the posterior: a fixed-parameter model, for simulators */
ap_status ap_model_draw(const ap_model *m, ap_rng *rng, ap_model **out);
/* score a whole aligned lexicon: Σ log P over opportunities (and per-pair values) */
ap_status ap_model_score_lexicon(const ap_model *m, const ap_context *ctx,
                                 const ap_aligned_pair *pairs, size_t npairs,
                                 double branch_offset, double *total, double *per_pair /*NULL ok*/);
```

Python wraps these as `alteruphono.model.ChangeModel.load(path)`. The wrapper exposes `.logprob(src, env, candidates)`, `.rates(...)`, `.change_prob(...)`, `.asymmetry(...)`, `.sample(..., rng=)`, `.draw(rng)` and `.score_lexicon(...)`. Python graphemes and environments are converted once per call; NumPy arrays are accepted for the batch forms.

The model's code is small: one logit per candidate, with sparse features precomputed per (s, y) pair and cached in the context.

## 7. Training split plan (TRAINING_SPLIT.md written and committed before any fit)

**When it is written.** `TRAINING_SPLIT.md` is committed at the start of M3. M3's calibration already needs held-out correspondences, so the split must exist before M3, not M4.

**Exclusion principle (D4).** A dataset is excluded if it contains **any language of a Glottolog top-level family that contains an evaluation family**. Excluding the evaluation datasets alone is not enough, because sister datasets share proto-languages, sources and authors with them.

| excluded (top-level family) | evaluation material it covers | reason |
|---|---|---|
| Indo-European | Germanic (Kroonen), Romance (NorthEuraLex, Latin, UniMorph, IE-CoR Romance), Gothic, PIE/Hittite laryngeal material, the Sanskrit/Greek/Latin kaikki material used by `historia` | scored or used in blindrec |
| Tucanoan | Tukanoan (`chacontukanoan`) | scored |
| Arawakan | `chaconbaniwa` (in-track with Tukanoan) | in a scored track |
| Sino-Tibetan | Burmish, Karen, Bai, Lalo, Bizic | scored |
| Austronesian | Polynesian (ABVD, Walworth) | scored; ABVD spans the whole family |
| Atlantic-Congo | Bantu (`tls`) | scored |
| Mixe-Zoque | Mixe-Zoque | scored |
| Nuclear Trans New Guinea | Finisterre-Huon | scored |
| Uralic, Basque, Albanian, Japonic, Eskimo-Aleut, Dravidian | confounders and null controls (fin, hun, eus, sqi, jpn, ale, mal) | in tracks or null panels; excluding costs little |
| every simulated family | all of blindrec's synthetic tracks | the simulator's own output |

The family-level rule is stricter than the prompt's list. It removes, for example, all non-Polynesian Austronesian data. That loss is real; the reason for paying it is that ABVD and the Polynesian sources overlap with every Austronesian proto-dataset.

**Candidate training datasets**, each to be verified (proto-forms present, licence, version), with a checksum recorded in TRAINING_SPLIT.md before use:
- Lexibank `lionnetyotonahua` and `pharaocoracholaztecan` (Uto-Aztecan). blindrec ingested both but dropped them before scoring. Whether the developer has seen their outputs is to be confirmed (see D4).
- Further Lexibank or CLDF datasets with proto-forms outside the excluded families, found by a search done at M3 and listed there. Nothing is assumed here.
- Wiktionary descendant trees, via the kaikki dumps (the host is reachable), for families outside the exclusion list.

**Expected size.** It is probably small: a few thousand cognate pairs, from perhaps 5–15 families. That is one reason the hierarchical, feature-shared parameterisation matters. Too few families is the main data risk. If fewer than about 5 families qualify, M3 stops and reports, and does not loosen the exclusion.

**Catalogues.**
- alteruphono's `sound_changes.tsv`.
- Index Diachronica v10.2: fetched to a git-ignored path, parsed locally, never committed. Packs fitted from it carry a licence note (CC BY-NC-SA) and store only counts of change types aggregated over many rules. Whether such a derived pack may be committed is **D6**, a licensing question. The default is to keep packs derived from Index Diachronica out of the repository, generated locally by a script.
- Index Diachronica sections for evaluation families are removed from the prior, reusing blindrec's `LEAVE_OUT` filters (`recon.py:1463`), extended to the family-level rule above.

**Calibration split.** The training families are split, **by family**, into fit (about 70%) and calibration-held-out (about 30%). The split is drawn with a recorded seed and committed in TRAINING_SPLIT.md. Calibration therefore measures transfer to an unseen family, which is the use case. A secondary within-family split by cognate set is reported as well.

## 8. Parity strategy

### 8.1 Oracle

The oracle is Python 1.x at tag `v1.0.0rc1-simultaneous` (= `b466d90`), installed in a separate virtualenv as `alteruphono` and driven through a subprocess harness. The two versions can therefore never import each other.

The Q3 fixes are the subject of D2. If Tiago accepts them, the oracle becomes `b466d90` plus `3fdb52b`, taken as a patch, and the tag of that oracle is recorded.

### 8.2 Suites

1. **Upstream tests.** The 233 upstream tests run against the 2.0 package, unchanged. Tests that exercise the dropped `tresoldi`/`distinctive` systems or 1.x feature internals are listed one by one as intended breaks, each with its reason.
2. **Catalogue.** All 801 test pairs, wrapped in `# … #`.
3. **Simultaneity.** The five simultaneous-application regression cases (upstream and blindrec).
4. **Randomised differential test, at least 50,000 applications.**
   - (a) blindrec's own stream: `scripts/check_soundengine.py`'s generator (`Simulator4(Params4(seed=800))` words, `changegen.sample_mixture` rules). This needs the locally fetched Index Diachronica.
   - (b) A grammar-based generator of random rules over the full 1.x notation, including quantifiers, sets, negation and modifiers, applied to random words from the catalogue's test forms. At least 200,000 applications, with a fixed seed.
   - Both report agreement counts and every disagreement.
5. **Backward.** Every catalogue rule applied to its `TEST_POST`, and to the outputs of the differential stream, comparing the full candidate sets.
6. **Fuzzing (regulae style).** libFuzzer targets for `ap_rule_parse`, `ap_parse_sequence`, `ap_forward` and `ap_backward`, built with ASan and UBSan. They run 15 s each in `scripts/check.sh --full`, seeded from the catalogue.

### 8.3 Expected and intended differences

Each must be listed and agreed (D1, D2):
- the merkmal projection cases in §4.1 (labial handling, tone mapping, eight `mid` vowels, `ʈʂː`, two clicks, three unresolved graphemes), with **every** catalogue, differential or backward case they change;
- Q1 and Q2, quantified rules (none in the catalogue, the blindrec stream or blindrec's own engine);
- Q3, if D2 is accepted;
- intended upstream test breaks, `tresoldi`/`distinctive`.

### 8.4 blindrec byte-identity

**Run.** blindrec is run with its vendored 1.x and with 2.0 on a fixed set of development tracks:
- two simulated development tracks (seeds 140 and 141, full and short);
- one development family from 700–709;
- the Romance and Tukanoan stage 1–5 runs.

The stage 1–5 runs never read gold; gold is only reached through `evaluate.py`.

**Comparison.** Every file under `data/work*/<track>/` is compared byte for byte. Every differing file is explained down to the rule or grapheme that causes it.

**Expectation.** If D3 keeps the 1.x geometry distance, the expectation is identity except for cases traceable to §8.3. If D3 switches to merkmal, the outputs will differ everywhere, and byte-identity is replaced by a pre-registered re-run.

The guard is never disabled (`BLINDREC_GUARD=0` is not used).

## 9. Speed targets

The targets are measured on the same machine as the baselines, and the benchmark scripts are committed in `bench/`. All of these are targets until M1/M2 measure them.

| operation | Python 1.x (measured) | target | basis |
|---|---|---|---|
| `forward`, C call, catalogue stream | 25.9 µs | **≤ 0.25 µs (≥ 100×)** | bitset class tests on interned ids |
| `forward` through the 1.x Python API (tuples of `Sound`) | 25.9 µs | **≤ 1.3 µs (≥ 20×)** | the main risk: rebuilding the output tuple and the C crossing; mitigated by interned `Sound`s |
| `forward_lexicon` (Python, batch, a ruleset over a lexicon) | 25.9 µs × words × rules | **≥ 100× per application** | one crossing per lexicon |
| `backward`, Python API | 43.2 µs | ≥ 20× | |
| `parse_rule`, Python API | 68.9 µs | ≥ 20× | |
| scoring a lexicon: Σ log P over aligned opportunities | Python reference implementation of the same model (written in M3 as the oracle for the C scorer) | **≥ 20×**, and ≤ 0.2 µs per opportunity in C | precomputed sparse (s, y) features |
| blindrec stage 5 on a dev track, wall clock | measured in M2 | reported, no target | stage 5 is dominated by `expm` and EM, not by alteruphono |

The last row is there to be honest about scope. Faster rule application speeds up blindrec's simulators v1–v4 and the catalogue checks; it barely moves stage 5. Whatever speed-up stage 5 gets from 2.0 comes from the model replacing Python cost callables, and it will be reported as measured.

## 10. Evaluation plan with gates

### M1: engine parity

**Gate.** M1 passes when all of these hold:
- §8.2 suites 1–5 agree except for the cases listed in §8.3, each agreed by Tiago;
- the fuzzers run clean under ASan and UBSan for 15 s each;
- `-Werror` builds pass with gcc and clang.

### M2: bindings in blindrec

**Gate.** M2 passes when both hold:
- blindrec runs unmodified, with `vendor/alteruphono` swapped for the 2.0 package;
- §8.4 holds: byte-identity, or every diff explained.

Speed numbers (§9) are reported, but they are not a gate on correctness. A missed speed target is recorded as missed.

### M3: catalogue-prior model and calibration

**Order.** `TRAINING_SPLIT.md` is committed first.

**Report.** On the calibration-held-out families, it covers:
- **log-loss per opportunity** (substitution stream and insertion stream separately);
- **reliability curves**:
  - for P(change), in 10 bins, with bootstrap bands over families;
  - for the probability assigned to the observed reflex;
  - stratified by environment type (`#_`, `V_V`, `_#`, other) and by `α̂_b` tercile;
- **expected calibration error**;
- the same quantities for the **baselines**:
  - (i) uniform over `C`, with P(stay) fitted on the fit split;
  - (ii) phonetic distance: a softmax over `−d(s,y)/T` using merkmal's dissimilarity, with T and P(stay) fitted on the fit split;
  - (iii) catalogue-only: the M3 pack;
  - (iv) blindrec's existing `historia/direction.py` p(y|x), which is the incumbent catalogue model.

**Gate.** M3 has no pass/fail gate, because the catalogue-only model is a baseline. M4's calibration gate is defined against it.

### M4: data-fitted model, then the stage-5 test

**Calibration gate (development, on the calibration-held-out families).** The fitted `full` model must:
- have lower log-loss than every baseline, with a family-bootstrap 95% interval excluding 0 against the best baseline;
- have an ECE below 0.05 on P(change);
- give l/r an asymmetry whose interval covers 0. This is a sanity check, not a target, and it is reported either way.

If the calibration gate fails, M4 stops before blindrec. The failure is recorded, and no held-out seeds are spent.

**Stage-5 integration (blindrec v16, planned in PREREG before any test family exists)** — details in the [blindrec note](notes/blindrec.md):
- **Variant R (rates).** `Substitution` uses the model's relative rates `ap_model_rates(x, ·, env)` in place of `exp(−Costs)`, with the existing EM over observed changes left on. The column `ctx` is replaced by the proto-environment that `column_envs` already computes.
- **Variant O (objective).** The v8 move score at `recon.py:1582` gains a term `λ₂ · Σ_d w_d · (−log P(y_d | x, env))`, where `w_d` are v8's independence weights. λ₂ = 1 is fixed a priori. It may be changed only on development families, and any change is recorded.
- The variant to freeze is chosen on development families: R, O, or R+O, whichever has the lowest paired development NED against v8. If none beats v8 on development, nothing is frozen.

**Development gate (before freezing).** On the existing development families (700–709 full lists, plus the short variants of 140–163):
- the paired NED of v16 − v8 has a 95% bootstrap upper bound below 0 on full lists;
- it is not worse on short lists (upper bound < +0.005).

This development gate is also where the paired SD is measured for the power calculation below.

**Held-out test (scored once).** The run is:
1. freeze v16 at a commit;
2. generate fresh simulated families;
3. score them once.

The primary comparison is paired, **v16 − v8**, on full lists and on short lists. These are two co-primary comparisons, each passing if its 95% bootstrap upper bound is below 0.

The real tracks (Germanic, Romance, Tukanoan, Tier B) are secondary. They are developer-exposed and are reported as such, with the ablated `data-only` and `catalogue-only` variants alongside.

**Power.** v8's own gate (v8 − v5 on 20 families: −0.0226, CI [−0.0436, −0.0041]) implies a paired SD of about 0.045. At 80% power and α = 0.05, the minimum detectable effect is:

| families per list length | minimum detectable effect |
|---|---|
| 20 | ≈ 0.028 |
| 40 | ≈ 0.020 |
| 80 | ≈ 0.014 |

The proposal is **60 families per list length**: 15 per template, minimum detectable effect about 0.016. N is fixed in PREREG after measuring the paired SD on development families: N = ⌈(2.8·SD/0.016)²⌉, capped at 100.

**Seeds.** Fresh seeds are proposed at 7000–7059, plus their short variants. At freezing they are checked against `data/sealed`, `data/work*`, the archive and PREREG, following blindrec's procedure, and replaced with the next unused seed where needed.

**Circularity on simulated families (D5).** §6.6 point 2 means the gain on simulated families is inflated if the simulator and the prior share a catalogue. Options:
- **(a)** Split Index Diachronica and alteruphono's catalogue into two halves, by source language family, with a recorded seed:
  - the prior is fitted on half A;
  - the fresh test families are simulated from half B, through a `changegen` filter, which is a small blindrec change;
  - development families stay as they are.
- **(b)** The primary comparison uses the `data-only` variant, with no catalogue. The `full` variant is reported as secondary.
- **(c)** Accept the shared catalogue, and state the circularity.

**Recommendation: (a)** with (b) reported alongside. Option (a) tests the real use case: whether attested change types help on a family that changes by other attested types.

## 11. Decisions for Tiago

| id | question | default if unanswered |
|---|---|---|
| **D1** | Accept the `alteruphono-1` projection rules in §4.1 (drop `labial`, map tone labels, accept merkmal on the 8 + 1 + 2 cases) and the resulting listed diffs? | yes; the diffs are listed in M1 for your sign-off |
| **D2** | Does the parity reference include the Q3 fixes from the unmerged `claude/backward-latents`? Are the Q1/Q2 quantifier fixes accepted? | yes to both, with every affected case listed |
| **D3** | Keep the 1.x geometry distance as a C compatibility function for `get_system().sound_distance`, so that blindrec's outputs stay byte-identical, with moving to merkmal's dissimilarity left as a separate blindrec decision? | yes |
| **D4** | Exclude at Glottolog top-level family (§7, stricter than the prompt's list)? Has the developer seen outputs on `lionnetyotonahua`/`pharaocoracholaztecan`, and if so, may they still be training data? | family-level; Uto-Aztecan used unless you object |
| **D5** | How to handle the simulator sharing the prior's catalogue: (a) split, (b) data-only primary, or (c) state it? | (a) + (b) |
| **D6** | May a pack that contains aggregated counts derived from Index Diachronica be committed? | no; generated locally |
| **D7** | merkmal's bundle API is on an orphan branch. Rebase or port it to merkmal master (large; [merkmal note](notes/merkmal.md) item 2), or should alteruphono build against that branch? | wait for master; M1 builds without abstract segments |
| **D8** | Pushing the 1.x tags (the session's git proxy refused tag pushes; the tags exist locally) | you push them (commands in the summary) |

## 12. Mistakes and corrections in this draft

- **§6.7 as built (2026-11-13) differs from the sketch.**
  - **Pack format.** Packs are tab-separated text, not JSON, so the C core needs no JSON parser. A pack holds the parameters, the merkmal labels it was fitted against (checked at load) and the catalogue rules.
  - **API.** The scorer takes graphemes, not segment ids: `ap_model_eta` and `ap_model_logprob`.
  - **Mutability.** A model caches feature vectors, distances and per-environment catalogue reflexes, so it is **mutable**: it is used by one thread at a time, with the context it was loaded into. The sketch called it immutable.
  - **Not built:** sampling, asymmetry intervals and Laplace draws. The posterior covariance stays in the fitter's output (`*_cov.npy`).

- I first ran the catalogue test pairs without boundaries and got 571 of 801. The test forms in `sound_changes.tsv` omit `#`. Wrapped, all 801 pass, and the suite in §8.2 wraps them.
- The prompt says simulators v5–v9 agreed with alteruphono on 50,000/50,000 applications. Only simulator v5 was checked (`scripts/check_soundengine.py`). v6, v7 and v9 reuse its engine (`synth5.Simulator5`), so the agreement covers them by inheritance, not by a separate check.
- **The `labial` rule in §4.1 was wrong as first written (found in M1).** "Drop `labial`" also removed the only place label of the 42 bilabial clicks (`ʘ`, `gʘ`, `ŋʘ`, …), for which 1.x uses `labial` as the place. The parity harness showed it as feature-only differences on `ʘ`. The rule now drops `labial` only where a finer place label is present. With it, the projection equals 1.x for 7,342 of the 7,353 graphemes merkmal resolves; the other 11 are exactly the D1 cases.
- The prompt counts "219+" upstream tests. That was the count when blindrec vendored `607b9f5`; master has 233.
