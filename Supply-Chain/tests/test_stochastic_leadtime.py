import numpy as np
from scripts.run_simulation import NormalIntLeadTime
import random

def test_normal_int_leadtime_distribution():
    rng = random.Random(123)
    sampler = NormalIntLeadTime(mean=3.0, std=1.0, rng=rng)
    samples = np.array([sampler.sample() for _ in range(1000)])
    assert (samples >= 0).all(), "Negative lead time values detected"
    # Check approximate mean (within 0.5 tolerance)
    assert abs(samples.mean() - 3.0) < 0.5, "Lead time mean out of expected range"
