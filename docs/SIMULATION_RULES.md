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
python3 tools/export_hormones_golden.py
```

---

# Hormone System Specification

## Overview

The hormone system implements a neurochemical model for agents in the ALife simulation. This document describes the hormones, events that affect them, update rules, clamp bounds, and conditions for depression and breakdown states.

## Hormone List

| Hormone | Symbol | Min | Max | Description |
|---------|--------|-----|-----|-------------|
| Dopamine | D | 0.0 | 2.0 | Reward/motivation signal |
| Serotonin | S | 0.0 | 2.0 | Mood/well-being regulator |
| Oxytocin | O | 0.0 | 2.0 | Social bonding hormone |
| Cortisol | C | 0.0 | 2.0 | Stress hormone |
| Testosterone | T | 0.0 | 2.0 | Aggression/dominance hormone |

## Additional States

| State | Min | Max | Description |
|-------|-----|-----|-------------|
| `allostatic` | 0.0 | ∞ | Accumulated damage from chronic stress |
| `depression` | 0.0 | 1.0 | Low mood/motivation state |
| `breakdown` | 0.0 | 1.0 | Critical state after excessive stress |
| `paranoia` | 0.0 | 1.0 | Distrust of surroundings |
| `trust` | 0.0 | 1.0 | Tendency for social interaction |
| `delayed_punishment` | 0.0 | 1.0 | Trace from past negative events |

## Events Affecting Hormones

The `update()` function accepts the following events:

| Event | Description | Affected Hormones |
|-------|-------------|-------------------|
| `reward` | Positive reinforcement | D (+), S (+) |
| `punishment` | Negative reinforcement | D (-), C (+), S (- via delayed) |
| `social` | Social interaction | O (+), paranoia (-) |
| `kin` | Kinship interaction | O (+) |
| `conflict` | Conflict situation | C (+), T (+) |
| `dominance` | Dominance display | T (+) |
| `hunger` | Hunger level | C (+), S (-) |
| `injury` | Physical injury | C (+) |
| `fear` | Fear stimulus | C (+), paranoia (+) |

## Update Rules

### Dopamine (D)
```
D += dopamine_reactivity * (reward - punishment) * 0.25 * D_sensitivity
     + D_decay * (dopamine_base - D)
D = clamp(D, 0.0, 2.0)
```

### Cortisol (C)
```
resilience_factor = 1.0 - stress_resilience * 0.4
stress = (punishment * 1.0 + conflict * 0.6 + hunger * 0.35 + injury * 0.9 + fear * 0.8) * resilience_factor
C += cortisol_reactivity * stress * 0.12 * C_sensitivity
     - C_decay * (C - cortisol_base)
C = clamp(C, 0.0, 2.0)
```

### Serotonin (S)
```
S += S_decay * (serotonin_base - S) * S_sensitivity
     + reward * 0.03
     - max(0.0, C - 0.8) * 0.05
     - delayed_punishment * 0.02
S = clamp(S, 0.0, 2.0)
```

### Oxytocin (O)
```
social_temper = social_temperament
O += oxytocin_gain * (social * 0.06 + kin * 0.08) * O_sensitivity * (0.7 + social_temper * 0.6)
     - O_decay * (O - oxytocin_base)
O = clamp(O, 0.0, 2.0)
```

### Testosterone (T)
```
T += testosterone_reactivity * (conflict * 0.08 + dominance * 0.05) * T_sensitivity
     - T_decay * (T - testosterone_base)
T = clamp(T, 0.0, 2.0)
```

### Delayed Punishment
Punishments > 0.1 are stored in history and decay over time (max age 50.0):
```
delayed_effect = average(p * max(0.1, 1.0 - age/50.0) for all active punishments)
delayed_punishment = clamp(delayed_effect, 0.0, 1.0)
```

### Allostatic Load
```
if C > 0.85:
    allostatic += (C - 0.85) * 0.03 * (1.0 - stress_resilience * 0.3)
else:
    allostatic = max(0.0, allostatic - 0.004)
```

### Breakdown
```
if allostatic > 1.8:
    breakdown = min(1.0, breakdown + 0.01)
else:
    breakdown = max(0.0, breakdown - 0.006)
```

### Depression
```
low_S_threshold = 0.30 * (2.0 - S_sensitivity)
low_D_threshold = 0.35 * (2.0 - D_sensitivity)
if S < low_S_threshold and D < low_D_threshold:
    depression = min(1.0, depression + 0.004 * (1.0 + delayed_punishment))
else:
    recovery_rate = 0.002 * (1.0 + O * 0.3)
    depression = max(0.0, depression - recovery_rate)
