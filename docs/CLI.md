# CLI Arguments Documentation

## Overview

The ALife MVP simulation supports command-line arguments for both visual and headless modes.

## Usage

```bash
cd python
python main.py [OPTIONS]
```

## Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--headless` | flag | off | Run without Pygame display (console mode) |
| `--seed` | int | None | Random seed for reproducibility |
| `--ticks` | int | 1000 | Number of simulation ticks (headless mode only) |
| `--agents` | int | None | Initial number of agents (overrides config) |
| `--food` | int | None | Initial/max number of food items (overrides config) |
| `--out` | str | None | Output file for headless results |
| `--hidden-neurons` | int | None | Number of hidden neurons (overrides config) |

## Examples

### Visual Mode (default)

```bash
python main.py
```

Launches the simulation with Pygame GUI. Use keyboard controls to interact.

### Headless Mode

```bash
python main.py --headless --ticks 1000
```

Runs 1000 ticks of simulation without graphics, outputs statistics to console.

### Headless with Custom Parameters

```bash
python main.py --headless --ticks 5000 --agents 50 --food 100
```

Runs 5000 ticks with 50 initial agents and 100 food items.

### Reproducible Run with Seed

```bash
python main.py --headless --ticks 1000 --seed 42
```

Sets random seed for reproducible simulation results.

### Save Results to File

```bash
python main.py --headless --ticks 1000 --out results.txt
```

Writes simulation statistics to `results.txt`.

### Combined Example

```bash
python main.py --headless --seed 123 --ticks 2000 --agents 30 --food 80 --out output.log
```

Full-featured headless run with all parameters specified.

## Output Format (Headless)

When running in headless mode, the following statistics are printed:

```
=== Headless Simulation Results ===
Ticks completed: 1000
Average tick time: XX.XXX ms
Final agent count: XX
Average generation: X.XX
Total births: XX
Total deaths: XX
Total simulation time: XX.XX s
```

If `--out` is specified, the same data is written to the output file.

## Controls (Visual Mode)

| Key | Action |
|-----|--------|
| Space | Pause/Resume |
| F | Add food |
| A | Add agent |
| R | Reset world |
| S | Save world |
| L | Load world |
| T | Reward selected agent |
| P | Punish selected agent |
| +/- | Simulation speed |
| Click | Select agent |
| ESC | Exit |

## Configuration Override

The following arguments temporarily override values from `alife/config.py`:

- `--agents` → `AGENT_COUNT`
- `--food` → `FOOD_MAX`
- `--hidden-neurons` → `N_HIDDEN`

Original values are restored after simulation completes.
