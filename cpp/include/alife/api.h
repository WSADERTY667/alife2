/**
 * @file api.h
 * @brief Stable C API for ALife Core simulation.
 * 
 * This header provides a C-compatible interface to the ALife simulation,
 * designed for use with GDExtension and other external bindings.
 * 
 * Key features:
 * - extern "C" linkage for C compatibility
 * - Opaque handles (no direct exposure of C++ classes)
 * - Clear ownership semantics
 * - Thread-unsafe (single-threaded use only)
 */

#ifndef ALIFE_API_H
#define ALIFE_API_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Opaque handle to the simulation world.
 * 
 * Created with alife_world_create(), destroyed with alife_world_destroy().
 * Do not access internal members directly.
 */
typedef struct AlifeWorld AlifeWorld;

/**
 * @brief View structure for agent data.
 * 
 * Used to retrieve agent state from the simulation.
 * All fields are read-only copies of internal state.
 */
typedef struct AgentView {
    int id;           ///< Unique agent identifier
    int generation;   ///< Generation number (0 = initial)
    int tribe;        ///< Tribe identifier (from genome)
    float x;          ///< Position X coordinate
    float y;          ///< Position Y coordinate
    float angle;      ///< Movement direction angle (radians)
    float energy;     ///< Current energy level (0-100)
    float dopamine;   ///< Dopamine hormone level
    float serotonin;  ///< Serotonin hormone level
    float oxytocin;   ///< Oxytocin hormone level
    float cortisol;   ///< Cortisol hormone level
    float testosterone; ///< Testosterone hormone level
    float depression; ///< Depression indicator (0-1)
    float breakdown;  ///< Breakdown indicator (0-1)
} AgentView;

/**
 * @brief View structure for food data.
 * 
 * Used to retrieve food positions from the simulation.
 */
typedef struct FoodView {
    float x;  ///< Position X coordinate
    float y;  ///< Position Y coordinate
} FoodView;

/* ============================================================================
 * World Management Functions
 * ============================================================================ */

/**
 * @brief Create a new simulation world.
 * @return Pointer to the new world, or NULL on failure.
 * 
 * Creates a world with default settings:
 * - seed = 42
 * - initial agents = 24
 * - initial food = 90
 * 
 * Ownership: Caller must call alife_world_destroy() when done.
 * 
 * Example:
 * @code
 * AlifeWorld* world = alife_world_create();
 * if (!world) {
 *     // Handle error
 *     return;
 * }
 * // ... use world ...
 * alife_world_destroy(world);
 * @endcode
 */
AlifeWorld* alife_world_create(void);

/**
 * @brief Destroy a simulation world and free all resources.
 * @param world Pointer to world created by alife_world_create().
 * 
 * Safe to call with NULL (does nothing).
 * After calling, the pointer must not be used.
 * 
 * Example:
 * @code
 * alife_world_destroy(world);
 * world = NULL;  // Good practice
 * @endcode
 */
void alife_world_destroy(AlifeWorld* world);

/* ============================================================================
 * World Configuration Functions
 * ============================================================================ */

/**
 * @brief Set the random seed for the world.
 * @param world Pointer to world.
 * @param seed Random seed value (64-bit).
 * 
 * Must be called before alife_world_reset() to take effect.
 * Using the same seed guarantees deterministic simulation.
 * 
 * Example:
 * @code
 * alife_world_set_seed(world, 12345);
 * alife_world_reset(world, 24, 90);
 * @endcode
 */
void alife_world_set_seed(AlifeWorld* world, uint64_t seed);

/**
 * @brief Reset the world to initial state.
 * @param world Pointer to world.
 * @param agent_count Number of agents to spawn.
 * @param food_count Number of food items to spawn.
 * 
 * Clears all existing agents and food, then spawns new ones.
 * Resets tick counter to 0.
 * 
 * Example:
 * @code
 * alife_world_reset(world, 30, 100);
 * @endcode
 */
void alife_world_reset(AlifeWorld* world, int agent_count, int food_count);

/* ============================================================================
 * Simulation Step Function
 * ============================================================================ */

/**
 * @brief Advance the simulation by one tick.
 * @param world Pointer to world.
 * 
 * Performs one complete simulation step:
 * 1. Spawn new food (probabilistic)
 * 2. Update all agents (sensors, brain, movement, events)
 * 3. Remove eaten food
 * 4. Add newborn agents
 * 5. Remove dead agents
 * 6. Protect from extinction (spawn if needed)
 * 
 * Example:
 * @code
 * for (int i = 0; i < 1000; i++) {
 *     alife_world_step(world);
 * }
 * @endcode
 */
