# Saved real-data outputs

`improvement_v2/selected_hmm_v2.npz` is the frozen model chosen using training
and validation only. `improvement_v2/validation_comparison.csv` records all eight
candidate scores; `selection.json` records the choice rule and selected features.

`fresh_test_v2/` contains the later four-file evaluation: `summary.json` with the
frozen model hash and 27/30 (90.00%) score, `test_metrics.csv` with the required
four-state table, `test_predictions.csv` with every two-second decision,
`sampling_audit.csv`, a confusion matrix and decoded-sequence figures. The four
files were scored separately without fitting or tuning. They test steady activity
recognition for one person/phone/day, not changes within a continuous recording.

Files directly under `results/` are the historical V1 experiment using seven
original recordings. Training has 282 windows, approximate mixed validation 21,
and approximate mixed test 24. Its `test_metrics.csv` gives 45.83% agreement with
uncertain participant-order/signal-timed references. The walking/still mismatch is
explained in `data/annotation_provenance.json`; the user-confirmed order was not
changed to improve scores. `fitted_hmm.npz` is V1, and `preliminary_hmm.npz` is an
earlier initial-four-file fit. These are not the frozen V2 model.

No synthetic study data or favourable relabelling were used.
