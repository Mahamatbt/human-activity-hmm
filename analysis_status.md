# Analysis status — 28 October 2026

The frozen four-feature V2 HMM has now been scored on four new, separately labelled
Sensor Logger exports collected later the same day. The new files were not used in
feature choice, scaling, emission fitting or transition estimation. The evaluator
loads `results/improvement_v2/selected_hmm_v2.npz` and records its SHA-256 hash in
`results/fresh_test_v2/summary.json`.

The unseen V2 result is **27/30 = 90.00% accuracy**, macro-F1 **0.888**. By state:
standing 4/7, walking 8/8, jumping 8/8, still 7/7. Standing's three middle
windows were predicted as still. These are adjacent two-second windows within only
four files, not independent trials. The files test steady-state recognition, not
real changes among activities. They all use the same person, phone and date.

The selected V2 model reached 19/21 = 90.48% on approximate mixed-run validation
labels. The older V1 model reached 11/24 = 45.83% on an approximate mixed test.
Its walking/still reference order remains unresolved against the signal pattern;
the user-confirmed labels were not changed to increase accuracy. Those V1 results
are historical and are not a paired baseline for the new four-file test.

The five-page V2 PDF includes the required table, training transition heatmap,
decoded sequences, confusion matrix, methods and limitations. Original source CSVs,
hashes, sampling audits, model parameters, predictions and metrics are included.

Author Mahamat bakhit, public video links and the GitHub repository link are now
included in the report. See rubric_status.md for remaining grading requirements.
Check the still video's full-body framing. A continuous,
independently timed test would be useful future evidence for transition detection,
but is not needed to report the present four-file state-recognition result.
