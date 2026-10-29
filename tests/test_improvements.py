"""Check v2 weighting and feature preparation without using study test data."""
import unittest
import numpy as np

from improve_model import RecordingBalancedHMM, transform_features


class ImprovementChecks(unittest.TestCase):
    def test_recording_balance_is_invariant_to_repeating_a_long_record(self):
        sequences = []
        for state in range(4):
            for name, value in [('long', 0.), ('short', 10.)]:
                sequences.append(dict(recording_id=f'{state}_{name}', X=np.full((4, 2), value),
                                      y=np.full(4, state), purity=np.ones(4), stable=np.ones(4, bool), activity='mixed'))
        original = RecordingBalancedHMM().fit(sequences)
        duplicated = [dict(s, X=np.repeat(s['X'], 30, axis=0), y=np.repeat(s['y'], 30),
                           purity=np.repeat(s['purity'], 30), stable=np.repeat(s['stable'], 30))
                      if s['recording_id'].endswith('long') else s for s in sequences]
        repeated = RecordingBalancedHMM().fit(duplicated)
        np.testing.assert_allclose(original.means_, 5.)
        np.testing.assert_allclose(repeated.means_, original.means_)
        np.testing.assert_allclose(repeated.variances_, original.variances_)

    def test_transform_does_not_change_input_and_preserves_frequency_fraction(self):
        x = np.arange(16, dtype=float).reshape(2, 8)
        original = x.copy()
        actual = transform_features(x, 'compact4', 'log1p')
        np.testing.assert_allclose(actual[:, :3], np.log1p(x[:, [0, 1, 3]]))
        np.testing.assert_array_equal(actual[:, 3], x[:, 5])
        np.testing.assert_array_equal(x, original)


if __name__ == '__main__':
    unittest.main()
