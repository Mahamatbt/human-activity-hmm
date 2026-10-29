For each mixed recording, create the annotation CSV named in ../recordings.csv.
Columns: start_s,end_s,activity
Units: seconds on the same seconds_elapsed clock as the raw sensor files.
Allowed activities: standing,walking,jumping,still.

Use continuous, non-overlapping intervals covering the entire retained recording.
Annotate actual observed change times using a synchronized video or timed activity log.
Do not assume the planned cue times were the actual transition times.
Document the uncertainty of these labels, especially while placing/picking up the phone.

The activity at the midpoint is the label of each 2-second feature window.
The feature pipeline also records the fraction of that window occupied by its label.
Mixed windows are included for sequence decoding and midpoint evaluation; only pure
windows estimate emission parameters. A pure-window test score is also reported.

Single-activity recordings do not need annotation files: their labels and verified
trim intervals come from ../recordings.csv. CSVs here must contain real annotations,
not an illustrative schedule copied without checking it.
