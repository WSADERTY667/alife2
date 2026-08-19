// world.cpp
// Класс мира симуляции ALife - реализация
#include "alife/world.h"
#include "alife/math_utils.h"
#include <cmath>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <iomanip>

namespace alife {

World::World(uint64_t seed, int initial_agents, int initial_food)
    : tick_(0),
      seed_(seed),
      rng_(seed)
{
    // Инициализация статистики поколений
    gen_stats_.max_generation = 0;
    
    // Спавн еды
    for (int i = 0; i < initial_food; ++i) {
        spawn_food();
    }
    
    // Спавн агентов
    for (int i = 0; i < initial_agents; ++i) {
        spawn_random_agent();
    }
}

void World::spawn_food() {
    double pos_x = rng_.next_float() * (WORLD_W - 20.0) + 10.0;
    double pos_y = rng_.next_float() * (WORLD_H - 20.0) + 10.0;
    double nutrition = rng_.next_float() * 12.0 + 18.0;  // [18, 30]
    
    foods_.push_back({pos_x, pos_y, nutrition, false});
}

void World::spawn_random_agent() {
    Genome genome({}, -1, {}, -1, &rng_);
    genome.mutate(&rng_);
    
    double pos_x = rng_.next_float() * (WORLD_W - 60.0) + 30.0;
    double pos_y = rng_.next_float() * (WORLD_H - 60.0) + 30.0;
    
    agents_.emplace_back(pos_x, pos_y, genome, 0, std::nullopt, &rng_);
}

std::optional<NearestFood> World::find_nearest_food(double pos_x, double pos_y) const {
    std::optional<NearestFood> best = std::nullopt;
    double best_d = 1e18;
    
    for (const auto& f : foods_) {
        if (f.eaten) continue;
        
        double dx = f.pos_x - pos_x;
        double dy = f.pos_y - pos_y;
        double d = std::sqrt(dx * dx + dy * dy);
        
        if (d < best_d) {
            best_d = d;
            double angle = std::atan2(dy, dx);
            best = NearestFood{d, angle, f.eaten, f.nutrition, f.pos_x, f.pos_y};
        }
    }
    
    return best;
}

std::optional<NearestAgent> World::find_nearest_agent(int agent_id) const {
    const Agent* self = nullptr;
    for (const auto& a : agents_) {
        if (a.id == agent_id) {
            self = &a;
            break;
        }
    }
    
    if (!self) return std::nullopt;
    
    std::optional<NearestAgent> best = std::nullopt;
    double best_d = 1e18;
    
    for (const auto& other : agents_) {
        if (other.id == agent_id || !other.alive) continue;
        
        double dx = other.pos_x - self->pos_x;
        double dy = other.pos_y - self->pos_y;
        double d = std::sqrt(dx * dx + dy * dy);
        
        if (d < best_d) {
            best_d = d;
            double angle = std::atan2(dy, dx);
            double kin_sim = genome_similarity(self->genome, other.genome);
            best = NearestAgent{d, angle, other.alive, kin_sim};
        }
    }
    
    return best;
}

void World::mark_food_eaten(double pos_x, double pos_y) {
    const double EPS = 1.0;  // Точность поиска
    for (auto& f : foods_) {
        if (!f.eaten) {
            double dx = f.pos_x - pos_x;
            double dy = f.pos_y - pos_y;
            if (std::abs(dx) < EPS && std::abs(dy) < EPS) {
                f.eaten = true;
                return;
            }
        }
    }
}

void World::damage_agent(int agent_id, double damage) {
    for (auto& a : agents_) {
        if (a.id == agent_id && a.alive) {
            a.energy -= damage;
            a.last_pain = 1.0;
            a.pending_punishment += 0.8;
            a.hormones.C = clamp(a.hormones.C + 0.12, 0.0, 2.0);
            return;
        }
    }
}

bool World::can_agent_reproduce(int agent_id) const {
    for (const auto& a : agents_) {
        if (a.id == agent_id) {
            return a.can_reproduce();
        }
    }
    return false;
}

void World::request_reproduction(int parent1_id, int parent2_id, double sociality) {
    reproduction_requests_.emplace_back(parent1_id, parent2_id, sociality);
}

size_t World::get_food_count() const {
    size_t count = 0;
    for (const auto& f : foods_) {
        if (!f.eaten) ++count;
    }
    return count;
}

void World::update_generation_stats() {
    std::map<int, int> gen_counts;
    std::map<std::string, std::map<std::string, double>> lineage_data;
    
    for (const auto& agent : agents_) {
        int gen = agent.generation;
        gen_counts[gen]++;
        
        // Обновление max_generation
        if (gen > gen_stats_.max_generation) {
            gen_stats_.max_generation = gen;
        }
        
        // Статистика по tribal tags
        for (const auto& tag : agent.genome.tribal_tags) {
            lineage_data[tag]["count"]++;
            lineage_data[tag]["total_energy"] += agent.energy;
            
            // Min/max generation для тега
            if (lineage_data[tag].find("min_gen") == lineage_data[tag].end() || 
                gen < lineage_data[tag]["min_gen"]) {
                lineage_data[tag]["min_gen"] = static_cast<double>(gen);
            }
            if (lineage_data[tag].find("max_gen") == lineage_data[tag].end() || 
                gen > lineage_data[tag]["max_gen"]) {
                lineage_data[tag]["max_gen"] = static_cast<double>(gen);
            }
        }
    }
    
    gen_stats_.generation_counts = gen_counts;
    
    // Преобразование в формат для JSON
    gen_stats_.lineage_stats.clear();
    for (const auto& [tag, data] : lineage_data) {
        double avg_energy = data.at("total_energy") / data.at("count");
        gen_stats_.lineage_stats[tag] = {
            {"count", data.at("count")},
            {"avg_energy", avg_energy},
            {"min_gen", data.at("min_gen")},
            {"max_gen", data.at("max_gen")}
        };
    }
}

void World::update() {
    tick_++;
    newborns_.clear();
    reproduction_requests_.clear();
    
    // 1. Спавн новой еды (если меньше максимума)
    if (static_cast<int>(foods_.size()) < FOOD_MAX && rng_.next_float() < FOOD_RESPAWN) {
        spawn_food();
    }
    
    // 2. Поиск ближайших объектов для каждого агента
    for (auto& a : agents_) {
        if (!a.alive) continue;
        a.nearest_food = find_nearest_food(a.pos_x, a.pos_y);
        a.nearest_agent = find_nearest_agent(a.id);
    }
    
    // 3. Обновление агентов
    for (auto& a : agents_) {
        if (a.alive) {
            a.update(*this, 1.0);
        }
    }
    
    // 4. Обработка запросов на размножение
    for (const auto& [p1_id, p2_id, sociality] : reproduction_requests_) {
        // Находим родителей
        Agent* parent1 = nullptr;
        Agent* parent2 = nullptr;
        
        for (auto& a : agents_) {
            if (a.id == p1_id && a.alive) parent1 = &a;
            if (a.id == p2_id && a.alive) parent2 = &a;
        }
        
        if (parent1 && parent2 && parent1->can_reproduce() && parent2->can_reproduce()) {
            // Проверяем дистанцию ещё раз
            double dx = parent1->pos_x - parent2->pos_x;
            double dy = parent1->pos_y - parent2->pos_y;
            double dist = std::sqrt(dx * dx + dy * dy);
            
            if (dist < 55.0) {
                double mate_social = clamp(parent2->hormones.O, 0.0, 1.0);
                double compat = 0.35 + 0.65 * genome_similarity(parent1->genome, parent2->genome);
                double chance = REPRO_BASE * sociality * compat * (0.3 + mate_social);
                
                if (rng_.next_float() < chance) {
                    Agent child = parent1->make_child(*parent2, &rng_);
                    parent1->energy -= REPRO_COST;
                    parent2->energy -= REPRO_COST;
                    parent1->repro_cooldown = REPRODUCE_COOLDOWN;
                    parent2->repro_cooldown = REPRODUCE_COOLDOWN;
                    newborns_.push_back(std::move(child));
                }
            }
        }
    }
    
    // 5. Удаление съеденной еды
    foods_.erase(
        std::remove_if(foods_.begin(), foods_.end(),
            [](const Food& f) { return f.eaten; }),
        foods_.end()
    );
    
    // 6. Добавление новорождённых
    agents_.insert(agents_.end(), 
                   std::make_move_iterator(newborns_.begin()),
                   std::make_move_iterator(newborns_.end()));
    
    // 7. Удаление мёртвых агентов
    agents_.erase(
        std::remove_if(agents_.begin(), agents_.end(),
            [](const Agent& a) { return !a.alive; }),
        agents_.end()
    );
    
    // 8. Защита от вымирания: спавн новых агентов если популяция ниже минимума
    while (static_cast<int>(agents_.size()) < MIN_AGENTS) {
        spawn_random_agent();
    }
    
    // 9. Обновление статистики поколений каждые 100 тиков
    if (tick_ % 100 == 0) {
        update_generation_stats();
    }
}

std::string World::to_json(const std::optional<std::string>& path) const {
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(6);
    
    oss << "{\n";
    oss << "  \"schema_version\": 2,\n";
    oss << "  \"tick\": " << tick_ << ",\n";
    
    // Еда
    oss << "  \"foods\": [\n";
    bool first = true;
    for (const auto& f : foods_) {
        if (!first) oss << ",\n";
        first = false;
        oss << "    {\"pos\": [" << f.pos_x << ", " << f.pos_y << "], "
            << "\"nutrition\": " << f.nutrition << ", "
            << "\"eaten\": " << (f.eaten ? "true" : "false") << "}";
    }
    oss << "\n  ],\n";
    
    // Агенты
    oss << "  \"agents\": [\n";
    first = true;
    for (const auto& a : agents_) {
        if (!first) oss << ",\n";
        first = false;
        oss << "    {\n";
        oss << "      \"id\": " << a.id << ",\n";
        oss << "      \"generation\": " << a.generation << ",\n";
        oss << "      \"age\": " << a.age << ",\n";
        oss << "      \"energy\": " << a.energy << ",\n";
        oss << "      \"pos\": [" << a.pos_x << ", " << a.pos_y << "],\n";
        oss << "      \"angle\": " << a.angle << ",\n";
        oss << "      \"alive\": " << (a.alive ? "true" : "false") << "\n";
        oss << "    }";
    }
    oss << "\n  ],\n";
    
    // Статистика поколений
    oss << "  \"generation_stats\": {\n";
    oss << "    \"max_generation\": " << gen_stats_.max_generation << ",\n";
    oss << "    \"generation_counts\": {";
    first = true;
    for (const auto& [gen, count] : gen_stats_.generation_counts) {
        if (!first) oss << ", ";
        first = false;
        oss << "\"" << gen << "\": " << count;
    }
    oss << "}\n";
    oss << "  }\n";
    
    oss << "}\n";
    
    std::string result = oss.str();
    
    // Запись в файл если указан путь
    if (path.has_value()) {
        std::ofstream file(path.value());
        if (file.is_open()) {
            file << result;
            file.close();
        }
    }
    
    return result;
}

} // namespace alife
