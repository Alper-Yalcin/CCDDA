# Backend V1 Final Plan: Explainable, Analysis-Oriented, Clinically Transition-Ready Image-Only Baseline

## 1. Short Summary
- This plan builds a 4-class image-only backend V1 that is not just a metric generator, but also includes explainability, robust error analysis, and clinical-transition preparation.
- V1 scope: data audit + manifest, training, evaluation, explainability artifacts, feature extraction artifacts, review pack generation, and Phase-2 interface preparation.
- V1 is not a clinical diagnosis system. Emotion classes are not clinical disorder labels.

## 2. Implementation Changes

### Data audit and manifest
- Required classes: `Happy, Sad, Angry, Fear`.
- Manifest schema: `sample_id,image_path,label,label_id,split,sha256,width,height,age_months,task_type,context_note`.
- Split: stratified `70/15/15`, `seed=42`, deterministic.
- Exact duplicate control is mandatory: produce cross-class conflict candidates using SHA-256.
- `data/conflict_resolution.csv` required schema: `sha256,decision,final_label,note`; `decision in {keep,drop,relabel}`.
- Pipeline must hard-fail on unresolved conflicts or invalid decisions.
- Near-duplicate note: in V1, exact hash is mandatory; perceptual hash (`phash`) audit is optional and non-blocking.
- Label provenance requirement: `data/label_provenance.md` must exist with class definitions, label source, annotation procedure, and version/date.

### Training pipeline
- Model: `EfficientNet-B0` (ImageNet pretrained), single head, 4 logits.
- Input: `224x224`; augmentation on train only; deterministic transform for val/test.
- Class imbalance handling: `WeightedRandomSampler`.
- Loss/optimizer: Cross-Entropy + AdamW + early stopping.
- Best checkpoint criterion: only `val macro_f1`.
- Outputs: `checkpoints/best.pt`, `checkpoints/last.pt`, `train_history.json`, `config_snapshot.json`.

### Evaluation pipeline
- Required metrics: `accuracy`, `macro_f1`, `balanced_accuracy`, per-class precision/recall/f1, confusion matrix.
- Per-sample output: `predictions_test.csv` with `top1_conf`, `top2_conf`, `entropy`.
- Calibration included: confidence histogram + `ECE` (10 bins).
- Outputs: `metrics.json`, `confusion_matrix.csv`, `calibration.json`, `confidence_histogram.csv`.
- Error analysis outputs: `misclassified.csv`, `high_confidence_errors.csv`, `low_confidence_cases.csv`.

### Explainability pipeline
- Generate Grad-CAM overlays for test split.
- Produce `heatmap_path` per sample; log failures.
- Auto-generate class-level correct/incorrect galleries.
- Explainability failures do not crash the whole pipeline; they are reported in `explainability_failures.csv` and summarized.

### Clinical feature extraction preparation
- Feature extraction does not feed V1 model decisions; it produces auxiliary analysis artifacts only.
- `features_v1.csv` is generated for full manifest while preserving `split`.
- Split-aware summaries are mandatory: `feature_summary_train.csv`, `feature_summary_val.csv`, `feature_summary_test.csv`.
- Test summary must be separately reported; mixed all-split summaries are not used for decision reporting.

### Phase-2 compatibility preparation
- Stable contracts:
- `predictions_v1`: per-sample model outputs + explainability paths.
- `features_v1`: auxiliary visual features + validity mask.
- `priors_v0`: reserved schema `prior_happy,prior_sad,prior_angry,prior_fear,prior_valid` (nullable in V1).
- Join key in all artifacts: `sample_id`.

