# Human Activity States Using a NumPy HMM

**Author: Mahamat bakhit** · [Video evidence](https://mahamatbt.github.io/human-activity-hmm/)

See [rubric_status.md](rubric_status.md) for remaining rubric requirements,
including Baum–Welch, data-file quantity clarification and missing figures.

Individual iPhone experiment, updated 28 October 2026. The **frozen V2 model
correctly classified 27 of 30 two-second windows (90.00%)** in four newly recorded,
separately labelled activity files. Macro-F1 was 0.888. The four files were kept out
of training and validation. Standing was correct in 4/7 windows; walking 8/8,
jumping 8/8 and still 7/7. Three quiet standing windows were predicted as still.

The primary deliverable is the [five-page V2 report](output/pdf/activity_hmm_report_v2.pdf).
The [executed notebook](human_activity_hmm.ipynb) reproduces the original HMM
experiment, displays the saved V2 development comparison, and evaluates the frozen
model on the four new files. [Fresh test metrics](results/fresh_test_v2/test_metrics.csv),
[predictions](results/fresh_test_v2/test_predictions.csv), and
[model hash/results summary](results/fresh_test_v2/summary.json) are saved.

This result measures steady activities for **one person, iPhone and date**. The four
fresh test recordings each contain only one activity. They do not establish how well
the model recognizes real transitions within a continuous recording or generalizes
to other people, phones, days or environments. Thirty neighbouring windows are not
thirty independent trials.

## Data and reproducibility

The project includes eleven real Sensor Logger exports: four initial single-activity
training files, mixed training and validation files, one historical mixed test, and
four fresh single-activity V2 tests. The original calibrated accelerometer and
gyroscope CSVs are in `data/raw/`; all source-member hashes are recorded in
`data/import_provenance.json` and `data/fresh_test_v2_import_provenance.json`.
All sensor CSVs retain timestamps. The app requested 50 Hz; measured average rates
for the fresh tests were 50.1739–50.1757 Hz. The pipeline aligns both sensors to
50 Hz and takes non-overlapping two-second windows.

V2 uses four features: acceleration magnitude mean and standard deviation,
gyroscope magnitude RMS, and acceleration high-band FFT power fraction. The first
three are transformed with log1p; all four are standardized with training-only
statistics. A supervised four-state diagonal Gaussian HMM supplies emissions;
the mixed training run supplies the transition matrix. Viterbi decodes each complete
recording separately. The [model-selection script](improve_model.py) compared eight
development variants using validation only. The chosen model reached 19/21 (90.48%)
validation accuracy, then was saved as `results/improvement_v2/selected_hmm_v2.npz`
before the fresh test. [The evaluator](evaluate_fresh_v2.py) loads that file without
fitting or tuning.

The older V1 model scored 11/24 (45.83%) on an approximately labelled mixed test.
The participant confirmed the activity order, but exact change times were not
measured and the reported walking/still order conflicts with the signal pattern.
That result is retained in `results/` and `output/pdf/activity_hmm_report_draft.pdf`
as historical evidence. It uses a different model and reference design, so the
45.83% and 90.00% figures are not a controlled paired comparison.

To run locally:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m jupyter lab human_activity_hmm.ipynb
```

Open the notebook from this folder. It is saved with real execution outputs. For
Colab, upload the entire project ZIP; the notebook alone lacks its support modules
and dataset. Re-running the notebook reads the saved V2 comparison and frozen
model; it does not replace the model selected before the fresh test. Run
`python -m unittest discover -s tests -v` for the eight algorithm/pipeline checks.
The temporary synthetic fixtures used by those checks are not study data.

## Video evidence and submission

The public videos are [standing (9.77 s)](https://mahamatbt.github.io/human-activity-hmm/videos/standing.mp4),
[walking (5.23 s)](https://mahamatbt.github.io/human-activity-hmm/videos/walking.mp4),
[jumping (11.48 s)](https://mahamatbt.github.io/human-activity-hmm/videos/jumping.mp4) and
[still (10.33 s)](https://mahamatbt.github.io/human-activity-hmm/videos/still.mp4). Sampled still-video frames crop
part of the participant at the left edge. Check the rubric's full-body, face,
lighting and phone visibility criteria. The report includes the author's name,
these video links and the [public GitHub repository](https://github.com/Mahamatbt/human-activity-hmm).
Browser-compatible copies live in docs/videos; the jumping clip was converted from
HEVC to H.264 without trimming or changing the recorded activity.

See [submission_checklist.md](submission_checklist.md) for the remaining hand-in
steps. The unrelated project in the parent folder is not part of this submission.

References: [Sensor Logger help](https://www.tszheichoi.com/sensorloggerhelp),
[units](https://github.com/tszheichoi/awesome-sensor-logger/blob/main/UNITS.md),
[HMM algorithm tutorial](https://hmmlearn.readthedocs.io/en/stable/tutorial.html).
