> Historical plan. Four new single-activity files have now been evaluated with the frozen V2 model at 90.00% accuracy. No further recording is needed to report this steady-state result. The timed mixed run below would test transitions in future work.

# Remaining steps

The three mixed sensor files have been received and analysed. Do not repeat the
whole dataset automatically. The notebook and five-page report are provisional
because activity-change times were not measured.

## 1. Verify the activity intervals

Check the CSVs in data/annotations/ against a timed log or synchronized full-run video
if you have one. The participant-confirmed test order is jumping, walking, still,
standing, but the signal is quiet around 16–23 s and moving around 24–39 s. We kept
your confirmed order and did not swap it to improve scores. Do not treat model
predictions as ground truth when checking the labels.

If no timing evidence exists, the clearest next step is one new mixed test run with a
full-run video or explicit activity-change log. Keep the existing fitted model fixed.
Record each activity for roughly 8–10 seconds, note actual seconds_elapsed change
times including any start delay, and allow time for placing/picking up the phone.
A helper can film you and the phone, while Sensor Logger records continuously.
Send both the ZIP and the timing evidence. This is a new test, not a reason to tune
against the current uncertain test and reuse it as untouched evidence.

## 2. Check the still-video framing

The longer replacement videos exceed five seconds. In sampled still-video frames,
part of your body is cropped at the left edge. Use a wider frame or a longer original
that keeps your face, full body and flat stationary phone visible together for at
least five seconds. Keep the required holding position consistent in other videos.

## 3. Finish the report and repository

Read output/pdf/activity_hmm_report_draft.pdf and report_draft.md. Add your author
name/ID and accessible video URLs; check the report's actual five-page layout after
edits. Publish this project's contents to its own GitHub repository, including real
CSV data, annotations, executed notebook, implementation, report and figures.
The parent folder's unrelated sentiment-analysis project should not be uploaded.

The current poor/uncertain scores must be reported honestly. A clearly explained
limitation is preferable to changing test labels or presenting estimated times as
precise measured ground truth. Use submission_checklist.md before hand-in.