void alife_world_step(AlifeWorld* world);

/* ============================================================================
 * Agent Query Functions
 * ============================================================================ */

/**
 * @brief Get the current number of agents.
 * @param world Pointer to world.
 * @return Number of living agents.
 * 
 * Example:
 * @code
 * int count = alife_world_get_agent_count(world);
 * printf("Agents: %d\n", count);
 * @endcode
 */
int alife_world_get_agent_count(AlifeWorld* world);

/**
 * @brief Get agent data into a buffer.
 * @param world Pointer to world.
 * @param buffer Output buffer for agent data.
 * @param max_count Maximum number of agents to retrieve.
 * @return Number of agents written to buffer.
 * 
 * Copies up to max_count agents into the buffer.
 * Returns the actual number copied (may be less than max_count).
 * If buffer is NULL, returns total count without copying.
 * 
 * Example:
 * @code
 * int count = alife_world_get_agent_count(world);
 * AgentView* agents = malloc(count * sizeof(AgentView));
 * int actual = alife_world_get_agents(world, agents, count);
 * 
 * for (int i = 0; i < actual; i++) {
 *     printf("Agent %d: (%f, %f)\n", 
 *            agents[i].id, agents[i].x, agents[i].y);
 * }
 * free(agents);
 * @endcode
 */
int alife_world_get_agents(AlifeWorld* world, AgentView* buffer, int max_count);

/* ============================================================================
 * Food Query Functions
 * ============================================================================ */

/**
 * @brief Get the current number of food items.
 * @param world Pointer to world.
 * @return Number of uneaten food items.
 * 
 * Example:
 * @code
 * int count = alife_world_get_food_count(world);
 * printf("Food: %d\n", count);
 * @endcode
 */
int alife_world_get_food_count(AlifeWorld* world);

/**
 * @brief Get food data into a buffer.
 * @param world Pointer to world.
 * @param buffer Output buffer for food data.
 * @param max_count Maximum number of food items to retrieve.
 * @return Number of food items written to buffer.
 * 
 * Copies up to max_count food items into the buffer.
 * Returns the actual number copied.
 * If buffer is NULL, returns total count without copying.
 * 
 * Example:
 * @code
 * int count = alife_world_get_food_count(world);
 * FoodView* foods = malloc(count * sizeof(FoodView));
 * int actual = alife_world_get_foods(world, foods, count);
 * 
 * for (int i = 0; i < actual; i++) {
 *     printf("Food %d: (%f, %f)\n", 
 *            i, foods[i].x, foods[i].y);
 * }
 * free(foods);
 * @endcode
 */
int alife_world_get_foods(AlifeWorld* world, FoodView* buffer, int max_count);

/* ============================================================================
 * Agent Intervention Functions
 * ============================================================================ */

/**
 * @brief Give reward to an agent.
 * @param world Pointer to world.
 * @param agent_id ID of the agent to reward.
 * @param amount Reward amount (positive value).
 * 
 * Adds to the agent's pending_reward, which affects learning.
 * Silently ignores invalid agent IDs.
 * 
 * Example:
 * @code
 * // Reward agent 5 for good behavior
 * alife_agent_reward(world, 5, 1.0f);
 * @endcode
 */
void alife_agent_reward(AlifeWorld* world, int agent_id, float amount);

/**
 * @brief Punish an agent.
 * @param world Pointer to world.
 * @param agent_id ID of the agent to punish.
 * @param amount Punishment amount (positive value).
 * 
 * Adds to the agent's pending_punishment, which affects learning.
 * Silently ignores invalid agent IDs.
 * 
 * Example:
 * @code
 * // Punish agent 3 for bad behavior
 * alife_agent_punish(world, 3, 0.5f);
 * @endcode
 */
void alife_agent_punish(AlifeWorld* world, int agent_id, float amount);

/* ============================================================================
 * Food Manipulation Functions
 * ============================================================================ */

/**
 * @brief Spawn food at a specific position.
 * @param world Pointer to world.
 * @param x X coordinate for food spawn.
 * @param y Y coordinate for food spawn.
 * 
 * Spawns food with default nutrition at the specified position.
 * Position is clamped to world bounds if necessary.
 * 
 * Example:
 * @code
 * // Spawn food near center of world
 * alife_world_spawn_food(world, 500.0f, 320.0f);
 * @endcode
 */
void alife_world_spawn_food(AlifeWorld* world, float x, float y);

#ifdef __cplusplus
}
#endif

#endif /* ALIFE_API_H */
