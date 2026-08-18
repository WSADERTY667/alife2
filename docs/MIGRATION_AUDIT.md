# Migration Audit: Python to C++/Godot

## Overview

This document audits the current Python prototype for the ALife simulation in preparation
for migration to C++ with Godot engine integration.

---

## Current Python Modules

### Core Simulation Modules (`alife/`)

| Module | Description |
|--------|-------------|
| `config.py` | Global constants and configuration (world size, neural network params, population settings) |
| `genome.py` | Genome class with genes, mutation, crossover, and tribal tag inheritance |
| `brain.py` | Spiking Neural Network (SNN) with STDP learning, plasticity modulation |
| `hormones.py` | Hormonal system (Dopamine, Serotonin, Oxytocin, Cortisol, Testosterone) with emotional states |
| `agent.py` | Agent class integrating brain, hormones, genome, sensors, movement, reproduction |
| `world.py` | World simulation managing agents, food, save/load, generation statistics |
| `utils.py` | Utility functions (angle normalization, wall sensing) |
| `render.py` | Pygame-based visualization (not needed for headless/server mode) |

### Entry Points

| File | Description |
|------|-------------|
| `main.py` | Main entry point with CLI args for headless/visual mode |
| `alife_mvp.py` | Legacy monolithic file (should be removed after migration) |

### Tests (`tests/`)

| Test File | Coverage |
|-----------|----------|
| `test_brain.py` | SNN step output, NaN checks |
| `test_emotions.py` | Hormone dynamics, emotional states (depression, paranoia, trust, aggression) |
| `test_genome.py` | Genome creation, mutation bounds |
| `test_world.py` | Basic world update cycle |

---

## Current Simulation Rules

### World Configuration
- **World Size**: 1000x640 pixels
- **FPS**: 60
- **Initial Agents**: 24
- **Initial Food**: 90 (respawn rate: 0.22 per tick)
- **Minimum Agents**: 6 (auto-respawn if below)

### Neural Network Architecture
- **Input Neurons**: 12 (hunger, food sensors, agent sensors, wall sensor, pain, cortisol level)
- **Hidden Neurons**: 160 (heritable, can mutate between 40-400)
- **Output Neurons**: 6 (left, right, forward, backward, eat, attack)
- **Learning**: Enabled via STDP with dopamine modulation
- **Synaptic Scale**: 0.085

### Energy & Lifecycle
- **Max Energy**: 100.0
- **Start Energy**: 70.0
- **Reproduction Threshold**: 78.0 energy
- **Reproduction Cost**: 28.0 energy per parent
- **Base Reproduction Rate**: 0.035 * sociality * compatibility
- **Maturation Age**: 500 ticks
- **Max Age**: 26000 ticks
- **Metabolism**: Heritable (0.01-0.10 per tick)

### Sensors (12 inputs)
1. Hunger level
2-3. Food proximity (left/right relative angle)
4-7. Nearest agent proximity and kinship similarity
8. Wall distance sensor
9. Pain level (recent)
10. Cortisol level
11. Social proximity flag

### Actions (6 outputs)
1. Turn left
2. Turn right
3. Move forward
4. Move backward
5. Eat attempt
6. Attack attempt

### Hormonal System

| Hormone | Base Range | Key Functions |
|---------|------------|---------------|
| Dopamine (D) | 0.2-1.0 | Reward signaling, plasticity modulation |
| Serotonin (S) | 0.2-1.0 | Mood regulation, depression prevention |
| Oxytocin (O) | 0.1-0.8 | Social bonding, trust, mating |
| Cortisol (C) | 0.05-0.6 | Stress response, arousal, aggression |
| Testosterone (T) | 0.1-1.0 | Dominance, conflict behavior |

### Emotional States (derived from hormones)
- **Arousal**: Cortisol + Testosterone - Serotonin
- **Plasticity**: Dopamine-dependent learning rate
- **Aggression**: Testosterone + Cortisol - Serotonin + hunger
- **Sociality**: Oxytocin + Serotonin - Cortisol
- **Depression**: Low serotonin + low dopamine over time
- **Breakdown**: Chronic high cortisol (allostatic load > 1.8)
- **Paranoia**: Punishment history + cortisol + fear
- **Trust**: Oxytocin + social rewards - punishment

### Genome (30 heritable parameters)
- Mutation rate, connection probability, weight scale/max
- Membrane decay, spike threshold, STDP rate
- Hormone base levels, reactivity, decay rates, sensitivities
- Aggression gain, social gain, lamarckian weight
- Brain architecture mutability, stress resilience, social temperament

### Reproduction Rules
- Both parents must be mature (>500 ticks), have energy >78, cooldown ≤0
- Depression >0.85 blocks reproduction
- Compatibility based on genome similarity (kin recognition)
- Child inherits:
  - Blended genome with mutation
  - Tribal tags from both parents (up to 5)
  - Average hidden neuron count (±4 variation)
  - Lamarckian: 50% blended parent brain weights (if shapes match)

---

## Current Tests

### Passing Tests (17 total)

#### Brain Tests (2)
- `test_brain_step_returns_correct_size`: Verifies output shape matches OUTPUT_SIZE
- `test_brain_no_nan_after_steps`: Ensures no NaN after multiple steps

#### Emotion Tests (13)
- `test_hormones_initialization`: Default hormone levels
- `test_stress_increases_cortisol`: Punishment → cortisol rise
- `test_chronic_stress_leads_to_breakdown`: Sustained cortisol → breakdown state
- `test_low_serotonin_dopamine_causes_depression`: Dual deficiency → depression
- `test_oxytocin_increases_sociality`: Social events → oxytocin → sociality
- `test_punishment_history_affects_delayed_punishment`: Temporal credit assignment
- `test_paranoia_increases_with_punishment`: Negative events → paranoia
- `test_trust_increases_with_positive_social`: Positive interactions → trust
- `test_aggression_affected_by_paranoia_and_trust`: Emotional modulation of aggression
- `test_mood_refects_emotional_state`: Mood label selection logic
- `test_helper_methods`: is_broken(), is_depressed(), etc.
- `test_individual_hormone_profiles`: Variation across agents

