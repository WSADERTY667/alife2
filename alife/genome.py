# genome.py
# Геном агента и генетические операции
import random
from .config import TAG_COLORS, clamp

GENOME_KEYS = [
    "mutation_rate", "conn_prob", "weight_scale", "weight_max",
    "membrane_decay", "threshold", "stdp_rate", "plasticity_gain",
    "dopamine_base", "dopamine_reactivity",
    "serotonin_base", "serotonin_decay",
    "oxytocin_base", "oxytocin_gain",
    "cortisol_base", "cortisol_reactivity", "cortisol_decay",
    "testosterone_base", "testosterone_reactivity",
    "aggression_gain", "social_gain",
    "lamarckian_weight", "metabolism",
]

BOUNDS = {
    "mutation_rate": (0.001, 0.30),
    "conn_prob": (0.02, 0.25),
    "weight_scale": (0.05, 1.5),
    "weight_max": (0.5, 3.0),
    "membrane_decay": (0.70, 0.98),
    "threshold": (0.5, 1.8),
    "stdp_rate": (0.0005, 0.05),
    "plasticity_gain": (0.1, 2.5),
    "dopamine_base": (0.2, 1.0),
    "dopamine_reactivity": (0.1, 2.0),
    "serotonin_base": (0.2, 1.0),
    "serotonin_decay": (0.01, 0.20),
    "oxytocin_base": (0.1, 0.8),
    "oxytocin_gain": (0.1, 2.0),
    "cortisol_base": (0.05, 0.6),
    "cortisol_reactivity": (0.1, 2.0),
    "cortisol_decay": (0.01, 0.30),
    "testosterone_base": (0.1, 1.0),
    "testosterone_reactivity": (0.1, 2.0),
    "aggression_gain": (0.0, 2.0),
    "social_gain": (0.0, 2.0),
    "lamarckian_weight": (0.0, 0.9),
    "metabolism": (0.01, 0.10),
}

MUT_SCALE = {
    k: max(1e-5, (BOUNDS[k][1] - BOUNDS[k][0]) * 0.08)
    for k in GENOME_KEYS
}

KIN_KEYS = [
    "conn_prob", "threshold",
    "dopamine_base", "serotonin_base",
    "oxytocin_gain", "cortisol_decay",
    "aggression_gain", "social_gain",
]


class Genome:
    def __init__(self, genes=None, tag=None):
        if genes is None:
            genes = {
                k: random.uniform(BOUNDS[k][0], BOUNDS[k][1])
                for k in GENOME_KEYS
            }
        self.genes = genes
        if tag is None:
            self.tag = random.randint(0, len(TAG_COLORS) - 1)
        else:
            self.tag = tag

    def __getitem__(self, key):
        return self.genes[key]

    def mutate(self):
        mr = clamp(self.genes.get("mutation_rate", 0.08), 0.0, 0.5)
        for k in GENOME_KEYS:
            if random.random() < mr:
                self.genes[k] = clamp(
                    self.genes[k] + random.gauss(0.0, MUT_SCALE[k]),
                    BOUNDS[k][0], BOUNDS[k][1],
                )
        if random.random() < mr * 0.35:
            self.tag = random.randint(0, len(TAG_COLORS) - 1)

    @staticmethod
    def crossover(a, b):
        genes = {}
        for k in GENOME_KEYS:
            r = random.random()
            if r < 0.45:
                v = a[k]
            elif r < 0.90:
                v = b[k]
            else:
                v = (a[k] + b[k]) * 0.5
            genes[k] = v
        tag = a.tag if random.random() < 0.5 else b.tag
        return Genome(genes, tag)


def genome_similarity(g1, g2):
    total = 0.0
    for k in KIN_KEYS:
        lo, hi = BOUNDS[k]
        rng = max(1e-6, hi - lo)
        total += abs(g1[k] - g2[k]) / rng
    gene_sim = 1.0 - clamp(total / len(KIN_KEYS), 0.0, 1.0)
    tag_sim = 1.0 if g1.tag == g2.tag else 0.0
    return clamp(0.7 * gene_sim + 0.3 * tag_sim, 0.0, 1.0)
