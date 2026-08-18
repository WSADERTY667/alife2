# Genome Specification

## Overview

Genome module implements genetic operations for agents in the ALife simulation. This document describes the genes, bounds, mutation rules, crossover rules, and tag inheritance.

## Gene List

The genome consists of 34 genes that control various aspects of agent behavior, neural network properties, hormone systems, and other characteristics.

### Neural Network Genes

| Gene | Min | Max | Description |
|------|-----|-----|-------------|
| `mutation_rate` | 0.001 | 0.30 | Probability of gene mutation |
| `conn_prob` | 0.02 | 0.25 | Connection probability in neural network |
| `weight_scale` | 0.05 | 1.5 | Scale factor for synaptic weights |
| `weight_max` | 0.5 | 3.0 | Maximum synaptic weight |
| `membrane_decay` | 0.70 | 0.98 | Neuron membrane potential decay |
| `threshold` | 0.5 | 1.8 | Neuron activation threshold |
| `stdp_rate` | 0.0005 | 0.05 | STDP learning rate |
| `plasticity_gain` | 0.1 | 2.5 | Synaptic plasticity gain |

### Dopamine System Genes

| Gene | Min | Max | Description |
|------|-----|-----|-------------|
| `dopamine_base` | 0.2 | 1.0 | Base dopamine level |
| `dopamine_reactivity` | 0.1 | 2.0 | Dopamine response to stimuli |
| `dopamine_decay` | 0.01 | 0.20 | Dopamine decay rate |
| `dopamine_sensitivity` | 0.5 | 2.0 | Dopamine receptor sensitivity |

### Serotonin System Genes

| Gene | Min | Max | Description |
|------|-----|-----|-------------|
| `serotonin_base` | 0.2 | 1.0 | Base serotonin level |
| `serotonin_decay` | 0.01 | 0.20 | Serotonin decay rate |
| `serotonin_sensitivity` | 0.5 | 2.0 | Serotonin receptor sensitivity |

### Oxytocin System Genes

| Gene | Min | Max | Description |
|------|-----|-----|-------------|
| `oxytocin_base` | 0.1 | 0.8 | Base oxytocin level |
| `oxytocin_gain` | 0.1 | 2.0 | Oxytocin production gain |
| `oxytocin_decay` | 0.01 | 0.20 | Oxytocin decay rate |
| `oxytocin_sensitivity` | 0.5 | 2.0 | Oxytocin receptor sensitivity |

### Cortisol System Genes

| Gene | Min | Max | Description |
|------|-----|-----|-------------|
| `cortisol_base` | 0.05 | 0.6 | Base cortisol level |
| `cortisol_reactivity` | 0.1 | 2.0 | Cortisol response to stress |
| `cortisol_decay` | 0.01 | 0.30 | Cortisol decay rate |
| `cortisol_sensitivity` | 0.5 | 2.0 | Cortisol receptor sensitivity |

### Testosterone System Genes

| Gene | Min | Max | Description |
|------|-----|-----|-------------|
| `testosterone_base` | 0.1 | 1.0 | Base testosterone level |
| `testosterone_reactivity` | 0.1 | 2.0 | Testosterone response to stimuli |
| `testosterone_decay` | 0.01 | 0.30 | Testosterone decay rate |
| `testosterone_sensitivity` | 0.5 | 2.0 | Testosterone receptor sensitivity |

### Behavioral Genes

| Gene | Min | Max | Description |
|------|-----|-----|-------------|
| `aggression_gain` | 0.0 | 2.0 | Aggression tendency modifier |
| `social_gain` | 0.0 | 2.0 | Social behavior modifier |
| `lamarckian_weight` | 0.0 | 0.9 | Weight of learned traits in inheritance |
| `metabolism` | 0.01 | 0.10 | Energy consumption rate |

### Architecture Genes

| Gene | Min | Max | Description |
|------|-----|-----|-------------|
| `brain_arch_mutability` | 0.0 | 0.15 | Probability of brain architecture mutation |
| `stress_resilience` | 0.1 | 0.9 | Resistance to stress |
| `social_temperament` | 0.1 | 0.9 | Social temperament trait |

