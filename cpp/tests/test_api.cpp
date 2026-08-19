/**
 * @file test_api.cpp
 * @brief Tests for the C API (api.h/api.cpp).
 * 
 * Tests cover:
 * - World creation and destruction
 * - Simulation stepping
 * - Agent and food queries
 * - Agent reward/punishment
 * - Food spawning
 */

#include <iostream>
#include <cstdlib>
#include <cstring>
#include "alife/api.h"

// Test result tracking
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) void name()
#define RUN_TEST(name) do { \
    std::cout << "Running " #name "... "; \
    try { \
        name(); \
        std::cout << "PASS" << std::endl; \
        tests_passed++; \
    } catch (const std::exception& e) { \
        std::cout << "FAIL: " << e.what() << std::endl; \
        tests_failed++; \
    } catch (...) { \
        std::cout << "FAIL: unexpected exception" << std::endl; \
        tests_failed++; \
    } \
} while(0)

#define ASSERT(cond, msg) do { \
    if (!(cond)) { \
        throw std::runtime_error(msg); \
    } \
} while(0)

// ============================================================================
// Test: World Creation and Destruction
// ============================================================================

TEST(test_world_create_destroy) {
    // Create world
    AlifeWorld* world = alife_world_create();
    ASSERT(world != nullptr, "World creation returned null");
    
    // Destroy world (should not crash)
    alife_world_destroy(world);
    
    // Destroying null should be safe
    alife_world_destroy(nullptr);
}

// ============================================================================
// Test: Basic Simulation Step
// ============================================================================

TEST(test_world_step) {
    AlifeWorld* world = alife_world_create();
    ASSERT(world != nullptr, "World creation failed");
    
    // Run 100 steps without crash
    for (int i = 0; i < 100; ++i) {
        alife_world_step(world);
    }
    
    alife_world_destroy(world);
}

// ============================================================================
// Test: Agent Count Query
// ============================================================================

TEST(test_agent_count) {
    AlifeWorld* world = alife_world_create();
    ASSERT(world != nullptr, "World creation failed");
    
    int count = alife_world_get_agent_count(world);
    ASSERT(count > 0, "Initial agent count should be positive");
    
    // After some steps, count may change but should remain positive
    for (int i = 0; i < 50; ++i) {
        alife_world_step(world);
    }
    
    count = alife_world_get_agent_count(world);
    ASSERT(count >= 6, "Agent count should stay above minimum (6)");
    
    alife_world_destroy(world);
}

// ============================================================================
// Test: Get Agents Data
// ============================================================================

TEST(test_get_agents) {
    AlifeWorld* world = alife_world_create();
    ASSERT(world != nullptr, "World creation failed");
    
    int count = alife_world_get_agent_count(world);
    ASSERT(count > 0, "Should have agents");
    
    // Allocate buffer
    AgentView* agents = static_cast<AgentView*>(std::malloc(count * sizeof(AgentView)));
    ASSERT(agents != nullptr, "Memory allocation failed");
    
    // Get agent data
    int retrieved = alife_world_get_agents(world, agents, count);
    ASSERT(retrieved == count, "Should retrieve all agents");
    
    // Verify agent data is reasonable
    for (int i = 0; i < retrieved; ++i) {
        ASSERT(agents[i].id >= 0, "Agent ID should be non-negative");
        ASSERT(agents[i].generation >= 0, "Generation should be non-negative");
        ASSERT(agents[i].energy > 0.0f && agents[i].energy <= 100.0f, 
               "Energy should be in valid range");
        ASSERT(agents[i].x >= 0.0f && agents[i].x <= 1000.0f, 
               "X position should be within world bounds");
        ASSERT(agents[i].y >= 0.0f && agents[i].y <= 640.0f, 
               "Y position should be within world bounds");
    }
    
    std::free(agents);
    alife_world_destroy(world);
}

// ============================================================================
// Test: Food Count Query
// ============================================================================

TEST(test_food_count) {
    AlifeWorld* world = alife_world_create();
    ASSERT(world != nullptr, "World creation failed");
    
    int count = alife_world_get_food_count(world);
    ASSERT(count > 0, "Initial food count should be positive");
    
    alife_world_destroy(world);
}

// ============================================================================
// Test: Get Foods Data
// ============================================================================

TEST(test_get_foods) {
    AlifeWorld* world = alife_world_create();
    ASSERT(world != nullptr, "World creation failed");
    
    int count = alife_world_get_food_count(world);
    ASSERT(count > 0, "Should have food");
    
    // Allocate buffer
    FoodView* foods = static_cast<FoodView*>(std::malloc(count * sizeof(FoodView)));
    ASSERT(foods != nullptr, "Memory allocation failed");
    
    // Get food data
    int retrieved = alife_world_get_foods(world, foods, count);
    ASSERT(retrieved == count, "Should retrieve all food");
    
    // Verify food data is reasonable
    for (int i = 0; i < retrieved; ++i) {
        ASSERT(foods[i].x >= 0.0f && foods[i].x <= 1000.0f, 
               "Food X should be within world bounds");
        ASSERT(foods[i].y >= 0.0f && foods[i].y <= 640.0f, 
               "Food Y should be within world bounds");
    }
    
    std::free(foods);
    alife_world_destroy(world);
}

// ============================================================================
// Test: Agent Reward
// ============================================================================

TEST(test_agent_reward) {
    AlifeWorld* world = alife_world_create();
    ASSERT(world != nullptr, "World creation failed");
    
    // Get first agent ID
    AgentView agent;
    int retrieved = alife_world_get_agents(world, &agent, 1);
    ASSERT(retrieved > 0, "Should have at least one agent");
    
    int agent_id = agent.id;
    
    // Reward the agent (should not crash)
    alife_agent_reward(world, agent_id, 1.0f);
    
    // Invalid agent ID should not crash
    alife_agent_reward(world, -9999, 1.0f);
    
    alife_world_destroy(world);
}