## 3. Explainability and Analysis Outputs
- `reports/galleries/correct/<class>/`: highest-confidence correct samples per class + heatmaps.
- `reports/galleries/errors/<true>_as_<pred>/`: critical misclassifications + heatmaps.
- `reports/class_reports/<class>.md`: per-class metrics, typical errors, confidence profile.
- `reports/explainability_summary.json`: heatmap generation rate, failure counts, class summaries.
- `reports/error_analysis_summary.json`: confusion pairs, high-confidence error rate, entropy distribution.
- Explainability sanity behavior:
- Track and report overconfident behavior on empty/low-content images.
- Random/corrupted inputs are logged as invalid-input behavior; stable clinical-like explanation is not expected.

## 4. Clinical Feature Extraction Preparation
- Features are treated as auxiliary signals; never as standalone diagnosis/decision.
- Confidence tiering:
- High-confidence auxiliary features: `fg_area_ratio`, `empty_space_ratio`, `stroke_darkness_mean`, `component_count_norm`, `shading_ratio`.
- Medium-confidence auxiliary features: `centroid_y_norm`, `top_mass_ratio`, `bottom_mass_ratio`, `sharp_angle_ratio`, `dominant_orientation_abs`.
- Low-confidence/exploratory proxies: `face_candidate_count`, `figure_integrity_proxy`, isolated color-semantic interpretations (`warm_ratio` alone is non-diagnostic).
- Every feature has a `*_valid` flag; invalid values are `NaN` with valid flag `0`.

## 5. Feature Specification Summary

| Feature | Short Definition | Computation Logic | Type/Range | Invalid Condition | Core Method |
|---|---|---|---|---|---|
| `fg_area_ratio` | Drawing occupancy ratio | Foreground pixels / total pixels | float [0,1] | No foreground detected | Adaptive threshold + morphology |
| `empty_space_ratio` | Empty space ratio | 1 - `fg_area_ratio` | float [0,1] | `fg_area_ratio` invalid | Derived |
| `bbox_area_ratio` | Main drawing box ratio | Largest component bbox area / canvas area | float [0,1] | No component | Connected components |
| `centroid_x_norm` | Horizontal center of mass | Foreground centroid x / width | float [0,1] | No foreground | Image moments |
| `centroid_y_norm` | Vertical center of mass | Foreground centroid y / height | float [0,1] | No foreground | Image moments |
| `top_mass_ratio` | Top-half mass ratio | Top-half foreground / total foreground | float [0,1] | No foreground | Foreground split |
| `bottom_mass_ratio` | Bottom-half mass ratio | Bottom-half foreground / total foreground | float [0,1] | No foreground | Foreground split |
| `stroke_darkness_mean` | Mean stroke darkness | Mean (1-luma) over foreground pixels | float [0,1] | No foreground | Grayscale stats |
| `component_count_norm` | Fragmentation proxy | Component count / (img_area/10k) | float >=0 | No foreground | Connected components |
| `skeleton_break_count_norm` | Skeleton break proxy | Normalized endpoint count on skeleton | float >=0 | Skeleton extraction failed | Skeletonization + endpoint graph |
| `shading_ratio` | Shading intensity ratio | Dark dense local regions / foreground | float [0,1] | No foreground | Local variance + dark mask |
| `unique_hue_count` | Color diversity | Unique hue bins where S > threshold | int [0,180] | No reliable color content | HSV histogram |
| `warm_ratio` | Warm color ratio | Warm hue pixels / colored pixels | float [0,1] | Colored pixels too low | HSV band rules |
| `sharp_angle_ratio` | Angularity | Sharp corner ratio on contours | float [0,1] | No valid contour | Contour approximation + angle calc |
| `dominant_orientation_abs` | Dominant orientation | Absolute normalized main-axis angle | float [0,1] | No foreground | PCA orientation |
| `face_candidate_count` | Face candidate count (exploratory) | Count from heuristic shape/contrast candidates | int >=0 | Candidate extraction failed | Heuristic detection |
| `figure_integrity_proxy` | Figure integrity proxy (exploratory) | Composite score from component/extension/symmetry cues | float [0,1] | Missing required sub-signals | Rule-based composite |

