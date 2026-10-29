"""Small, readable activity-recognition pipeline; HMM algorithms use NumPy.

Raw inputs are calibrated Sensor Logger iOS CSVs, not synthetic examples.
All timestamps below use seconds_elapsed from the same recording clock.
"""
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from scipy.signal import butter, sosfiltfilt

STATES = ("standing", "walking", "jumping", "still")
FEATURE_NAMES = (
    "acc_mag_mean", "acc_mag_std", "acc_sma", "gyro_mag_rms",
    "acc_dominant_hz", "acc_highband_fraction", "gyro_ac_power", "gyro_dominant_hz",
)


def read_sensor(path):
    """Read one sensor, preserving its recording-relative time origin."""
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    needed = ["seconds_elapsed", "x", "y", "z"]
    if not set(needed).issubset(df.columns):
        raise ValueError(f"{path}: expected {needed}; found {list(df.columns)}. "
                         "Use calibrated Sensor Logger CSV export; inspect other schemas first.")
    clean = df[needed].apply(pd.to_numeric, errors="coerce")
    valid = np.isfinite(clean.to_numpy()).all(axis=1)
    removed = int((~valid).sum())
    if removed > max(1, 0.05 * len(df)):
        raise ValueError(f"{path}: too many invalid rows ({removed}/{len(df)}).")
    clean = clean.loc[valid].sort_values("seconds_elapsed")
    duplicates = int(clean.seconds_elapsed.duplicated().sum())
    clean = clean.drop_duplicates("seconds_elapsed", keep="first")
    if len(clean) < 30:
        raise ValueError(f"{path}: too few sensor rows.")
    t = clean.seconds_elapsed.to_numpy()
    dt = np.diff(t)
    audit = {
        "sensor_file": str(path), "input_rows": len(df), "valid_unique_rows": len(t),
        "invalid_rows_removed": removed, "duplicate_timestamps_removed": duplicates,
        "median_rate_hz": float(1 / np.median(dt)),
        "average_rate_hz": float((len(t) - 1) / (t[-1] - t[0])),
        "largest_gap_s": float(dt.max()),
        "interval_iqr_s": float(np.percentile(dt, 75) - np.percentile(dt, 25)),
    }
    return t, clean[["x", "y", "z"]].to_numpy(), audit


def _filtered_native(t, values, target_hz):
    """Regularize small timing jitter, then low-pass BEFORE rate reduction.

    This is offline preprocessing: zero-phase filtering uses future samples.
    Gaps exceeding 0.2 s are rejected instead of interpolated across.
    """
    rate = 1 / np.median(np.diff(t))
    if rate < 0.9 * target_hz:
        raise ValueError(f"Observed {rate:.2f} Hz is below target {target_hz} Hz. "
                         "Choose a lower common target before training; upsampling adds no information.")
    if np.diff(t).max() > 0.2:
        raise ValueError("Sensor gap exceeds 0.2 seconds; inspect or recollect this recording.")
    native_t = np.arange(t[0], t[-1] + 1e-10, 1 / rate)
    native_values = np.column_stack([np.interp(native_t, t, a) for a in values.T])
    cutoff = 0.4 * min(rate, target_hz)
    sos = butter(4, cutoff, btype="lowpass", fs=rate, output="sos")
    return native_t, sosfiltfilt(sos, native_values, axis=0)


def load_recording(root, row, target_hz=50):
    """Synchronize sensors by timestamps, never by row number."""
    ta, a, aa = read_sensor(Path(root) / row.accel_file)
    tg, g, ag = read_sensor(Path(root) / row.gyro_file)
    start, end = float(row.trim_start_s), float(row.trim_end_s)
    if not np.isfinite([start, end]).all() or end <= start:
        raise ValueError(f"{row.recording_id}: enter measured trim_start_s and trim_end_s.")
    # Filter the full recording so retained windows have surrounding context.
    ta, a = _filtered_native(ta, a, target_hz)
    tg, g = _filtered_native(tg, g, target_hz)
    if start < max(ta[0], tg[0]) or end - 1 / target_hz > min(ta[-1], tg[-1]):
        raise ValueError(f"{row.recording_id}: requested trim lies outside sensor overlap.")
    n = int(np.floor((end - start) * target_hz + 1e-6))
    grid = start + np.arange(n) / target_hz
    aligned = np.column_stack([
        *[np.interp(grid, ta, axis) for axis in a.T],
        *[np.interp(grid, tg, axis) for axis in g.T],
    ])
    frame = pd.DataFrame(aligned, columns=["acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z"])
    frame.insert(0, "seconds_elapsed", grid)
    for audit, sensor in ((aa, "accelerometer"), (ag, "gyroscope")):
        audit.update(recording_id=row.recording_id, sensor=sensor,
                     requested_rate_hz=row.requested_rate_hz, resampled_rate_hz=target_hz,
                     trim_start_s=start, trim_end_s=end)
    return frame, [aa, ag]


