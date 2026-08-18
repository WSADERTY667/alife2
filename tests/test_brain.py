import numpy as np
from alife.genome import Genome
from alife.brain import Brain
from alife.config import OUTPUT_SIZE


def test_brain_step_returns_correct_size():
    genome = Genome()
    brain = Brain(genome, n_hidden=16)
    sensors = np.zeros(12, dtype=np.float32)
    mod = {"arousal": 0.0, "plasticity": 0.0, "dopamine": 0.0}
    out = brain.step(sensors, mod)
    assert len(out) == OUTPUT_SIZE


def test_brain_no_nan_after_steps():
    genome = Genome()
    brain = Brain(genome, n_hidden=16)
    for i in range(100):
        sensors = np.random.rand(12).astype(np.float32)
        mod = {
            "arousal": np.random.rand(),
            "plasticity": np.random.rand(),
            "dopamine": np.random.rand() * 2 - 1,
        }
        brain.step(sensors, mod)
    assert not np.any(np.isnan(brain.W))
    assert not np.any(np.isnan(brain.v))
    assert not np.any(np.isnan(brain.out_rate))
