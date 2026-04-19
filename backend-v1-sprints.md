# Backend V1 — Micro-Sprint Execution Plan

Source plan: `plan.md`
Revision focus: break backend V1 into 1–2 day micro-sprints, preserve all locked decisions, maximize explainability + error analysis readiness, and prepare clean Phase-2 contracts without implementing dual-branch clinical prior yet.

---

## Part 1 — Heavy Sprints Identified

| # | Original Area (from `plan.md`) | Why it is heavy | Main Risk |
|---|---|---|---|
| H1 | Data audit + manifest + conflict resolution + provenance | Multiple gates and schemas in one block | Silent data leakage or mislabeled training set |
| H2 | Training baseline | Model, sampler, early stopping, checkpoint logic together | Unstable training and irreproducible best model |
| H3 | Evaluation + calibration + error analysis | Metrics, per-sample outputs, ECE, error exports combined | Good headline metric but weak model behavior visibility |
| H4 | Explainability pipeline | Grad-CAM generation, failure handling, galleries, summaries | Non-deterministic or broken explainability artifacts |
| H5 | Feature extraction preparation | 15+ features, validity masks, split-aware summaries | Feature drift and inconsistent definitions across team |
| H6 | Review pack generation | Multi-source joins (predictions + heatmaps + features) | Psychologist review files incomplete/inconsistent |
| H7 | End-to-end quality gates | Determinism, invalid conflict fail case, smoke tests | Late discovery of pipeline regressions |

---

## Part 2 — Refactored Sprint List (At A Glance)

```text
PHASE 0 — CONTRACTS & FOUNDATION
  S0a  Artifact directory and config skeleton
  S0b  Stable schemas: manifest / predictions_v1 / features_v1 / review_pack
  S0c  CLI entrypoint skeletons (build_manifest, train, evaluate, extract_features, generate_reports)

PHASE 1 — DATA GOVERNANCE
  S1a  Label provenance contract and validator
  S1b  Exact-hash audit + conflict candidate export
  S1c  Conflict resolution gate (hard-fail on unresolved/invalid rows)
  S1d  Deterministic stratified split (70/15/15, seed=42) + manifest export
  S1e  Optional near-duplicate (phash) audit report (non-blocking)

PHASE 2 — IMAGE-ONLY TRAINING BASELINE
  S2a  Dataset + transforms + WeightedRandomSampler wiring
  S2b  EfficientNet-B0 training loop + checkpoint save (last/best)
  S2c  Early stopping + best metric (val macro_f1) + config snapshot

PHASE 3 — EVALUATION, CALIBRATION, ERROR ANALYSIS
  S3a  Test inference runner + predictions_test.csv
  S3b  Metrics + confusion_matrix + per-class breakdown
  S3c  Calibration outputs (ECE-10bin + confidence histogram)
  S3d  Error analysis exports (misclassified, high_confidence_errors, low_confidence_cases)

PHASE 4 — EXPLAINABILITY
  S4a  Grad-CAM generation + heatmap_path contract
  S4b  Explainability failure handling (explainability_failures.csv)
  S4c  Correct/incorrect galleries + class markdown reports
  S4d  Explainability sanity checks (empty/low-content/corrupted behavior reporting)

PHASE 5 — CLINICAL-TRANSITION FEATURE PREP
  S5a  High-confidence feature block extraction
  S5b  Medium-confidence feature block extraction
  S5c  Exploratory feature block extraction + validity masks
  S5d  Split-aware feature summaries (train/val/test separately)
  S5e  Review pack assembly (required schema + joins)

PHASE 6 — HARDENING & RELEASE CANDIDATE
  S6a  End-to-end CLI integration and artifact map validation
  S6b  Determinism + invalid conflict fail-case + smoke tests
  S6c  Full dry-run and release checklist for Backend V1
```

Total: 24 micro-sprints (mostly 1 day, some 2 days).

---

## Part 3 — Micro-Sprint Details

### PHASE 0 — CONTRACTS & FOUNDATION

**S0a · Artifact Directory + Config Skeleton**
- Goal: Standardize outputs and run configuration early.
- Scope: Create canonical artifact folders and one runtime config schema (`seed`, `split`, `model`, `metrics`, `paths`).
- Checkpoint: A dry run produces empty but valid directory tree and config file.

**S0b · Stable Data Schemas**
- Goal: Freeze machine-readable contracts.
- Scope: Define schema validators for `manifest`, `predictions_v1`, `features_v1`, `review_pack`.
- Checkpoint: Validator passes for good fixtures and fails for malformed fixtures with explicit errors.

