# ALife Core C API Documentation

## Overview

The ALife Core C API provides a stable, C-compatible interface to the artificial life simulation. This API is designed for use with GDExtension and other external bindings that require a C interface.

## Key Features

- **extern "C" linkage**: Full C compatibility
- **Opaque handles**: Internal C++ classes are not exposed directly
- **Clear ownership semantics**: Explicit create/destroy pattern
- **Thread-unsafe**: Designed for single-threaded use only

## Structures

### AgentView

Structure containing agent state data:

```c
typedef struct AgentView {
    int id;           // Unique agent identifier
    int generation;   // Generation number (0 = initial)
    int tribe;        // Tribe identifier (-1 if none)
    float x;          // Position X coordinate (0-1000)
    float y;          // Position Y coordinate (0-640)
    float angle;      // Movement direction angle (radians)
    float energy;     // Current energy level (0-100)
    float dopamine;   // Dopamine hormone level
    float serotonin;  // Serotonin hormone level
    float oxytocin;   // Oxytocin hormone level
    float cortisol;   // Cortisol hormone level
    float testosterone; // Testosterone hormone level
    float depression; // Depression indicator (0-1)
    float breakdown;  // Breakdown indicator (0-1)
} AgentView;
```

### FoodView

Structure containing food position data:

```c
typedef struct FoodView {
    float x;  // Position X coordinate
    float y;  // Position Y coordinate
} FoodView;
```

### AlifeWorld

Opaque handle to the simulation world. Internal structure is not exposed.

```c
typedef struct AlifeWorld AlifeWorld;
```

## Functions

### World Management

#### alife_world_create

```c
AlifeWorld* alife_world_create(void);
```

Creates a new simulation world with default settings:
- seed = 42
- initial agents = 24
- initial food = 90

**Returns:** Pointer to the new world, or NULL on failure.

**Ownership:** Caller must call `alife_world_destroy()` when done.

---

#### alife_world_destroy

```c
void alife_world_destroy(AlifeWorld* world);
```

Destroys a simulation world and frees all resources.

**Parameters:**
- `world`: Pointer to world created by `alife_world_create()`.

Safe to call with NULL (does nothing).

---

### World Configuration

#### alife_world_set_seed

```c
void alife_world_set_seed(AlifeWorld* world, uint64_t seed);
```

Sets the random seed for the world. Must be called before `alife_world_reset()` to take effect.

**Parameters:**
- `world`: Pointer to world.
- `seed`: Random seed value (64-bit).

Using the same seed guarantees deterministic simulation.

---

#### alife_world_reset

```c
void alife_world_reset(AlifeWorld* world, int agent_count, int food_count);
```

Resets the world to initial state with specified parameters.

**Parameters:**
- `world`: Pointer to world.
- `agent_count`: Number of agents to spawn.
- `food_count`: Number of food items to spawn.

Clears all existing agents and food, then spawns new ones. Resets tick counter to 0.

---

### Simulation

#### alife_world_step

```c
void alife_world_step(AlifeWorld* world);
```

Advances the simulation by one tick.

**Parameters:**
- `world`: Pointer to world.

Performs one complete simulation step:
1. Spawn new food (probabilistic)
2. Update all agents (sensors, brain, movement, events)
3. Remove eaten food
4. Add newborn agents
5. Remove dead agents
6. Protect from extinction (spawn if needed)

---

### Agent Queries

#### alife_world_get_agent_count

```c
int alife_world_get_agent_count(AlifeWorld* world);
```

Gets the current number of living agents.

**Parameters:**
- `world`: Pointer to world.

**Returns:** Number of living agents.

---

#### alife_world_get_agents

```c
int alife_world_get_agents(AlifeWorld* world, AgentView* buffer, int max_count);
```

Gets agent data into a buffer.

**Parameters:**
- `world`: Pointer to world.
- `buffer`: Output buffer for agent data (can be NULL).
- `max_count`: Maximum number of agents to retrieve.

**Returns:** Total number of agents (may be more than `max_count`).

If buffer is NULL, returns total count without copying. If buffer is provided, copies up to `max_count` agents and returns the total count.

---

### Food Queries

#### alife_world_get_food_count

```c
int alife_world_get_food_count(AlifeWorld* world);
```

Gets the current number of uneaten food items.

**Parameters:**
- `world`: Pointer to world.

**Returns:** Number of uneaten food items.

---

#### alife_world_get_foods

```c
int alife_world_get_foods(AlifeWorld* world, FoodView* buffer, int max_count);
```

Gets food data into a buffer.

**Parameters:**
- `world`: Pointer to world.
- `buffer`: Output buffer for food data (can be NULL).
- `max_count`: Maximum number of food items to retrieve.

**Returns:** Total number of uneaten food items.

---

### Agent Intervention

#### alife_agent_reward

```c
void alife_agent_reward(AlifeWorld* world, int agent_id, float amount);
```

Gives reward to an agent.

**Parameters:**
- `world`: Pointer to world.
- `agent_id`: ID of the agent to reward.
- `amount`: Reward amount (positive value).

