"""Import the four untouched, single-activity iPhone test exports.

Run once with the source directory as the only argument. The activity labels come
from the export filenames; no model output is consulted while preparing them.
"""
from pathlib import Path
import csv
import hashlib
import json
import sys
import zipfile

from activity_hmm import read_sensor


ROOT = Path(__file__).resolve().parent
STATES = ("standing", "walking", "jumping", "still")
MEMBERS = (
    "Accelerometer.csv", "Gyroscope.csv", "AccelerometerUncalibrated.csv",
    "GyroscopeUncalibrated.csv", "Metadata.csv", "Annotation.csv",
)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def import_exports(source):
    source = Path(source)
    archives = sorted(source.glob("*.zip"))
    if len(archives) != 4:
        raise ValueError(f"Expected exactly four ZIPs; found {len(archives)}.")
    seen = set()
    records, provenance = [], []
    for archive in archives:
        activity = archive.name.split("-", 1)[0].lower()
        if activity not in STATES or activity in seen:
            raise ValueError(f"Missing or duplicate single-activity ZIP label: {archive.name}")
        seen.add(activity)
        recording_id = f"p01_fresh_test_v2_{activity}_20261028"
        dest = ROOT / "data/raw" / recording_id
        dest.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as z:
            if set(z.namelist()) != set(MEMBERS):
                raise ValueError(f"Unexpected archive contents in {archive.name}: {z.namelist()}")
            for name in MEMBERS:
                contents = z.read(name)
                target = dest / name
                if target.exists() and target.read_bytes() != contents:
                    raise ValueError(f"Refusing to replace changed source file: {target}")
                target.write_bytes(contents)
                provenance.append(dict(source_archive=archive.name, source_archive_sha256=sha256(archive.read_bytes()),
                                       source_member=name, destination=str(target.relative_to(ROOT)),
                                       sha256=sha256(contents), bytes=len(contents)))
        with (dest / "Metadata.csv").open(newline="") as f:
            metadata = next(csv.DictReader(f))
        if metadata["device name"] != "iPhone 13 Pro" or metadata["sampleRateMs"].split("|")[0] != "20":
            raise ValueError(f"Unexpected device or sampling request in {archive.name}")
        ta, _, aa = read_sensor(dest / "Accelerometer.csv")
        tg, _, ag = read_sensor(dest / "Gyroscope.csv")
        if len(ta) != len(tg) or max(abs(ta - tg)) > 1e-6:
            raise ValueError(f"Sensor timestamps disagree in {archive.name}")
        # Fixed edge rule chosen from duration alone: skip 2 s startup, retain
        # complete 2 s windows only, and leave any incomplete tail out.
        start = 2.0
        end = start + 2 * int((min(ta[-1], tg[-1]) - start) // 2)
        if end <= start + 4:
            raise ValueError(f"Too short for evaluation: {archive.name}")
        records.append(dict(recording_id=recording_id, participant_id="p01", session_id="run_20261028_fresh_test_v2",
                            split="fresh_test_v2", activity=activity, status="recorded",
                            accel_file=str((dest / "Accelerometer.csv").relative_to(ROOT)),
                            gyro_file=str((dest / "Gyroscope.csv").relative_to(ROOT)),
                            annotation_file="", trim_start_s=start, trim_end_s=end,
                            requested_rate_hz=50, phone_model=metadata["device name"],
                            ios_version=metadata["platform version"], app_version=metadata["appVersion"],
                            collected_at=metadata["recording time"], environment="",
                            notes="Fresh separate single-activity file; label from filename. Fixed 2 s startup trim; complete 2 s windows only.",
                            boundary_guard_s=0, annotation_quality="participant-labelled single-activity file",
                            source_zip=archive.name, raw_duration_s=float(ta[-1] - ta[0]),
                            accel_average_rate_hz=aa["average_rate_hz"], gyro_average_rate_hz=ag["average_rate_hz"],
                            accel_largest_gap_s=aa["largest_gap_s"], gyro_largest_gap_s=ag["largest_gap_s"]))
    records.sort(key=lambda r: STATES.index(r["activity"]))
    out = ROOT / "data/fresh_test_v2_recordings.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader(); writer.writerows(records)
    (ROOT / "data/fresh_test_v2_import_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return records


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python import_fresh_test_v2.py /path/to/new-tests-v2")
    for record in import_exports(sys.argv[1]):
        print(record["activity"], record["raw_duration_s"], record["trim_start_s"], record["trim_end_s"])
