"""Implementation checks only. Temporary synthetic fixtures are NOT project data."""
from itertools import product
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from activity_hmm import (
    STATES, GaussianHMM, _spectrum, apply_scaler, build_dataset,
    classification_metrics, evaluate, fit_scaler,
    extract_sequence,
)


class AlgorithmChecks(unittest.TestCase):
    def test_guard_excludes_estimated_interval_edges(self):
        t = np.arange(1000) / 50
        frame = pd.DataFrame(np.zeros((1000, 6)), columns=['ax','ay','az','gx','gy','gz'])
        frame.insert(0, 'seconds_elapsed', t)
        ann = pd.DataFrame(dict(start_s=[0,10], end_s=[10,20], activity=['standing','walking']))
        seq = extract_sequence(frame, ann, boundary_guard_s=2)
        np.testing.assert_array_equal(seq['stable'], [False,True,True,True,False,False,True,True,True,False])

    def test_viterbi_and_forward_against_exhaustive_paths(self):
        model = GaussianHMM()
        model.pi_ = np.array([0.4, 0.3, 0.2, 0.1])
        model.A_ = np.full((4, 4), 0.1) + np.eye(4) * 0.6
        model.means_ = np.array([[-2., 0.], [0., 2.], [2., 0.], [0., -2.]])
        model.variances_ = np.full((4, 2), 0.8)
        x = np.array([[-1.8, 0.2], [-0.2, 1.7], [0.1, 2.1], [1.8, 0.1]])
        log_paths, paths = [], list(product(range(4), repeat=len(x)))
        for path in paths:
            probability = model.pi_[path[0]]
            for t, state in enumerate(path):
                probability *= np.prod(np.exp(-(x[t] - model.means_[state]) ** 2 / (2 * model.variances_[state]))
                                       / np.sqrt(2 * np.pi * model.variances_[state]))
                if t:
                    probability *= model.A_[path[t-1], state]
            log_paths.append(np.log(probability))
        np.testing.assert_array_equal(model.decode(x), paths[int(np.argmax(log_paths))])
        self.assertAlmostEqual(model.score(x), np.log(np.exp(log_paths).sum()), places=10)

    def test_no_transition_across_recording_boundaries(self):
        sequences = []
        for state in range(4):
            sequences.append(dict(X=np.full((4, 2), state, float), y=np.full(4, state),
                                  purity=np.ones(4), activity='mixed'))
        model = GaussianHMM().fit(sequences)
        np.testing.assert_array_equal(model.transition_counts_, np.eye(4) * 3)
        np.testing.assert_allclose(model.A_.sum(axis=1), 1)
        self.assertAlmostEqual(model.pi_.sum(), 1)

    def test_spectral_scaling_even_and_odd_lengths(self):
        rng = np.random.default_rng(3)
        for n in [99, 100]:
            signal = rng.normal(size=n)
            _, _, power = _spectrum(signal, 50)
            self.assertAlmostEqual(power, np.var(signal), places=12)
        t = np.arange(100) / 50
        peak, _, _ = _spectrum(np.sin(2 * np.pi * 2 * t), 50)
        self.assertEqual(peak, 2)

    def test_hand_calculated_metrics(self):
        table, _, scores = classification_metrics([0, 0, 1, 1, 2, 2, 3, 3], [0, 1, 1, 1, 2, 3, 3, 0])
        self.assertEqual(scores['accuracy'], 5/8)
        self.assertEqual(table.iloc[0]['Sensitivity'], 1/2)
        self.assertEqual(table.iloc[0]['Specificity'], 5/6)
        self.assertEqual(table.iloc[0]['Number of Samples'], 2)
        self.assertEqual(table.iloc[0]['One-vs-Rest Accuracy'], 6/8)


def make_temporary_fixture(root):
    """Create plausible-shaped signals solely to exercise file/sequence plumbing."""
    root = Path(root)
    (root / 'data/annotations').mkdir(parents=True, exist_ok=True)
    rows = []
    rng = np.random.default_rng(12)
    for split in ['train', 'validation', 'test']:
        for activity in [*STATES, 'mixed']:
            rid = f'fixture_{split}_{activity}'
            folder = root / 'data/raw' / rid
            folder.mkdir(parents=True)
            end = 34 if activity == 'mixed' else 10
            if activity == 'mixed':
                annotations = pd.DataFrame(dict(start_s=[2, 10, 18, 26], end_s=[10, 18, 26, 34], activity=STATES))
                annotations.to_csv(root / 'data/annotations' / f'{rid}.csv', index=False)
            for sensor, rate in [('Accelerometer', 100), ('Gyroscope', 80)]:
                t = np.arange(0, end + 2, 1/rate)
                labels = np.clip(((t - 2) // 8).astype(int), 0, 3) if activity == 'mixed' else np.full(len(t), STATES.index(activity))
                amplitude = np.array([0.03, 1., 4., 0.001])[labels]
                frequency = np.array([0.6, 1.5, 2.5, 0.5])[labels]
                scale = 1 if sensor == 'Accelerometer' else 0.2
                values = np.column_stack([
                    scale * amplitude * np.sin(2*np.pi*frequency*t + offset) for offset in [0, 0.5, 1.0]
                ]) + rng.normal(0, 0.0001, (len(t), 3))
                pd.DataFrame(dict(seconds_elapsed=t, x=values[:,0], y=values[:,1], z=values[:,2])).to_csv(folder / f'{sensor}.csv', index=False)
            rows.append(dict(recording_id=rid, session_id=f'fixture_session_{split}',
                             split=split, activity=activity, status='recorded',
                             accel_file=f'data/raw/{rid}/Accelerometer.csv', gyro_file=f'data/raw/{rid}/Gyroscope.csv',
                             annotation_file=f'data/annotations/{rid}.csv' if activity == 'mixed' else '',
                             trim_start_s=2, trim_end_s=end, requested_rate_hz=100))
    pd.DataFrame(rows).to_csv(root / 'data/recordings.csv', index=False)


class PipelineChecks(unittest.TestCase):
    def test_different_sensor_rates_to_features_and_decoding(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_temporary_fixture(tmp)
            sequences, audit = build_dataset(tmp)
            self.assertEqual(len(sequences), 15)
            self.assertEqual(len(audit), 30)
            self.assertTrue(np.allclose(audit.resampled_rate_hz, 50))
            train = [s for s in sequences if s['split'] == 'train']
            test = [s for s in sequences if s['split'] == 'test']
            mean, scale = fit_scaler(train)
            model = GaussianHMM().fit(apply_scaler(train, mean, scale))
            table, cm, scores = evaluate(model, apply_scaler(test, mean, scale))
            self.assertEqual(cm.sum(), 32)
            self.assertEqual(table['Number of Samples'].sum(), 32)
            self.assertGreater(scores['accuracy'], 0.8)
            aligned = pd.read_csv(Path(tmp) / 'data/processed/fixture_train_standing_aligned.csv')
            np.testing.assert_allclose(np.diff(aligned.seconds_elapsed), 1/50)
            self.assertEqual(set(aligned.activity), {'standing'})


if __name__ == '__main__':
    unittest.main()
