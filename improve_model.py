"""Development-only HMM comparison. Does not read or score test recordings.

The original exposed test result is historical. V2 requires a fresh, independently
timed test after selecting/fixing this development model.
"""
from pathlib import Path
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from activity_hmm import (
    STATES, FEATURE_NAMES, GaussianHMM, annotations_for, extract_sequence,
    fit_scaler, apply_scaler, evaluate,
)

FEATURE_SETS = {"all8": tuple(range(8)), "compact4": (0, 1, 3, 5)}
LOG_COLUMNS = (0, 1, 2, 3, 6)


class RecordingBalancedHMM(GaussianHMM):
    """Give each training recording equal emission weight within a state.

    This ablation checks whether one long recording dominates a shorter run.
    Transitions and starts retain the base model's continuous-training counts.
    """
    def fit(self, sequences):
        super().fit(sequences)
        for state in range(len(STATES)):
            groups = {}
            for index, seq in enumerate(sequences):
                mask = (seq["y"] == state) & seq.get("stable", seq["purity"] >= 1 - 1e-6)
                if mask.any():
                    key = seq.get("recording_id", index)
                    groups.setdefault(key, []).append(seq["X"][mask])
            pieces = [np.concatenate(parts) for parts in groups.values()]
            mean = np.mean([part.mean(axis=0) for part in pieces], axis=0)
            variance = np.mean([np.mean((part - mean) ** 2, axis=0) for part in pieces], axis=0)
            self.means_[state] = mean
            self.variances_[state] = np.maximum(variance, self.variance_floor)
        return self


def transform_features(x, feature_set, transform):
    x = np.array(x, dtype=float, copy=True)
    if x.ndim != 2 or x.shape[1] != len(FEATURE_NAMES) or not np.isfinite(x).all():
        raise ValueError("Expected finite rows of the original eight features.")
    if transform not in {"raw", "log1p"} or feature_set not in FEATURE_SETS:
        raise ValueError("Unknown feature set or transform.")
    if transform == "log1p":
        if (x[:, LOG_COLUMNS] < 0).any():
            raise ValueError("Magnitude/power features must be nonnegative.")
        x[:, LOG_COLUMNS] = np.log1p(x[:, LOG_COLUMNS])
    return x[:, FEATURE_SETS[feature_set]]


def load_development_sequences(root):
    """Read only train/validation aligned files; never open a test sensor file."""
    root = Path(root)
    manifest = pd.read_csv(root / "data/recordings.csv", keep_default_na=False)
    development = manifest.loc[manifest.split.isin(["train", "validation"]) & manifest.status.eq("recorded")]
    sequences = []
    for row in development.itertuples(index=False):
        path = root / "data/processed" / f"{row.recording_id}_aligned.csv"
        frame = pd.read_csv(path)
        columns = ["seconds_elapsed", "acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z"]
        if not np.allclose(np.diff(frame.seconds_elapsed), 1 / 50):
            raise ValueError(f"{path}: expected the existing 50 Hz aligned cache.")
        seq = extract_sequence(frame[columns], annotations_for(root, row),
                               boundary_guard_s=float(row.boundary_guard_s or 0))
        seq.update(recording_id=row.recording_id, split=row.split, activity=row.activity)
        sequences.append(seq)
    if not sequences or not any(s["split"] == "validation" for s in sequences):
        raise ValueError("Training and validation recordings are required.")
    return sequences


def decode_v2(raw_eight_features, artifact_path):
    """Decode new features with the frozen transform/scaler/model, without fitting."""
    with np.load(artifact_path, allow_pickle=False) as artifact:
        feature_set = str(artifact["feature_set"].item())
        transform = str(artifact["transform"].item())
        x = transform_features(raw_eight_features, feature_set, transform)
        x = (x - artifact["scaler_mean"]) / artifact["scaler_scale"]
        model = GaussianHMM(smoothing=0.1, variance_floor=0.05)
        model.A_, model.pi_ = artifact["A"].copy(), artifact["pi"].copy()
        model.means_, model.variances_ = artifact["means"].copy(), artifact["variances"].copy()
    return model.decode(x)