**S0c · CLI Skeletons**
- Goal: Lock command interfaces before implementation details.
- Scope: Add no-op CLI entrypoints for `build_manifest`, `train_image_only`, `evaluate_image_only`, `extract_features`, `generate_reports`.
- Checkpoint: Each command runs with `--help`; argument names match `plan.md`.

---

### PHASE 1 — DATA GOVERNANCE

**S1a · Label Provenance Contract**
- Goal: Prevent folder-name-only labeling assumptions.
- Scope: Enforce `data/label_provenance.md` presence and required sections (label source, annotation procedure, version/date).
- Checkpoint: Missing or incomplete provenance file blocks manifest build.

**S1b · Exact-Hash Conflict Audit**
- Goal: Detect cross-class identical images.
- Scope: Compute SHA-256, export `conflict_candidates.csv` with cross-class collisions.
- Checkpoint: Audit report generated deterministically on same data.

**S1c · Conflict Resolution Gate**
- Goal: Ensure conflict handling is explicit and auditable.
- Scope: Parse `data/conflict_resolution.csv` (`keep/drop/relabel`), enforce full resolution, hard-fail unresolved entries.
- Checkpoint: Pipeline fails on invalid decision; passes after corrected file.

**S1d · Deterministic Split + Manifest**
- Goal: Produce training-ready canonical manifest.
- Scope: Stratified split `70/15/15` with `seed=42`; export required columns including `split`, image metadata, hash.
- Checkpoint: Two consecutive runs produce identical split assignments.

**S1e · Optional Near-Duplicate Audit (phash)**
- Goal: Add visibility without blocking V1.
- Scope: Generate `near_duplicate_audit.csv` using perceptual hash; no hard gate.
- Checkpoint: Report exists and is referenced in audit summary.

---

### PHASE 2 — IMAGE-ONLY TRAINING BASELINE

**S2a · Dataset Pipeline + Sampler**
- Goal: Reliable data loading and class imbalance handling.
- Scope: Implement dataset reader from manifest, train/val transforms, `WeightedRandomSampler` on train split.
- Checkpoint: One mini-epoch runs without shape or class-index errors.

**S2b · EfficientNet-B0 Training Loop**
- Goal: Baseline learning loop with checkpointing.
- Scope: Implement forward/backward loop, optimizer, epoch logging, save `last.pt` and provisional `best.pt`.
- Checkpoint: 3-epoch smoke run writes checkpoints and history JSON.

**S2c · Early Stopping + Best Metric Lock**
- Goal: Stabilize model selection policy.
- Scope: Early stopping on validation, best model strictly by `val macro_f1`, export `config_snapshot.json`.
- Checkpoint: Best checkpoint changes only when `val macro_f1` improves.

---

### PHASE 3 — EVALUATION, CALIBRATION, ERROR ANALYSIS

**S3a · Test Inference + Predictions Contract**
- Goal: Per-sample prediction traceability.
- Scope: Generate `predictions_test.csv` with `sample_id,true_label,pred_label,top1_conf,top2_conf,entropy,correct`.
- Checkpoint: Predictions file row count equals test split size.

**S3b · Core Metrics + Confusion Outputs**
- Goal: Reliable headline + class-wise performance view.
- Scope: Compute `accuracy, macro_f1, balanced_accuracy`, per-class PRF1, confusion matrix exports.
- Checkpoint: Metrics and confusion files are produced and schema-valid.

**S3c · Calibration Outputs**
- Goal: Confidence quality visibility.
- Scope: Compute ECE (10 bins) and confidence histogram, save `calibration.json`, `confidence_histogram.csv`.
- Checkpoint: ECE value and bin table generated for test predictions.

**S3d · Error Analysis Exports**
- Goal: Operational error triage.
- Scope: Build `misclassified.csv`, `high_confidence_errors.csv`, `low_confidence_cases.csv` using fixed thresholds from config.
- Checkpoint: All three files exist and have non-overlapping definitions.

---

### PHASE 4 — EXPLAINABILITY

**S4a · Grad-CAM Core Integration**
- Goal: Per-sample visual rationale artifacts.
- Scope: Generate heatmap overlays for test samples; write `heatmap_path` back to explainability table.
- Checkpoint: At least one sample per class has valid overlay output.

