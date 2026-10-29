Real, unmodified Sensor Logger CSV exports are stored here, one folder per recording.
The original seven recording IDs are in ../recordings.csv; four later single-activity
test IDs are in ../fresh_test_v2_recordings.csv. Each contains calibrated and
uncalibrated sensor CSVs, Metadata.csv and the original empty Annotation.csv.
Source-member hashes are in the two import-provenance JSON files in ../.
Keep the original timestamp columns. Do not replace these with fabricated rows.

The loader expects calibrated iOS data, acceleration in m/s² without gravity,
gyroscope in rad/s, with seconds_elapsed,x,y,z columns in both sensor files.
The loader aligns sensors by timestamp, never row index.