// ============================================================================
// Test: Agent Punish
// ============================================================================

TEST(test_agent_punish) {
    AlifeWorld* world = alife_world_create();
    ASSERT(world != nullptr, "World creation failed");
    
    // Get first agent ID
    AgentView agent;
    int retrieved = alife_world_get_agents(world, &agent, 1);
    ASSERT(retrieved > 0, "Should have at least one agent");
    
    int agent_id = agent.id;
    
    // Punish the agent (should not crash)
    alife_agent_punish(world, agent_id, 0.5f);
    
    // Invalid agent ID should not crash
    alife_agent_punish(world, -9999, 0.5f);
    
    alife_world_destroy(world);
}

// ============================================================================
// Test: Spawn Food
// ============================================================================

TEST(test_spawn_food) {
    AlifeWorld* world = alife_world_create();
    ASSERT(world != nullptr, "World creation failed");
    
    int initial_count = alife_world_get_food_count(world);
    
    // Spawn new food
    alife_world_spawn_food(world, 500.0f, 320.0f);
    
    int new_count = alife_world_get_food_count(world);
    ASSERT(new_count > initial_count, "Food count should increase after spawn");
    
    // Spawn at edge positions (should clamp)
    alife_world_spawn_food(world, 0.0f, 0.0f);
    alife_world_spawn_food(world, 10000.0f, 10000.0f);
    
    alife_world_destroy(world);
}

// ============================================================================
// Test: Set Seed and Reset
// ============================================================================

TEST(test_seed_and_reset) {
    AlifeWorld* world = alife_world_create();
    ASSERT(world != nullptr, "World creation failed");
    
    // Set seed
    alife_world_set_seed(world, 12345);
    
    // Reset with different counts
    alife_world_reset(world, 10, 50);
    
    int agent_count = alife_world_get_agent_count(world);
    ASSERT(agent_count == 10, "Should have 10 agents after reset");
    
    int food_count = alife_world_get_food_count(world);
    ASSERT(food_count == 50, "Should have 50 food items after reset");
    
    alife_world_destroy(world);
}

// ============================================================================
// Test: Full Integration (100 steps + queries + interventions)
// ============================================================================

TEST(test_full_integration) {
    AlifeWorld* world = alife_world_create();
    ASSERT(world != nullptr, "World creation failed");
    
    // Run 100 steps
    for (int i = 0; i < 100; ++i) {
        alife_world_step(world);
    }
    
    // Get agents
    int count = alife_world_get_agent_count(world);
    AgentView* agents = static_cast<AgentView*>(std::malloc(count * sizeof(AgentView)));
    ASSERT(agents != nullptr, "Memory allocation failed");
    
    alife_world_get_agents(world, agents, count);
    
    // Reward first agent, punish second
    if (count >= 2) {
        alife_agent_reward(world, agents[0].id, 2.0f);
        alife_agent_punish(world, agents[1].id, 1.0f);
    }
    
    // Spawn food
    alife_world_spawn_food(world, 250.0f, 160.0f);
    
    // Continue simulation
    for (int i = 0; i < 50; ++i) {
        alife_world_step(world);
    }
    
    // Final queries
    int final_agents = alife_world_get_agent_count(world);
    int final_food = alife_world_get_food_count(world);
    
    ASSERT(final_agents >= 6, "Should maintain minimum population");
    ASSERT(final_food > 0, "Should have food remaining");
    
    std::free(agents);
    alife_world_destroy(world);
}

// ============================================================================
// Test: Buffer Edge Cases
// ============================================================================

TEST(test_buffer_edge_cases) {
    AlifeWorld* world = alife_world_create();
    ASSERT(world != nullptr, "World creation failed");
    
    // NULL buffer should return count without copying
    int count = alife_world_get_agent_count(world);
    int returned = alife_world_get_agents(world, nullptr, 0);
    ASSERT(returned == count, "NULL buffer should return total count");
    
    // Small buffer should not overflow
    AgentView small_buffer[1];
    returned = alife_world_get_agents(world, small_buffer, 1);
    ASSERT(returned == count, "Should return total count even with small buffer");
    
    alife_world_destroy(world);
}

// ============================================================================
// Main Test Runner
// ============================================================================

int main() {
    std::cout << "=== ALife C API Tests ===" << std::endl;
    std::cout << std::endl;
    
    // World management tests
    RUN_TEST(test_world_create_destroy);
    RUN_TEST(test_seed_and_reset);
    
    // Simulation tests
    RUN_TEST(test_world_step);
    RUN_TEST(test_full_integration);
    
    // Query tests
    RUN_TEST(test_agent_count);
    RUN_TEST(test_get_agents);
    RUN_TEST(test_food_count);
    RUN_TEST(test_get_foods);
    
    // Intervention tests
    RUN_TEST(test_agent_reward);
    RUN_TEST(test_agent_punish);
    RUN_TEST(test_spawn_food);
    
    // Edge case tests
    RUN_TEST(test_buffer_edge_cases);
    
    // Summary
    std::cout << std::endl;
    std::cout << "=== Test Summary ===" << std::endl;
    std::cout << "Passed: " << tests_passed << std::endl;
    std::cout << "Failed: " << tests_failed << std::endl;
    std::cout << "Total:  " << (tests_passed + tests_failed) << std::endl;
    
    return tests_failed > 0 ? 1 : 0;
}
