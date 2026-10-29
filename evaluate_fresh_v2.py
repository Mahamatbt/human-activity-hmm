"""One-pass evaluation of the frozen v2 HMM on four new labelled recordings.

No fitting, feature selection, or parameter tuning occurs here. Each recording
is decoded separately so artificial transitions between files cannot arise.
"""
from pathlib import Path
import hashlib
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from activity_hmm import STATES, annotations_for, classification_metrics, extract_sequence, load_recording
from improve_model import decode_v2


ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "results/improvement_v2/selected_hmm_v2.npz"
OUT = ROOT / "results/fresh_test_v2"


def run_evaluation():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(MODEL_PATH)
    model_hash = hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest()
    manifest = pd.read_csv(ROOT / "data/fresh_test_v2_recordings.csv", keep_default_na=False)
    if set(manifest.activity) != set(STATES) or len(manifest) != 4:
        raise ValueError("Exactly one new recording for each of four activities is required.")
    if not manifest.split.eq("fresh_test_v2").all():
        raise ValueError("Only the separate fresh v2 test files can be scored here.")
    OUT.mkdir(parents=True, exist_ok=True)
    all_truth, all_pred, rows, audit_rows = [], [], [], []
    sequences = []
    for row in manifest.itertuples(index=False):
        frame, audits = load_recording(ROOT, row, target_hz=50)
        seq = extract_sequence(frame, annotations_for(ROOT, row), rate=50, window_s=2)
        prediction = decode_v2(seq["X"], MODEL_PATH)
        truth = seq["y"]
        all_truth.extend(truth); all_pred.extend(prediction)
        audit_rows.extend(audits)
        for i, (actual, predicted) in enumerate(zip(truth, prediction)):
            rows.append(dict(recording_id=row.recording_id, center_s=float(seq["center_s"][i]),
                             actual_activity=STATES[actual], predicted_activity=STATES[predicted],
                             correct=bool(actual == predicted)))
        sequences.append((row.activity, seq["center_s"], truth, prediction))
        aligned_path = ROOT / "data/processed" / f"{row.recording_id}_aligned.csv"
        aligned_path.parent.mkdir(parents=True, exist_ok=True)
        frame.assign(activity=row.activity).to_csv(aligned_path, index=False)
    table, confusion, scores = classification_metrics(all_truth, all_pred)
    table.to_csv(OUT / "test_metrics.csv", index=False)
    pd.DataFrame(rows).to_csv(OUT / "test_predictions.csv", index=False)
    pd.DataFrame(audit_rows).to_csv(OUT / "sampling_audit.csv", index=False)
    pd.DataFrame(confusion, index=STATES, columns=STATES).to_csv(OUT / "confusion_matrix.csv")
    summary = dict(model="frozen compact4_log1p_window v2", model_sha256=model_hash,
                   evaluated_split="fresh_test_v2", source_recordings=manifest.source_zip.tolist(),
                   same_participant=True, same_phone=True, same_date=True,
                   independent_single_activity_recordings=4,
                   n_windows=scores["n_windows"], accuracy=scores["accuracy"],
                   macro_f1=scores["macro_f1"], correct_windows=int(np.trace(confusion)),
                   changes_to_model_after_test=0,
                   interpretation="New recordings were held out from v2 model selection. Four separate single-activity files test state recognition, not transitions within a continuous run. Windows within each file are correlated.")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    fig, axes = plt.subplots(4, 1, figsize=(10, 6.4), sharey=True)
    for ax, (name, centers, truth, pred) in zip(axes, sequences):
        ax.step(centers, truth, where="mid", linewidth=2.5, color="#204a65", label="Recorded activity")
        ax.step(centers, pred, where="mid", linewidth=2.0, color="#d46a28", label="Viterbi prediction")
        ax.set(title=f"{name.title()} recording", xlabel="Seconds since Start", xlim=(0, max(centers) + 2),
               yticks=range(4), yticklabels=[s.title() for s in STATES], ylim=(-0.3, 3.3))
        ax.grid(alpha=0.2)
    axes[0].legend(loc="upper right", fontsize=8)
    fig.suptitle("Frozen v2 HMM: new single-activity recordings")
    fig.tight_layout(); fig.savefig(OUT / "decoded_sequences.png", dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    im = ax.imshow(confusion, cmap="Blues", vmin=0)
    ax.set(xticks=range(4), xticklabels=[s.title() for s in STATES],
           yticks=range(4), yticklabels=[s.title() for s in STATES],
           xlabel="Predicted", ylabel="Recorded", title="Fresh v2 test confusion matrix")
    for i in range(4):
        for j in range(4):
            ax.text(j, i, str(confusion[i, j]), ha="center", va="center",
                    color="white" if confusion[i, j] > confusion.max() / 2 else "#17354A")
    fig.colorbar(im, ax=ax, shrink=0.85)
    fig.tight_layout(); fig.savefig(OUT / "confusion_matrix.png", dpi=180); plt.close(fig)
    return summary, table, confusion


if __name__ == "__main__":
    summary, table, confusion = run_evaluation()
    print(json.dumps(summary, indent=2))
    print(table.to_string(index=False))
    print(confusion)