Adds to the agent's pending_reward, which affects learning. Silently ignores invalid agent IDs.

---

#### alife_agent_punish

```c
void alife_agent_punish(AlifeWorld* world, int agent_id, float amount);
```

Punishes an agent.

**Parameters:**
- `world`: Pointer to world.
- `agent_id`: ID of the agent to punish.
- `amount`: Punishment amount (positive value).

Adds to the agent's pending_punishment, which affects learning. Silently ignores invalid agent IDs.

---

### Food Manipulation

#### alife_world_spawn_food

```c
void alife_world_spawn_food(AlifeWorld* world, float x, float y);
```

Spawns food at a specific position.

**Parameters:**
- `world`: Pointer to world.
- `x`: X coordinate for food spawn.
- `y`: Y coordinate for food spawn.

Position is clamped to world bounds (10 to WORLD_W-10, 10 to WORLD_H-10).

---

## Memory Ownership Rules

1. **Create/Destroy Pattern**: All `AlifeWorld*` pointers must be created with `alife_world_create()` and destroyed with `alife_world_destroy()`.

2. **Buffer Ownership**: Buffers passed to `alife_world_get_agents()` and `alife_world_get_foods()` are owned by the caller. The caller must allocate and free them.

3. **NULL Safety**: All functions safely handle NULL world pointers (they do nothing and return appropriate zero values).

4. **No Internal Allocation**: The API does not allocate memory that the caller must free (except for the world itself).

---

## Example Usage

### Basic Simulation Loop

```c
#include <stdio.h>
#include <stdlib.h>
#include "alife/api.h"

int main() {
    // Create world
    AlifeWorld* world = alife_world_create();
    if (!world) {
        fprintf(stderr, "Failed to create world\n");
        return 1;
    }
    
    // Run simulation for 1000 steps
    for (int i = 0; i < 1000; i++) {
        alife_world_step(world);
        
        // Print status every 100 steps
        if (i % 100 == 0) {
            int agents = alife_world_get_agent_count(world);
            int food = alife_world_get_food_count(world);
            printf("Step %d: %d agents, %d food\n", i, agents, food);
        }
    }
    
    // Get final agent data
    int count = alife_world_get_agent_count(world);
    AgentView* agents = malloc(count * sizeof(AgentView));
    alife_world_get_agents(world, agents, count);
    
    printf("\nFinal population:\n");
    for (int i = 0; i < count; i++) {
        printf("  Agent %d: gen=%d, energy=%.1f, pos=(%.1f, %.1f)\n",
               agents[i].id, agents[i].generation, agents[i].energy,
               agents[i].x, agents[i].y);
    }
    
    free(agents);
    alife_world_destroy(world);
    return 0;
}
```

### Using Custom Seed and Reset

```c
#include "alife/api.h"

int main() {
    AlifeWorld* world = alife_world_create();
    
    // Set custom seed for reproducibility
    alife_world_set_seed(world, 12345);
    
    // Reset with custom counts
    alife_world_reset(world, 30, 100);
    
    // ... run simulation ...
    
    alife_world_destroy(world);
    return 0;
}
```

### Intervening in Simulation

```c
#include "alife/api.h"

void train_agent(AlifeWorld* world, int agent_id) {
    // Get agent data
    AgentView agent;
    alife_world_get_agents(world, &agent, 1);
    
    if (agent.id == agent_id) {
        // Reward good behavior
        if (agent.energy > 80.0f) {
            alife_agent_reward(world, agent_id, 1.0f);
        }
        
        // Punish bad behavior
        if (agent.cortisol > 1.5f) {
            alife_agent_punish(world, agent_id, 0.5f);
        }
    }
    
    // Add extra food near struggling agents
    if (agent.energy < 30.0f) {
        alife_world_spawn_food(world, agent.x, agent.y);
    }
}
```

---

## Building

### CMake

```bash
cd cpp/build
cmake ..
make
```

### Linking

Link against `libalife_core.a` and include `cpp/include`:

```bash
g++ -I./cpp/include my_program.cpp -L./cpp/build -lalife_core -o my_program
```

---

## Testing

Run the C API tests:

```bash
cd cpp/build
./test_api
```

Expected output:
```
=== ALife C API Tests ===

Running test_world_create_destroy... PASS
Running test_seed_and_reset... PASS
Running test_world_step... PASS
...

=== Test Summary ===
Passed: 12
Failed: 0
Total:  12
```

---

## Limitations

1. **Single-threaded**: The API is not thread-safe. All calls must be made from the same thread.

2. **No Error Reporting**: Functions silently ignore invalid inputs (NULL pointers, invalid IDs). Check return values where applicable.

3. **Tribe Identification**: The `tribe` field in `AgentView` is derived from genome tribal_tags using a hash. It may not match internal representations.

4. **Float Precision**: Position and hormone values are returned as floats (not doubles) for C compatibility.

5. **World Bounds**: Coordinates outside [10, WORLD_W-10] × [10, WORLD_H-10] are clamped.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024 | Initial release |