def _spectrum(magnitude, rate):
    """Dominant frequency, 3–10 Hz power fraction, and mean-square AC power."""
    centered = magnitude - magnitude.mean()
    frequencies = np.fft.rfftfreq(len(centered), 1 / rate)
    # Hann taper for peak and band fraction; omit DC.
    power = np.abs(np.fft.rfft(centered * np.hanning(len(centered)))) ** 2
    band = (frequencies >= 0.5) & (frequencies <= 10)
    band_power = power[band].sum()
    dominant = float(frequencies[band][np.argmax(power[band])]) if band_power > 1e-12 else 0.0
    high = float(power[(frequencies >= 3) & (frequencies <= 10)].sum() / band_power) if band_power > 1e-12 else 0.0
    # Parseval scaling of the untapered one-sided FFT: mean-square AC power.
    p = np.abs(np.fft.rfft(centered)) ** 2
    weights = np.full(len(p), 2.0)
    weights[0] = 1
    if len(centered) % 2 == 0:
        weights[-1] = 1
    ac_power = float(np.dot(weights, p) / len(centered) ** 2)
    return dominant, high, ac_power


def window_features(values, rate):
    a, g = values[:, :3], values[:, 3:]
    am, gm = np.linalg.norm(a, axis=1), np.linalg.norm(g, axis=1)
    af, ah, _ = _spectrum(am, rate)
    gf, _, gp = _spectrum(gm, rate)
    return np.array([am.mean(), am.std(), np.abs(a).sum(axis=1).mean(),
                     np.sqrt(np.mean(gm ** 2)), af, ah, gp, gf])


def annotations_for(root, row):
    if row.activity in STATES:
        return pd.DataFrame([dict(start_s=float(row.trim_start_s),
                                  end_s=float(row.trim_end_s), activity=row.activity)])
    if row.activity != "mixed" or not str(row.annotation_file).strip():
        raise ValueError(f"{row.recording_id}: activity must be a state or mixed with an annotation file.")
    ann = pd.read_csv(Path(root) / row.annotation_file).sort_values("start_s").reset_index(drop=True)
    if len(ann) == 0 or not set(["start_s", "end_s", "activity"]).issubset(ann.columns):
        raise ValueError("Mixed annotations need nonempty start_s,end_s,activity intervals.")
    starts, ends = ann.start_s.to_numpy(float), ann.end_s.to_numpy(float)
    if not np.isfinite(np.r_[starts, ends]).all() or np.any(ends <= starts):
        raise ValueError("Annotation intervals must be finite, with end_s > start_s.")
    if not ann.activity.isin(STATES).all() or np.any(starts[1:] < ends[:-1] - 1e-8):
        raise ValueError("Unknown activity or overlapping annotation intervals.")
    if np.any(np.abs(starts[1:] - ends[:-1]) > 1e-6):
        raise ValueError("Mixed annotations must cover time continuously without gaps.")
    if starts[0] > float(row.trim_start_s) + 1e-6 or ends[-1] < float(row.trim_end_s) - 1e-6:
        raise ValueError("Annotations must cover the entire retained interval.")
    return ann


