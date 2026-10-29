# Why the original score was low and what has improved

The original test result was 11 correct windows out of 24: 45.83%. Validation was
12/21 = 57.14%. Neither score is an independently verified ground-truth result:
mixed activity-change times were estimated. The participant-confirmed test order
was retained even where it conflicts with the raw quiet/moving signal pattern.
Changing reference labels to increase the score would not improve the model.

## A low model score is not automatically a failed assignment

The assignment text supplied here does not specify an accuracy pass mark. It asks
for a working HMM, real data, unseen evaluation, figures and honest reflection.
The historical baseline did not demonstrate reliable recognition, but it identified
problems. The instructor determines assessment marks.

## Development-only improvements already tested

Eight fixed comparisons used training and validation recordings only. No historical
test sensor file was opened, and no v2 test predictions were computed by this search.
The factors were all eight versus four features, raw versus log1p magnitude/power
scaling, and window-weighted versus recording-balanced Gaussian emission fitting.
Transition smoothing/floor remained fixed at 0.1/0.05.

The best validation accuracy is **19/21 = 90.48%**, macro-F1 0.904, up from 57.14%
and 0.569. Several candidates tie. The simpler selected model uses the standard
unweighted Gaussian fit with four features: acceleration magnitude mean, acceleration
magnitude standard deviation, gyroscope magnitude RMS, and acceleration spectral
high-band fraction. The first three receive log1p compression before training-only
standardization. Both time and frequency domains remain represented.

The original model included frequency peaks in almost motionless signals, where the
peak can come from noise. It also had correlated magnitude/SMA features and skewed
power values. Original isolated walking has mean magnitude around 2.96 m/s²; the
mixed training and validation walking are around 1.48 and 1.45 m/s². This difference
is observed; changed grip/pace is a possible explanation, not an independently logged
fact. Feature reduction and log scaling improve validation agreement without using
test labels. They do not prove which physical factor caused the original errors.

The two remaining validation errors are near estimated activity changes. More
precisely timed labels may clarify them. Validation has only 21 dependent windows,
approximate boundaries and was used for model selection. The four subsequent,
single-activity test files provide a separate unseen evaluation.

## Current model files and reproducibility

The development comparison was run with `python improve_model.py`; the notebook now
reads its saved outputs so re-running it preserves the frozen test model.
Results are under results/improvement_v2/: validation_comparison.csv,
selected_validation_metrics.csv, selected_validation_predictions.csv,
validation_comparison.png, selection.json and selected_hmm_v2.npz.

The model can be applied with improve_model.decode_v2 using the original eight raw
features; it applies its saved feature selection, log transform and scaler before
Viterbi. Do not call the four-feature model on untransformed eight-feature inputs.

The original PDF/report and results/test_metrics.csv document the historical v1
baseline. The five-page V2 report is output/pdf/activity_hmm_report_v2.pdf.

## Fresh unseen result

Four new same-day Sensor Logger files were recorded after V2 selection, one per
activity. They were excluded from fitting and tuning. The frozen model scored
**27/30 = 90.00% accuracy**, macro-F1 **0.888**: standing 4/7, walking 8/8,
jumping 8/8 and still 7/7. Three quiet standing windows were predicted as still.
The raw files, source hashes, sampling audit, predictions, per-state metrics and
model hash are saved in data/ and results/fresh_test_v2/.

This test measures steady-state recognition from four separate recordings, not
within-file activity transitions. All four are from the same participant, iPhone
and day. The 30 adjacent windows are correlated, so broader generalization is not
established. The old 45.83% V1 score and new 90.00% V2 score use different models
and reference designs, so their gap is not a controlled estimate of improvement.

## Further evidence, if desired

A continuous test with independently recorded activity-change times would evaluate
transition detection. The existing four-file test is sufficient for an honest
steady-state result. If V2 is redesigned using these new results, collect another
untouched test before claiming new unseen performance. Do not change historical
reference labels merely to match predictions. Additional sessions and a second
validation run would strengthen future development.

No honest method guarantees the best possible unseen accuracy or 100%. The goal
is reproducible recognition on correct labels and genuinely new measurements.

Reference: [scikit-learn guidance on evaluation and test leakage](https://scikit-learn.org/stable/modules/cross_validation.html).
