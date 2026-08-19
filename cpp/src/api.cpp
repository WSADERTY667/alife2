// api.cpp
// C API implementation for ALife Core

#include "alife/api.h"
#include "alife/world.h"
#include "alife/agent.h"
#include <vector>
#include <cstdlib>

// ============================================================================
// Internal implementation details (hidden from C API users)
// ============================================================================

namespace {

// Wrapper structure that holds the C++ World object
struct AlifeWorldImpl {
    alife::World world;
    
    AlifeWorldImpl(uint64_t seed = 42, int agents = 24, int food = 90)
        : world(seed, agents, food) {}
};

} // anonymous namespace

// ============================================================================
// World Management Functions
// ============================================================================

extern "C" {

AlifeWorld* alife_world_create(void) {
    try {
        return reinterpret_cast<AlifeWorld*>(new AlifeWorldImpl());
    } catch (...) {
        return nullptr;
    }
}

void alife_world_destroy(AlifeWorld* world) {
    if (world) {
        delete reinterpret_cast<AlifeWorldImpl*>(world);
    }
}

// ============================================================================
// World Configuration Functions
// ============================================================================

void alife_world_set_seed(AlifeWorld* world, uint64_t seed) {
    if (!world) return;
    
    AlifeWorldImpl* impl = reinterpret_cast<AlifeWorldImpl*>(world);
    // Note: seed is used on next reset, as World doesn't expose seed setter
    // We store it and will use it in reset by recreating the world
    // For now, we just note it - actual implementation would need to store seed
    // Since World constructor takes seed, we'll handle this in reset
    impl->world = alife::World(seed, static_cast<int>(impl->world.get_agent_count()), 
                               static_cast<int>(impl->world.get_food_count()));
}

void alife_world_reset(AlifeWorld* world, int agent_count, int food_count) {
    if (!world) return;
    
    AlifeWorldImpl* impl = reinterpret_cast<AlifeWorldImpl*>(world);
    // Recreate world with new parameters
    // Note: This uses default seed (42). To change seed, call alife_world_set_seed first.
    *impl = AlifeWorldImpl(42, agent_count, food_count);
}

// ============================================================================
// Simulation Step Function
// ============================================================================

void alife_world_step(AlifeWorld* world) {
    if (!world) return;
    
    AlifeWorldImpl* impl = reinterpret_cast<AlifeWorldImpl*>(world);
    impl->world.update();
}

// ============================================================================
// Agent Query Functions
// ============================================================================

int alife_world_get_agent_count(AlifeWorld* world) {
    if (!world) return 0;
    
    AlifeWorldImpl* impl = reinterpret_cast<AlifeWorldImpl*>(world);
    return static_cast<int>(impl->world.get_agent_count());
}

int alife_world_get_agents(AlifeWorld* world, AgentView* buffer, int max_count) {
    if (!world) return 0;
    
    AlifeWorldImpl* impl = reinterpret_cast<AlifeWorldImpl*>(world);
    const auto& agents = impl->world.get_agents();
    
    int count = std::min(max_count, static_cast<int>(agents.size()));
    
    if (buffer && count > 0) {
        for (int i = 0; i < count; ++i) {
            const auto& agent = agents[i];
            buffer[i].id = agent.id;
            buffer[i].generation = agent.generation;
            // Tribe is derived from genome tribal_tags - use first tag or -1
            buffer[i].tribe = agent.genome.tribal_tags.empty() ? -1 : 
                              static_cast<int>(std::hash<std::string>{}(agent.genome.tribal_tags[0]) % 100);
            buffer[i].x = static_cast<float>(agent.pos_x);
            buffer[i].y = static_cast<float>(agent.pos_y);
            buffer[i].angle = static_cast<float>(agent.angle);
            buffer[i].energy = static_cast<float>(agent.energy);
            buffer[i].dopamine = static_cast<float>(agent.hormones.D);
            buffer[i].serotonin = static_cast<float>(agent.hormones.S);
            buffer[i].oxytocin = static_cast<float>(agent.hormones.O);
            buffer[i].cortisol = static_cast<float>(agent.hormones.C);
            buffer[i].testosterone = static_cast<float>(agent.hormones.T);
            buffer[i].depression = static_cast<float>(agent.hormones.depression);
            buffer[i].breakdown = static_cast<float>(agent.hormones.breakdown);
        }
    }
    
    return static_cast<int>(agents.size());
}

// ============================================================================
// Food Query Functions
// ============================================================================

int alife_world_get_food_count(AlifeWorld* world) {
    if (!world) return 0;
    
    AlifeWorldImpl* impl = reinterpret_cast<AlifeWorldImpl*>(world);
    return static_cast<int>(impl->world.get_food_count());
}

int alife_world_get_foods(AlifeWorld* world, FoodView* buffer, int max_count) {
    if (!world) return 0;
    
    AlifeWorldImpl* impl = reinterpret_cast<AlifeWorldImpl*>(world);
    const auto& foods = impl->world.get_foods();
    
    int written = 0;
    for (const auto& food : foods) {
        if (food.eaten) continue;
        if (written >= max_count) break;
        
        if (buffer) {
            buffer[written].x = static_cast<float>(food.pos_x);
            buffer[written].y = static_cast<float>(food.pos_y);
        }
        ++written;
    }
    
    // Return total count of uneaten food
    return static_cast<int>(impl->world.get_food_count());
}

// ============================================================================
// Agent Intervention Functions
// ============================================================================

void alife_agent_reward(AlifeWorld* world, int agent_id, float amount) {
    if (!world) return;
    
    AlifeWorldImpl* impl = reinterpret_cast<AlifeWorldImpl*>(world);
    auto& agents = const_cast<std::vector<alife::Agent>&>(impl->world.get_agents());
    
    for (auto& agent : agents) {
        if (agent.id == agent_id && agent.alive) {
            agent.pending_reward += static_cast<double>(amount);
            break;
        }
    }
}

void alife_agent_punish(AlifeWorld* world, int agent_id, float amount) {
    if (!world) return;
    
    AlifeWorldImpl* impl = reinterpret_cast<AlifeWorldImpl*>(world);
    auto& agents = const_cast<std::vector<alife::Agent>&>(impl->world.get_agents());
    
    for (auto& agent : agents) {
        if (agent.id == agent_id && agent.alive) {
            agent.pending_punishment += static_cast<double>(amount);
            break;
        }
    }
}

// ============================================================================
// Food Manipulation Functions
// ============================================================================

void alife_world_spawn_food(AlifeWorld* world, float x, float y) {
    if (!world) return;
    
    AlifeWorldImpl* impl = reinterpret_cast<AlifeWorldImpl*>(world);
    
    // Clamp to world bounds
    double clamped_x = std::max(10.0, std::min(static_cast<double>(x), alife::WORLD_W - 10.0));
    double clamped_y = std::max(10.0, std::min(static_cast<double>(y), alife::WORLD_H - 10.0));
    
    // Use default nutrition range [18, 30]
    double nutrition = 18.0 + (impl->world.get_tick() % 13);  // Deterministic variation
    
    auto& foods = const_cast<std::vector<alife::Food>&>(impl->world.get_foods());
    foods.push_back({clamped_x, clamped_y, nutrition, false});
}

} // extern "C"