## 6. Review Pack Schema
- File: `reports/review_pack/review_pack_test.csv`
- Required fields:
- `sample_id`
- `split`
- `true_label`
- `pred_label`
- `top1_conf`
- `top2_conf`
- `entropy`
- `correct`
- `original_image_path`
- `heatmap_path`
- `selected_feature_fields` (JSON string; includes at least high/medium-confidence subset)
- Optional field:
- `reviewer_note` (default empty string)

## 7. Public Interfaces and CLI Commands
- Manifest + audit:
```bash
python -m src.data.build_manifest \
  --data-dir data \
  --out artifacts/v1_backend/data/manifest.csv \
  --split 0.70 0.15 0.15 \
  --seed 42 \
  --conflict-file data/conflict_resolution.csv \
  --label-provenance data/label_provenance.md \
  --audit-out artifacts/v1_backend/data_audit \
  --near-dup-audit phash
```
- Feature extraction:
```bash
python -m src.features.extract_features \
  --manifest artifacts/v1_backend/data/manifest.csv \
  --out artifacts/v1_backend/features/features_v1.csv \
  --summary-out artifacts/v1_backend/features \
  --split-aware
```
- Training:
```bash
python -m src.train.train_image_only \
  --manifest artifacts/v1_backend/data/manifest.csv \
  --out artifacts/v1_backend/train \
  --model efficientnet_b0 \
  --epochs 30 --batch-size 32 --seed 42 \
  --select-metric macro_f1
```
- Evaluation:
```bash
python -m src.eval.evaluate_image_only \
  --manifest artifacts/v1_backend/data/manifest.csv \
  --ckpt artifacts/v1_backend/train/checkpoints/best.pt \
  --out artifacts/v1_backend/eval \
  --save-preds --calibration ece --ece-bins 10
```
- Explainability + reports:
```bash
python -m src.explain.generate_reports \
  --manifest artifacts/v1_backend/data/manifest.csv \
  --preds artifacts/v1_backend/eval/predictions_test.csv \
  --ckpt artifacts/v1_backend/train/checkpoints/best.pt \
  --features artifacts/v1_backend/features/features_v1.csv \
  --out artifacts/v1_backend/reports \
  --per-class-gallery 40
```

## 8. Test Plan
- Manifest determinism test: identical split output for same seed.
- Invalid conflict-file fail case: hard-fail on missing columns or unresolved hashes.
- Label distribution sanity check: split-level class distribution drift below threshold.
- Feature extraction smoke test: required features + `*_valid` columns exist.
- Split-aware reporting test: separate test summary is generated and not mixed with all-split reporting.
- Explainability smoke test: heatmap generation on small test subset and path validation.
- Explainability sanity check:
- Empty/low-content images: overconfidence rate is measured and reported.
- Corrupted/random input behavior is logged as invalid behavior.
- Heatmap generation failures are recorded in `explainability_failures.csv`.
- Error analysis output test: all error files and gallery directories are produced.
- Calibration test: `ECE` and confidence histogram outputs are generated.

## 9. Assumptions and Limitations
- This is not a clinical diagnosis system.
- Emotion labels are not clinical disorder labels.
- Label source/procedure must be documented; label quality is a separate risk area.
- Folder names are not annotation provenance by themselves; provenance document is authoritative.
- Age/context/task-type effects are only partially handled in V1; full clinical-prior integration is Phase-2.
- Features are auxiliary analysis signals and cannot independently justify clinical conclusions.
- API/UI are out of scope for this phase.

## 10. Locked Decisions
- Classes: `Happy, Sad, Angry, Fear`.
- Approach: image-only baseline is retained.
- Model: `EfficientNet-B0`.
- Best-checkpoint criterion: `val macro_f1`.
- Split: stratified `70/15/15`, `seed=42`.
- Duplicate gate: exact-hash mandatory, near-duplicate audit optional.
- API/UI out of scope.
- Clinical prior dual-branch implementation deferred to Phase-2.