def run_comparison(root):
    root = Path(root)
    output = root / "results/improvement_v2"
    output.mkdir(parents=True, exist_ok=True)
    development = load_development_sequences(root)
    train_original = [s for s in development if s["split"] == "train"]
    validation_original = [s for s in development if s["split"] == "validation"]
    rows, fitted = [], {}
    # A small factorial ablation, not an open-ended search over the test score.
    # Keep transition smoothing/floor fixed to the baseline validation choice.
    for feature_set in ["all8", "compact4"]:
        for transform in ["raw", "log1p"]:
            train = [dict(s, X=transform_features(s["X"], feature_set, transform)) for s in train_original]
            validation = [dict(s, X=transform_features(s["X"], feature_set, transform)) for s in validation_original]
            mean, scale = fit_scaler(train)
            scaled_train, scaled_validation = apply_scaler(train, mean, scale), apply_scaler(validation, mean, scale)
            for weighting in ["window", "recording"]:
                estimator = RecordingBalancedHMM if weighting == "recording" else GaussianHMM
                model = estimator(smoothing=0.1, variance_floor=0.05).fit(scaled_train)
                table, confusion, scores = evaluate(model, scaled_validation)
                _, _, stable_scores = evaluate(model, scaled_validation, stable_only=True)
                identifier = f"{feature_set}_{transform}_{weighting}"
                rows.append(dict(candidate=identifier, features=feature_set, transform=transform,
                                 weighting=weighting, n_features=len(FEATURE_SETS[feature_set]),
                                 accuracy=scores["accuracy"], macro_f1=scores["macro_f1"],
                                 n_windows=scores["n_windows"], stable_core_accuracy=stable_scores["accuracy"],
                                 weighting_complexity=int(weighting == "recording")))
                fitted[identifier] = (model, mean, scale, scaled_validation, table, confusion)
    # Among ties, prefer fewer features and the standard unweighted estimator.
    comparison = pd.DataFrame(rows).sort_values(
        ["macro_f1", "accuracy", "n_features", "weighting_complexity"],
        ascending=[False, False, True, True], kind="stable").reset_index(drop=True)
    comparison.drop(columns="weighting_complexity").to_csv(output / "validation_comparison.csv", index=False)
    selected = comparison.iloc[0]
    model, mean, scale, validation, table, confusion = fitted[selected.candidate]
    table.to_csv(output / "selected_validation_metrics.csv", index=False)
    selected_names = [FEATURE_NAMES[i] for i in FEATURE_SETS[selected.features]]
    np.savez(output / "selected_hmm_v2.npz", A=model.A_, pi=model.pi_,
             means=model.means_, variances=model.variances_,
             scaler_mean=mean, scaler_scale=scale,
             feature_set=np.array(selected.features), transform=np.array(selected["transform"]),
             selected_feature_names=np.array(selected_names), states=np.array(STATES))
    info = dict(status="development model; awaiting fresh independently timed test",
                selected_candidate=selected.candidate, feature_names=selected_names,
                feature_set=selected.features, transform=selected["transform"],
                emission_weighting=selected.weighting, smoothing=0.1, variance_floor=0.05,
                validation_accuracy=float(selected.accuracy), validation_macro_f1=float(selected.macro_f1),
                n_validation_windows=int(selected.n_windows),
                annotation_quality="Existing validation intervals remain approximate",
                test_files_loaded=0, test_predictions_computed=0,
                historical_test_accuracy_is_not_v2_accuracy=True,
                loaded_recording_ids=[s["recording_id"] for s in development],
                selection_rule="validation macro-F1, then accuracy, fewer features, standard fit")
    (output / "selection.json").write_text(json.dumps(info, indent=2) + "\n")
    prediction_rows = []
    for seq in validation:
        predictions = model.decode(seq["X"])
        for index, prediction in enumerate(predictions):
            prediction_rows.append(dict(recording_id=seq["recording_id"], center_s=float(seq["center_s"][index]),
                                        approximate_reference=STATES[seq["y"][index]], prediction=STATES[prediction],
                                        stable_core=bool(seq["stable"][index])))
    pd.DataFrame(prediction_rows).to_csv(output / "selected_validation_predictions.csv", index=False)
    fig, ax = plt.subplots(figsize=(10, 4.8))
    plot = comparison.iloc[::-1]
    ax.barh(plot.candidate, plot.accuracy * 100, color="steelblue")
    for y, value in enumerate(plot.accuracy):
        ax.text(value * 100 + 1, y, f"{value * 100:.1f}%", va="center", fontsize=9)
    ax.set(xlim=(0, 105), xlabel="Validation accuracy (%)", ylabel="Feature set / transform / emission weighting",
           title="Eight development-only HMM comparisons: 21 approximately labelled validation windows")
    fig.tight_layout(); fig.savefig(output / "validation_comparison.png", dpi=180); plt.close(fig)
    return comparison.drop(columns="weighting_complexity"), info


if __name__ == "__main__":
    comparison, info = run_comparison(Path(__file__).resolve().parent)
    print(comparison.to_string(index=False))
    print(json.dumps(info, indent=2))