def extract_sequence(frame, ann, rate=50, window_s=2, boundary_guard_s=0):
    n = int(round(rate * window_s))
    if n < 2 or not np.isclose(n, rate * window_s):
        raise ValueError("Window size must correspond to an integer number of sensor rows.")
    values = frame.iloc[:, 1:].to_numpy()
    if not np.isfinite(boundary_guard_s) or boundary_guard_s < 0:
        raise ValueError("Boundary guard must be finite and nonnegative.")
    features, labels, purity, centers, stable = [], [], [], [], []
    for first in range(0, len(frame) - n + 1, n):
        start = float(frame.seconds_elapsed.iloc[first])
        end, center = start + window_s, start + window_s / 2
        at_center = ann.loc[(ann.start_s <= center) & (center < ann.end_s)]
        if len(at_center) != 1:
            raise ValueError("Every window midpoint needs exactly one annotation.")
        label = at_center.iloc[0].activity
        overlap = np.maximum(0, np.minimum(ann.end_s.to_numpy(), end) - np.maximum(ann.start_s.to_numpy(), start))
        if not np.isclose(overlap.sum(), window_s, atol=1e-6):
            raise ValueError("An annotation gap intersects a feature window.")
        features.append(window_features(values[first:first + n], rate))
        labels.append(STATES.index(label))
        purity.append(float(overlap[ann.activity.to_numpy() == label].sum() / window_s))
        centers.append(center)
        # For approximate timings, require the whole window to lie inside an
        # interval's guarded core. This is a sensitivity check, not a confidence bound.
        inside_core = ((ann.start_s.to_numpy() + boundary_guard_s <= start + 1e-8)
                       & (ann.end_s.to_numpy() - boundary_guard_s >= end - 1e-8)
                       & (ann.activity.to_numpy() == label))
        stable.append(bool(inside_core.any()))
    if not features:
        raise ValueError("Recording has no complete feature windows.")
    return dict(X=np.vstack(features), y=np.array(labels), purity=np.array(purity),
                stable=np.array(stable), center_s=np.array(centers))


def build_dataset(root, target_hz=50, window_s=2):
    root = Path(root)
    manifest = pd.read_csv(root / "data/recordings.csv", keep_default_na=False)
    manifest = manifest.loc[manifest.status.eq("recorded")].copy()
    if manifest.recording_id.duplicated().any():
        raise ValueError("Each recording_id must be unique.")
    if not manifest.split.isin(["train", "validation", "test"]).all():
        raise ValueError("Allowed splits: train, validation, test.")
    # A raw file cannot appear in more than one row/split.
    for column in ["accel_file", "gyro_file"]:
        if manifest[column].duplicated().any():
            raise ValueError(f"Repeated {column}: split whole recordings, never reuse raw files.")
    sequences, audit_rows = [], []
    for row in manifest.itertuples(index=False):
        frame, audits = load_recording(root, row, target_hz)
        ann = annotations_for(root, row)
        guard = float(getattr(row, "boundary_guard_s", 0) or 0)
        seq = extract_sequence(frame, ann, target_hz, window_s, guard)
        seq.update(recording_id=row.recording_id, split=row.split, activity=row.activity,
                   session_id=row.session_id, boundary_guard_s=guard,
                   annotation_quality=getattr(row, "annotation_quality", "participant-labelled"))
        sequences.append(seq)
        audit_rows.extend(audits)
        frame["activity"] = [ann.loc[(ann.start_s <= t) & (t < ann.end_s), "activity"].iloc[0]
                             for t in frame.seconds_elapsed]
        out = root / "data/processed"
        out.mkdir(exist_ok=True, parents=True)
        frame.to_csv(out / f"{row.recording_id}_aligned.csv", index=False)
    return sequences, pd.DataFrame(audit_rows)


def fit_scaler(sequences):
    x = np.concatenate([s["X"] for s in sequences])
    mean, scale = x.mean(axis=0), x.std(axis=0)
    return mean, np.where(scale < 1e-10, 1.0, scale)


def apply_scaler(sequences, mean, scale):
    return [dict(s, X=(s["X"] - mean) / scale) for s in sequences]


def logsumexp(x, axis=None):
    x = np.asarray(x)
    m = np.max(x, axis=axis, keepdims=True)
    result = m + np.log(np.exp(x - m).sum(axis=axis, keepdims=True))
    return result.squeeze() if axis is None else np.squeeze(result, axis=axis)