**S4b · Explainability Failure Handling**
- Goal: No silent explainability breakage.
- Scope: Log failed heatmap generations into `explainability_failures.csv` with reason codes.
- Checkpoint: Forced failure case is captured in failure log; pipeline completes.

**S4c · Galleries + Class Reports**
- Goal: Human-review-ready explainability packaging.
- Scope: Create correct/incorrect galleries per class and class-level markdown summaries.
- Checkpoint: Gallery folders and class reports are generated with linked sample IDs.

**S4d · Explainability Sanity Checks**
- Goal: Detect suspicious behavior on weak inputs.
- Scope: Add sanity batch (empty/low-content/corrupted images) and record confidence/explainability behavior summary.
- Checkpoint: `explainability_sanity_summary.json` reports anomaly rates and counts.

---

### PHASE 5 — CLINICAL-TRANSITION FEATURE PREP

**S5a · High-Confidence Feature Block**
- Goal: Implement stable low-ambiguity signals.
- Scope: `fg_area_ratio`, `empty_space_ratio`, `stroke_darkness_mean`, `component_count_norm`, `shading_ratio`.
- Checkpoint: Features computed for >99% valid test samples (or documented reasons).

**S5b · Medium-Confidence Feature Block**
- Goal: Implement structured geometry proxies.
- Scope: `centroid_y_norm`, `top_mass_ratio`, `bottom_mass_ratio`, `sharp_angle_ratio`, `dominant_orientation_abs`.
- Checkpoint: Feature ranges and validity flags pass schema checks.

**S5c · Exploratory Feature Block + Validity Masks**
- Goal: Add low-confidence proxies without overclaiming.
- Scope: `face_candidate_count`, `figure_integrity_proxy`, `warm_ratio` + strict `*_valid` fields.
- Checkpoint: Invalid extraction paths produce `NaN` + `valid=0`, never silent fallback values.

**S5d · Split-Aware Summaries**
- Goal: Prevent train/test leakage in interpretation.
- Scope: Export separate summaries: `feature_summary_train.csv`, `feature_summary_val.csv`, `feature_summary_test.csv`.
- Checkpoint: Test-only summary can be generated and reviewed independently.

**S5e · Review Pack Assembly**
- Goal: Produce psychologist-ready minimum schema.
- Scope: Build `review_pack_test.csv` with required fields (`sample_id, split, true_label, pred_label, top1_conf, top2_conf, entropy, correct, original_image_path, heatmap_path, selected_feature_fields`) + optional `reviewer_note`.
- Checkpoint: Review pack row count equals test size; required columns are complete.

---

### PHASE 6 — HARDENING & RELEASE CANDIDATE

**S6a · End-to-End CLI Wiring**
- Goal: One-command reproducible backend run.
- Scope: Wire commands in sequence: manifest → train → evaluate → explain → feature extract → review pack.
- Checkpoint: Fresh run completes and populates all expected artifact folders.

**S6b · Quality Gate Test Set**
- Goal: Lock regression gates for V1.
- Scope: Run determinism checks, invalid conflict hard-fail test, explainability smoke test, feature extraction smoke test.
- Checkpoint: All gates pass and outputs are versioned with timestamp.

**S6c · Backend V1 Release Checklist**
- Goal: Freeze V1 handoff package.
- Scope: Produce final artifact index, schema versions, known limitations, and next-step contract for Phase-2 (`priors_v0` reserved fields).
- Checkpoint: Release checklist signed off; backend V1 marked ready.

---

## Part 4 — Five-Point Validation (Run Per Micro-Sprint)

Before closing a micro-sprint:
1. CLI/schema validation for touched outputs passes.
2. Sprint-specific checkpoint test passes on local run.
3. At least one prior critical checkpoint still passes (cheap regression).
4. New artifacts are written under agreed paths and readable.
5. If the sprint touches labels/splits, determinism check (`seed=42`) is re-run.

---

## Part 5 — What Is Preserved

- Locked decisions from `plan.md` are unchanged: 4 classes, image-only baseline, EfficientNet-B0, best checkpoint by `val macro_f1`, stratified split `70/15/15`, `seed=42`.
- API/UI remains out of scope.
- V1 remains explicitly non-diagnostic.
- Explainability, calibration, and error analysis are first-class outputs (not optional).
- Feature extraction is implemented as auxiliary analysis data, with validity masks and confidence-tier interpretation.
- Phase-2 interfaces (`predictions_v1`, `features_v1`, `priors_v0`) are prepared without forcing dual-branch implementation in V1.