#### Genome Tests (2)
- `test_genome_random_created`: Valid initial genome within bounds
- `test_genome_mutation_keeps_bounds`: Mutation respects min/max constraints

#### World Tests (1)
- `test_world_updates_without_crash`: Basic simulation step stability

### Missing Test Coverage
- No tests for save/load functionality
- No tests for reproduction mechanics
- No tests for agent-agent combat
- No tests for reflex assist behavior
- No tests for depression/breakdown behavioral effects
- No determinism/reproducibility tests
- No performance benchmarks

---

## Missing Determinism

### Current Issues

1. **No Random Seed Control**
   - `random` module used without seed initialization
   - `numpy.random.default_rng()` creates unseeded generators
   - Each run produces different results even with same config

2. **Non-Deterministic Operations**
   - Agent spawning uses `random.uniform()` for positions
   - Genome initialization uses `random.uniform()` for all genes
   - Brain weight initialization uses unseeded RNG
   - Mutation uses `random.random()` and `random.gauss()`
   - Crossover blending uses `random.random()`

3. **Floating Point Non-Associativity**
   - NumPy operations may vary across platforms
   - Order of agent updates depends on list iteration order
   - Parallel operations could introduce variance

### Required for C++ Migration

To ensure reproducible simulations:
- Implement seeded PRNG (e.g., PCG32, Xorshift) with explicit seed parameter
- Use fixed-point arithmetic or consistent floating-point ordering
- Ensure agent update order is deterministic (sorted by ID or spatial hash)
- Log simulation seed in save files for exact replay

---

## Missing Save/Load Versioning

### Current State

- `World.SCHEMA_VERSION = 2` exists but is minimally used
- Save format: JSON (world state) + NPZ (brain weights)
- Backward compatibility check exists but is incomplete:
  ```python
  if schema_version != self.SCHEMA_VERSION and schema_version < 2:
      pass  # No actual migration logic
  ```

### Risks

1. **No Migration Logic**: Loading v1 saves into v2 schema may fail silently
2. **Brain Architecture Changes**: If `n_hidden` changes between versions, weight matrices won't match
3. **New Fields Added**: Hormone fields (paranoia, trust, delayed_punishment) added without version bump handling
4. **Genome Field Evolution**: `tribal_tags` and `n_hidden` are recent additions; old saves lack these

### Required for C++ Migration

- Implement proper schema versioning with migration functions
- Define binary format specification for C++ compatibility
- Add checksums/validation for save file integrity
- Document field types and byte layouts explicitly
- Consider using Protocol Buffers or FlatBuffers for cross-language serialization

---

## Risks for C++ Migration

### High Priority Risks

1. **Neural Network Implementation**
   - Python uses NumPy vectorized operations; C++ needs equivalent (Eigen, BLAS, or custom)
   - STDP learning rule involves outer products; must be carefully ported
   - Sparse connectivity via mask; efficiency considerations in C++

2. **Hormonal System Complexity**
   - 30+ genome parameters affecting hormone dynamics
   - Non-linear interactions (clamp, thresholds, feedback loops)
   - Emotional state machine (depression, breakdown, paranoia, trust)
   - Must verify numerical stability in float32 vs float64

3. **Heritable Brain Architecture**
   - Variable hidden neuron count (40-400) per agent
   - Requires dynamic memory allocation in C++
   - Parent-child weight inheritance needs shape matching logic

4. **Reproduction & Genetics**
   - Crossover blends 30 genes with probabilistic rules
   - Tribal tag inheritance (set union, max 5)
   - Lamarckian weight blending requires compatible brain shapes

### Medium Priority Risks

5. **Physics/Movement**
   - Wall bouncing with angle reflection
   - Collision detection (eat range, attack range, social range)
   - Agent positioning precision (float32 vs double)

6. **Performance Expectations**
   - Python MVP runs at ~15ms/tick for 24 agents
   - C++ should target 1000+ agents at same tick rate
   - Godot rendering overhead unknown

7. **Testing Parity**
   - Must replicate all 17 existing Python tests in C++
   - Need additional tests for determinism, save/load, edge cases

### Low Priority Risks

8. **Configuration Management**
   - Python uses module-level constants; C++ needs Config singleton or struct
   - Default values must match exactly

9. **Tooling Ecosystem**
   - Python has pytest, black, ruff, mypy
   - C++ needs equivalent (Catch2, clang-format, cppcheck)

---

## Recommendations

### Phase 1: Stabilize Python Prototype
- [ ] Add random seed CLI argument for reproducibility
- [ ] Expand test coverage to 80%+
- [ ] Implement proper save/load migration
- [ ] Remove `alife_mvp.py` legacy file

### Phase 2: C++ Core Development
- [ ] Port config, genome, brain, hormones modules first
- [ ] Use Eigen for linear algebra (matches NumPy semantics)
- [ ] Implement deterministic PRNG with seed serialization
- [ ] Write unit tests alongside implementation

### Phase 3: Godot Integration
- [ ] Create GDExtension wrapper for C++ core
- [ ] Implement visual rendering separately from simulation
- [ ] Support headless server mode for batch experiments

### Phase 4: Validation
- [ ] Run identical seeds in Python and C++, compare trajectories
- [ ] Performance benchmarking at scale (100, 1000, 10000 agents)
- [ ] Verify all emotional behaviors match reference implementation

---

*Document generated for MIG-000 migration audit.*
