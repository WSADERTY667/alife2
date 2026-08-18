# C++ Build Documentation

## Requirements

### Compiler
- GCC 10+ or Clang 11+ with C++20 support

### Build System
- CMake 3.16 or higher

### Optional Tools
- `ctest` for running tests (included with CMake)

## Building the Project

### 1. Create Build Directory

```bash
cd cpp
mkdir -p build
cd build
```

### 2. Configure with CMake

```bash
cmake ..
```

For a release build with optimizations:

```bash
cmake -DCMAKE_BUILD_TYPE=Release ..
```

For a debug build:

```bash
cmake -DCMAKE_BUILD_TYPE=Debug ..
```

### 3. Build

```bash
cmake --build .
```

Or using make directly:

```bash
make
```

### 4. Build Output

After successful build, the following artifacts will be in the `build/` directory:
- `libalife_core.a` — static library
- `alife_headless` — headless simulation executable
- `test_version` — test executable

## Running Tests

```bash
cd cpp/build
ctest --output-on-failure
```

Or run tests manually:

```bash
./test_version
```

## Running alife_headless

### Basic Usage

```bash
./alife_headless
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--help` | Show help message | — |
| `--seed <N>` | Set random seed | 42 |
| `--ticks <N>` | Set number of simulation ticks | 100 |
| `--agents <N>` | Set number of agents | 50 |
| `--food <N>` | Set initial food amount | 100 |
| `--out <PATH>` | Set output file path | stdout |

### Examples

Run with default settings:

```bash
./alife_headless
```

Run with custom seed and tick count:

```bash
./alife_headless --seed 12345 --ticks 1000
```

Run with specific agent and food counts:

```bash
./alife_headless --agents 100 --food 200
```

Save output to file:

```bash
./alife_headless --out simulation.log
```

Show help:

```bash
./alife_headless --help
```

## Clean Build

To clean all build artifacts:

```bash
cd cpp/build
rm -rf *
```

Then reconfigure and rebuild from step 2.

## Troubleshooting

### CMake Version Error

If you see an error about CMake version, ensure you have CMake 3.16+:

```bash
cmake --version
```

### Compiler Does Not Support C++20

Update your compiler or use a newer version:

```bash
g++ --version
```

### Missing Dependencies

The current implementation has no external dependencies beyond the standard library.
