# Design note: historia and alteruphono 2.0

The framework's `00_overview.md` describes historia, the planned C99 + Python engine, as implementing the diachronic layer with "alteruphono internal". Today the Python reference lives in blindrec (`blindrec/historia/`, roadmap Stage E). Nothing here has been implemented.

## What historia gets from the C API

- **The deterministic forward model.** historia's forward score composes rules along a graph path (constitution §6.4: "Opacity = path composition"). It needs:
  - `ap_forward_ruleset` with an `ap_trace` (which rule fired where, which renderings failed);
  - `ap_backward` with the permissive policy for abstract segments, which returns proposals `q(·)`, not evidence.
- **Contexts that can be cloned for parallel chains.** `ap_context_clone`. Models are immutable and shareable across clones.
- **Abstract segments as merkmal bundles**, identified by (system fingerprint, bundle text), never by a label. This matches `interchange.md` §3.7 and is three-valued in tests (`AP_UNKNOWN` versus `AP_INAPPLICABLE`).
- **A versioned `P_typo` pack** (`ap_model_*`). Calls:
  - `ap_model_logprob` and `ap_model_rates` for the likelihood;
  - `ap_model_draw` for a parameter vector sampled from the posterior;
  - `ap_model_sample` for simulating reflexes;
  - the ablation variants (`full`, `data-only`, `catalogue-only`) for the `typo_dominated` check.

## Proposals for historia's design

1. **Packs in the run bundle.**
   - `interchange.md` §3.6 lists `packs: {P_struct, P_typo?, ...}`. An alteruphono model pack should be recorded there with its fingerprint, variant and training split (the commit of `TRAINING_SPLIT.md`).
   - `interchange.md` has no schema yet for change priors (its §5 lists open items). The pack's JSON header (DESIGN §6.4) is offered as a starting point.
2. **Leave-target-out by construction.**
   - The constitution's §6.10 requires `P_typo` to be leave-target-out.
   - A pack records which families it excludes. historia should refuse a pack whose training data contain the target family: a fingerprint check against the pack's exclusion list, not a convention.
3. **Replace `blindrec/historia/direction.py`.**
   - That module is a catalogue-only p(y | x), with a fixed identity share of 0.6 and a pseudo-count of 5 pulling the catalogue toward a feature kernel.
   - It is the incumbent that the change model must beat in calibration (DESIGN §10, baseline iv).
   - If M4's calibration gate passes, the E1 value step can call the pack instead. That is an analysis change, so it needs its own PREREG entry in blindrec.
4. **Never a majority-leaf direction.**
   - The model is a prior. Where a historia decision is decided by it (`prior_dominated` in `08_latent_elements.md`), that flag must be raised.
   - The asymmetry interval (`ap_model_asymmetry`) is the quantity to report, not the point value.