class GaussianHMM:
    """Supervised diagonal-Gaussian HMM with log-space Viterbi and Forward.

    State names are anchored by training labels. Test labels are never used
    for estimation, decoding, or state-name mapping. Baum–Welch is discussed
    in the notebook as an optional unsupervised alternative, not run here.
    """
    def __init__(self, smoothing=1.0, variance_floor=0.1):
        if smoothing <= 0 or variance_floor <= 0:
            raise ValueError("Smoothing and variance_floor must be positive.")
        self.smoothing, self.variance_floor = smoothing, variance_floor

    def fit(self, sequences):
        if not sequences:
            raise ValueError("Training sequences are required.")
        k = len(STATES)
        x = np.concatenate([s["X"] for s in sequences])
        y = np.concatenate([s["y"] for s in sequences])
        pure = np.concatenate([s.get("stable", s["purity"] >= 1 - 1e-6) for s in sequences])
        means, variances = [], []
        for state in range(k):
            selected = x[(y == state) & pure]
            if len(selected) < 2:
                raise ValueError(f"Need at least two pure training windows for {STATES[state]}.")
            means.append(selected.mean(axis=0))
            variances.append(np.maximum(selected.var(axis=0), self.variance_floor))
        self.means_, self.variances_ = np.vstack(means), np.vstack(variances)
        continuous = [s for s in sequences if s["activity"] == "mixed"]
        if not continuous:
            warnings.warn("No mixed training sequence: cross-activity transitions are only smoothing assumptions.")
        transition_sequences = continuous or sequences
        transitions = np.full((k, k), self.smoothing)
        starts = np.full(k, self.smoothing)
        for seq in transition_sequences:
            starts[seq["y"][0]] += 1
            # Never count a transition across independent recording boundaries.
            np.add.at(transitions, (seq["y"][:-1], seq["y"][1:]), 1)
        self.transition_counts_ = transitions - self.smoothing
        self.A_ = transitions / transitions.sum(axis=1, keepdims=True)
        self.pi_ = starts / starts.sum()
        return self

    def log_emissions(self, x):
        x = np.asarray(x)
        if x.ndim != 2 or len(x) == 0 or not np.isfinite(x).all():
            raise ValueError("Observations must be a nonempty finite 2-D array.")
        diff = x[:, None, :] - self.means_[None, :, :]
        return -0.5 * np.sum(np.log(2 * np.pi * self.variances_)[None, :, :]
                             + diff ** 2 / self.variances_[None, :, :], axis=2)

    def decode(self, x):
        """Most likely entire state path; offline, using past and future."""
        b = self.log_emissions(x)
        log_a = np.log(self.A_)
        delta = np.log(self.pi_) + b[0]
        back = np.zeros((len(b), len(STATES)), dtype=int)
        for t in range(1, len(b)):
            candidates = delta[:, None] + log_a
            back[t] = candidates.argmax(axis=0)
            delta = candidates.max(axis=0) + b[t]
        path = np.zeros(len(b), dtype=int)
        path[-1] = delta.argmax()
        for t in range(len(b) - 1, 0, -1):
            path[t - 1] = back[t, path[t]]
        return path

    def score(self, x):
        """Forward algorithm: log P(X), summing over every possible path."""
        b = self.log_emissions(x)
        alpha = np.log(self.pi_) + b[0]
        for emission in b[1:]:
            alpha = emission + logsumexp(alpha[:, None] + np.log(self.A_), axis=0)
        return float(logsumexp(alpha))

    def emission_only(self, x):
        """Diagnostic baseline: classify each window without transitions."""
        return self.log_emissions(x).argmax(axis=1)


def classification_metrics(truth, prediction):
    truth, prediction = np.asarray(truth, int), np.asarray(prediction, int)
    if len(truth) == 0 or truth.shape != prediction.shape:
        raise ValueError("Need equally sized nonempty truth and prediction arrays.")
    cm = np.zeros((len(STATES), len(STATES)), dtype=int)
    np.add.at(cm, (truth, prediction), 1)
    n, correct = int(cm.sum()), int(np.trace(cm))
    rows = []
    for i, name in enumerate(STATES):
        tp = int(cm[i, i]); fn = int(cm[i].sum() - tp); fp = int(cm[:, i].sum() - tp)
        tn = n - tp - fn - fp
        divide = lambda a, b: a / b if b else np.nan
        rows.append({"Activity": name, "Number of Samples": int(cm[i].sum()),
                     "Sensitivity": divide(tp, tp + fn), "Specificity": divide(tn, tn + fp),
                     "Overall Accuracy": correct / n, "One-vs-Rest Accuracy": (tp + tn) / n,
                     "Precision": divide(tp, tp + fp),
                     "F1": divide(2 * tp, 2 * tp + fp + fn),
                     "TP": tp, "FN": fn, "FP": fp, "TN": tn})
    table = pd.DataFrame(rows)
    return table, cm, {"accuracy": correct / n, "macro_f1": float(table.F1.mean()), "n_windows": n}


def evaluate(model, sequences, method="viterbi", pure_only=False, stable_only=False):
    predictions, truth = [], []
    for seq in sequences:
        pred = model.decode(seq["X"]) if method == "viterbi" else model.emission_only(seq["X"])
        mask = seq["purity"] >= 1 - 1e-6 if pure_only else np.ones(len(pred), bool)
        if stable_only:
            mask &= seq.get("stable", seq["purity"] >= 1 - 1e-6)
        predictions.extend(pred[mask]); truth.extend(seq["y"][mask])
    return classification_metrics(truth, predictions)
