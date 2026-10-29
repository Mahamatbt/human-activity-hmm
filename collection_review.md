> Historical initial-file review, before replacements/mixed runs arrived. See analysis_status.md for the current provisional evaluation.

# Review of the initial recordings — 28 October 2026

The supplied folder contains four Sensor Logger exports and four demonstration
videos. Original files in Downloads were not edited. The CSVs were copied into
`data/raw/`, videos into `videos/`, and source-file hashes saved in
`data/import_provenance.json`.

## What is available

The metadata identifies one iPhone 13 Pro, iOS 26.5, Sensor Logger 1.68, with a
requested motion-sensor interval of 20 ms (50 Hz). Standardisation was off. We use
the calibrated Accelerometer.csv and Gyroscope.csv, not the uncalibrated streams.
Both sensor files use named x/y/z columns despite their exported z,y,x order.

- Standing: 6,091 rows per sensor, 121.39 seconds of timestamp span, measured
  average rate 50.1673 Hz.
- Walking: 6,264 rows per sensor, 124.85 seconds, measured average rate 50.1635 Hz.
- Jumping: 6,391 rows per sensor, 127.37 seconds, measured average rate 50.1669 Hz.
- Still: 6,164 rows per sensor, 122.85 seconds, measured average rate 50.1668 Hz.

Both sensors have identical timestamps within each of these exports. There are no
invalid numeric rows or duplicated timestamps in the calibrated streams. The
largest timestamp interval is approximately 0.0211 s, below the 0.2 s rejection
threshold. The export's Annotation.csv files are empty; labels come from the
user-confirmed recording names, not time-stamped in-app interval annotations.

The user confirmed that “still” means the phone flat on a surface. Sitting while
holding the phone is not used as a fifth activity or substituted for still.

## What the notebook has completed

The four recordings are assigned to one initial collection session and used for
training only. A common fixed edge trim retains seconds 2–120, with original raw
data preserved. This excludes recording edges without selecting favourable windows.
It does not remove every hand movement or guarantee perfectly pure human labels.

The pipeline filters and aligns to 50 Hz, yielding 5,900 six-axis rows per activity,
23,600 aligned rows altogether. Two-second non-overlapping windows produce **59
windows per activity, 236 observations total**. A window is not an independent
recording. All 236 labels are pure under the supplied single-activity annotations;
that purity value expresses annotation coverage, not independently verified movement.

The executed notebook contains real training-signal plots, the sampling audit,
features, a preliminary HMM, and its transition probabilities/counts. It uses fixed
smoothing=1.0 and variance floor=0.1, without validation tuning. Five implementation
checks pass. The model and scaling parameters are in `results/preliminary_hmm.npz`.

No cross-activity changes were observed in the four isolated recordings. Each
activity contributes 58 self-transitions and no off-diagonal counts. Off-diagonal
probabilities in the heatmap come entirely from smoothing. The high diagonal
probabilities reflect this controlled collection and cannot establish everyday
transition behaviour. Unrelated files were not concatenated.

## Video review

Durations were read from the MP4 containers with ffprobe. Sampled frames show the
participant's face/body and the phone; this was a sampled-frame review, not a
frame-by-frame guarantee of compliance throughout every clip.

- Standing video: **4.768 s**, below five seconds. Use a longer original or retake.
- Jumping video: **4.868 s**, below five seconds. Use a longer original or retake.
- Walking video: **5.233 s**, exceeds five seconds. The sampled framing shows the
  whole body and phone. Keep the original available.
- Still video: **5.267 s** overall, but it includes placing the phone down. The phone
  is still being held at about 0.79 s, leaving less than five seconds afterward.
  Record at least 6–8 seconds after the phone is already flat and stationary.

For replacement videos, allow 6–8 usable seconds of the actual activity, keep the
whole body/face/phone visible in good lighting, and follow the required waist-level
holding position. Do not stretch or pad a short video to imitate a longer activity.
The required report links have not been supplied; `data/video_links.csv` records the
local files and duration findings without inventing public URLs.

## What is still missing

There are **no independent validation or unseen test recordings** in the supplied
folder. No unseen sensitivity, specificity, accuracy, confusion matrix or decoded
mixed-test sequence can be reported yet. The final metrics table remains unfilled.
Splitting the existing recordings into more files would not create a new session.

Follow `next_recordings.md`: add a continuous training run, a distinct validation run,
and a later untouched test run, each with all four activities. Short activity blocks
are sufficient; the existing two-minute recordings do not need to be repeated.
After those steps, complete the 4–5 page report and publish the GitHub repository.

The assignment's “approximately 20 samples” wording remains ambiguous. The current
dataset has four source recordings and 236 feature windows. Report those quantities
accurately; if the instructor intended 20 independent trials, four long recordings
do not satisfy that interpretation.