```

### Paranoia
```
paranoia_triggers = punishment * 0.4 + C * 0.2 + fear * 0.3
if paranoia_triggers > 0.3:
    paranoia = min(1.0, paranoia + 0.003 * paranoia_triggers)
else:
    paranoia_reduction = (O * 0.3 + social * 0.2) * (1.0 - paranoia)
    paranoia = max(0.0, paranoia - paranoia_reduction * 0.005)
```

### Trust
```
trust_boost = (O * 0.4 + S * 0.2 + reward * 0.1) * (1.0 - trust)
trust_decline = (punishment * 0.3 + paranoia * 0.4) * trust
trust = clamp(trust + (trust_boost - trust_decline) * 0.01, 0.0, 1.0)
```

## Clamp Rules

All hormones and states are clamped after each update:

| Variable | Min | Max |
|----------|-----|-----|
| D, S, O, C, T | 0.0 | 2.0 |
| depression, breakdown, paranoia, trust, delayed_punishment | 0.0 | 1.0 |
| allostatic | 0.0 | ∞ (no upper bound) |

## Conditions for Depression and Breakdown

### Depression
Depression develops when BOTH conditions are met:
- Serotonin below threshold: `S < 0.30 * (2.0 - S_sensitivity)`
- Dopamine below threshold: `D < 0.35 * (2.0 - D_sensitivity)`

Recovery occurs when at least one hormone is above its threshold, with rate boosted by oxytocin.

### Breakdown
Breakdown occurs when allostatic load exceeds critical level:
- `allostatic > 1.8`

Recovery occurs when allostatic load drops below 1.8.

## Effects Calculation

The `effects()` function returns derived behavioral modifiers:

| Effect | Formula Components | Range |
|--------|-------------------|-------|
| `arousal` | 0.15 + C_eff*0.55 + T_eff*0.25 - S_eff*0.15 + hunger*0.20 | [-1.0, 2.0] |
| `plasticity` | plasticity_gain * (0.15 + max(0, dopamine_error)*1.8) * (1 - min(0.75, C_eff*0.35)) | [0.0, 3.0] |
| `aggression` | aggression_gain * (T_eff*0.55 + C_eff*0.35 - S_eff*0.25 + hunger*0.20) * paranoia_factor * distrust_factor | [0.0, 3.0] |
| `sociality` | social_gain * (O_eff*0.85 + S_eff*0.10 - C_eff*0.20) * trust_factor * paranoia_penalty | [0.0, 3.0] |
| `dopamine_signal` | clamp((D - dopamine_base) * 1.5, -1.0, 1.0) | [-1.0, 1.0] |

Where:
- `X_eff = X * X_sensitivity` for each hormone
- `paranoia_factor = 1.0 + paranoia * 0.5`
- `distrust_factor = 1.0 + (1.0 - trust) * 0.3`
- `trust_factor = trust * 0.7 + 0.3`
- `paranoia_penalty = 1.0 - paranoia * 0.6`

Plasticity is reduced by 55% if depression > 0.5, and by 80% if breakdown > 0.5.

## Mood States

The `get_mood()` function returns current emotional state based on hormone levels:

| Condition | Mood |
|-----------|------|
| breakdown > 0.5 | "ярость" (rage) |
| depression > 0.5 | "грусть" (sadness) |
| paranoia > 0.7 | "подозрительность" (suspicion) |
| D < 0.3 and S < 0.3 and O < 0.3 | "отрешённость" (detachment) |
| C > 0.8 and S < 0.4 | "отрешённость" (detachment) |
| D > 0.7 and S > 0.6 | "радость" (joy) |
| D < 0.4 and C < 0.4 and T < 0.4 | "скука" (boredom) |
| C > 0.7 and T > 0.6 and S < 0.5 | "ярость" (rage) |
| trust > 0.6 and O > 0.5 | "спокойствие" (calm) |
| otherwise | "нормальное" (normal) |

## Implementation Files

- `cpp/include/alife/hormones.h` - Header file with class definition
- `cpp/src/hormones.cpp` - Implementation file
- `cpp/tests/test_hormones.cpp` - Unit tests
- `tools/export_hormones_golden.py` - Golden data export tool

## Testing

Run tests with:
```bash
cd cpp/build
ctest --output-on-failure
```

Generate golden data with:
```bash
python3 tools/export_hormones_golden.py
```

## Compatibility Notes

- All formulas are identical to Python implementation
- Uses `double` precision for parity with Python
- Allowed tolerance for comparison: `1e-10`
- No new hormones added, no existing hormones removed
- Brain and World modules not included in this migration
