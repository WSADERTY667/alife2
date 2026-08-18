from alife.genome import Genome, GENOME_KEYS, BOUNDS


def test_genome_random_created():
    g = Genome()
    for key in GENOME_KEYS:
        assert key in g.genes


def test_genome_mutation_keeps_bounds():
    g = Genome()
    for _ in range(100):
        g.mutate()
    for key in GENOME_KEYS:
        lo, hi = BOUNDS[key]
        assert lo <= g[key] <= hi