## Mutation Rules

### Gene Mutation

For each gene in the genome:
1. Generate a random number `r` in range [0, 1)
2. If `r < mutation_rate` (clamped to [0, 0.5]):
   - Apply Gaussian mutation: `gene = gene + gauss(0, MUT_SCALE[gene])`
   - Clamp result to gene bounds `[min, max]`

Where `MUT_SCALE[gene] = max(1e-5, (max_bound - min_bound) * 0.08)`

### Tag Mutation

With probability `mutation_rate * 0.35`:
- Assign a new random tag from available tribe colors (0-7)

### Brain Architecture Mutation

With probability `brain_arch_mutability` (clamped to [0, 0.5]):
- Choose delta from `[-8, -4, 4, 8]`
- Update `n_hidden = clamp(n_hidden + delta, 40, 400)`

### Tribal Tags Mutation

With probability `mutation_rate * 0.05`:
- Generate new tribal tag: `"mut_" + random(1000, 9999)`
- Add to tribal_tags list if not already present
- Keep only last 5 tags (FIFO)

## Crossover Rules

### Gene Inheritance

For each gene:
1. Generate random value `r` in [0, 1)
2. If `r < 0.45`: inherit from parent A
3. Else if `r < 0.90`: inherit from parent B
4. Else: average both parents `(a + b) / 2`

### Tag Inheritance

- Randomly choose tag from parent A (50%) or parent B (50%)

### Tribal Tags Inheritance

- Combine unique tags from both parents
- Keep first 5 tags maximum

### Brain Architecture Inheritance

1. Calculate average: `n_hidden = int((a.n_hidden + b.n_hidden) / 2)`
2. Add variation from `[-4, 0, 0, 0, 4]` (weighted towards 0)
3. Clamp to `[40, 400]`

## Tag Inheritance

### Visual Tag (`tag`)

- Single integer from 0 to 7 representing tribe color
- Inherited from one parent with equal probability
- Can mutate during mutation phase

### Tribal Tags (`tribal_tags`)

- List of string markers inherited along family line
- Combined from both parents during crossover
- Maximum 5 tags maintained (oldest removed first)
- New tags can be added through rare mutations

### Architecture (`n_hidden`)

- Integer representing number of hidden neurons
- Default value: 160
- Valid range: [40, 400]
- Inherited as average with small variation

## Genome Similarity

Similarity between two genomes is calculated as weighted combination:

```
similarity = 0.5 * gene_sim + 0.15 * tag_sim + 0.2 * tag_overlap + 0.15 * arch_sim
```

Where:
- `gene_sim`: Average similarity of KIN_KEYS genes (normalized by bounds)
- `tag_sim`: 1.0 if visual tags match, 0.0 otherwise
- `tag_overlap`: Fraction of shared tribal tags
- `arch_sim`: 1.0 - |n_hidden_diff| / 200 (clamped to [0, 1])

### KIN_KEYS (genes used for similarity calculation)

- `conn_prob`
- `threshold`
- `dopamine_base`
- `serotonin_base`
- `oxytocin_gain`
- `cortisol_decay`
- `aggression_gain`
- `social_gain`
- `cortisol_sensitivity`
- `oxytocin_sensitivity`

## Determinism

All operations use a deterministic RNG (SplitMix64) to ensure reproducibility:
- Same seed produces identical genome creation
- Same seed produces identical crossover results
- Same seed produces identical mutation results

## Implementation Files

- `cpp/include/alife/genome.h` - Header file with class definition
- `cpp/src/genome.cpp` - Implementation file
- `cpp/tests/test_genome.cpp` - Unit tests
- `tools/export_genome_golden.py` - Golden data export tool

## Testing

Run tests with:
```bash
cd cpp/build
ctest --output-on-failure
```

Generate golden data with:
```bash
python3 tools/export_genome_golden.py
```
