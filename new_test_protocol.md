# One fresh, independently timed v2 test

**Historical proposed protocol.** Four separate single-activity files were instead
collected and evaluated with the frozen model; see results/fresh_test_v2/. This
protocol remains useful only if a later continuous transition test is wanted.

The current v2 model is frozen at results/improvement_v2/selected_hmm_v2.npz.
Do not tune it using the following recording's outcomes.

1. Use the same iPhone/settings and a consistent grip/waist-level placement for
   standing, walking and jumping. For still, the phone must be flat on a surface.
2. Have a helper film the complete run continuously, with your whole body and phone
   visible. Include the moment you press Sensor Logger's Start so the video has a
   synchronization anchor to seconds_elapsed. Avoid a separate unsynchronized demo.
3. Allow a few seconds to settle. Perform each of the four activities for about
   10 seconds. Announce each change aloud so it can be located in the video.
   Include standing, walking, jumping and phone-on-surface still in any recorded order.
4. The helper should note the actual change times from the video and its Start
   anchor. Do not assume activities started at the planned cue if they did not.
   Note pickup/placement periods separately; windows spanning them may be mixed.
5. Keep logging continuously through changes and allow time to stop. A 45–60 second
   recording is enough for an initial new check; two or three independent runs would
   give stronger evidence if time allows. Do not repeat the whole original dataset.
6. Export Zipped CSV under a new name such as v2_test_timed_01. Keep the full-run
   video and actual activity timing notes. Do not copy/rename an existing export.
7. Supply the new ZIP and timing evidence. Apply the frozen transform/scaler/model
   once, report per-state sensitivity/specificity and accuracy, and update the report
   with the true v2 unseen result. Preserve the old baseline as historical evidence.

If the new test motivates more model changes, it becomes development evidence and
another untouched timed recording is needed for the next final test.
