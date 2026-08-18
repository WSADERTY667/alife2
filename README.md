# ALife Creatures-like Prototype

2D artificial life simulation with:
- spiking neural network brain
- reward-modulated STDP learning
- genome bottleneck
- Darwin-Lamarckian inheritance
- hormone-based mood modulation (dopamine, serotonin, oxytocin, cortisol, testosterone)
- social behavior / tribes
- emotional states (depression, paranoia, trust, breakdown)

## Project Layout

```
alife/
├── README.md
├── docs/
│   ├── MIGRATION_AUDIT.md    # C++ migration audit document
│   └── emotional_model.md    # Hormonal/emotional system documentation
├── python/
│   ├── alife/                # Core simulation modules
│   │   ├── config.py         # Configuration constants
│   │   ├── genome.py         # Genome, mutation, crossover
│   │   ├── brain.py          # Spiking neural network
│   │   ├── hormones.py       # Hormonal system
│   │   ├── agent.py          # Agent class
│   │   ├── world.py          # World simulation
│   │   ├── utils.py          # Utilities
│   │   └── render.py         # Pygame rendering
│   ├── tests/                # pytest test suite
│   ├── main.py               # Entry point
│   └── requirements.txt      # Python dependencies
└── tools/                    # Migration tools (future)
```

## Run (Python Prototype)

```bash
cd python
pip install -r requirements.txt
python main.py              # Visual mode (Pygame)
python main.py --headless   # Headless mode
python main.py --headless --ticks 1000 --agents 50
```

## Run Tests

```bash
cd python
pytest -v
```

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

## Configuration

Key parameters in `python/alife/config.py`:
- `WORLD_W`, `WORLD_H`: World dimensions (1000x640)
- `AGENT_COUNT`: Initial agents (24)
- `N_HIDDEN`: Hidden neurons (160, heritable 40-400)
- `INPUT_SIZE`, `OUTPUT_SIZE`: Neural I/O (12/6)

## Migration Status

See [docs/MIGRATION_AUDIT.md](docs/MIGRATION_AUDIT.md) for:
- Current Python module structure
- Simulation rules and formulas
- Test coverage analysis
- Missing determinism issues
- Save/load versioning gaps
- C++ migration risks and recommendations

## C++ Build

For building the C++ version of the project, see [docs/CPP_BUILD.md](docs/CPP_BUILD.md).
