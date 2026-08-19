// agent.cpp
// Класс агента симуляции ALife - реализация
#include "alife/agent.h"
#include "alife/world.h"
#include "alife/math_utils.h"
#include <cmath>
#include <stdexcept>

namespace alife {

// Инициализация статического счётчика ID
int Agent::next_id_ = 1;

Agent::Agent(
    double pos_x,
    double pos_y,
    const Genome& genome,
    int generation,
    const std::optional<std::vector<double>>& parent_weights,
    RNG* rng
) : id(next_id_++),
    pos_x(pos_x),
    pos_y(pos_y),
    angle((rng ? rng->next_float() : default_rng_.next_float()) * 2.0 * M_PI - M_PI),
    genome(genome),
    brain(genome, 
          genome.n_hidden > 0 ? std::optional<int>(genome.n_hidden) : std::nullopt,
          parent_weights,
          rng),
    hormones(genome),
    energy(START_ENERGY),
    age(0.0),
    generation(generation),
    alive(true),
    repro_cooldown(REPRODUCE_COOLDOWN * ((rng ? rng->next_float() : default_rng_.next_float()) * 0.5 + 0.3)),
    last_pain(0.0),
    pending_reward(0.0),
    pending_punishment(0.0),
    nearest_food(std::nullopt),
    nearest_agent(std::nullopt),
    rng_(rng ? rng : &default_rng_)
{
}

bool Agent::can_reproduce() const {
    return (
        alive &&
        age > MATURE_AGE &&
        energy > REPRO_ENERGY &&
        repro_cooldown <= 0.0 &&
        hormones.depression < 0.85
    );
}

std::vector<double> Agent::make_sensors() const {
    std::vector<double> sensors(12, 0.0);
    
    // Sensor 0: hunger
    double hunger = 1.0 - clamp(energy / MAX_ENERGY, 0.0, 1.0);
    sensors[0] = hunger;
    
    // Sensors 1-3: food
    if (nearest_food.has_value()) {
        const auto& nf = nearest_food.value();
        if (nf.distance < SENSE_RANGE && !nf.eaten) {
            double rel = normalize_angle(nf.abs_angle - angle);
            double prox = 1.0 - nf.distance / SENSE_RANGE;
            sensors[1] = prox;
            if (rel < 0.0) {
                sensors[2] = std::min(1.0, -rel / M_PI);
            } else {
                sensors[3] = std::min(1.0, rel / M_PI);
            }
        }
    }
    
    // Sensors 4-7, 11: other agents
    if (nearest_agent.has_value()) {
        const auto& na = nearest_agent.value();
        if (na.distance < SENSE_RANGE && na.alive) {
            double rel = normalize_angle(na.abs_angle - angle);
            double prox = 1.0 - na.distance / SENSE_RANGE;
            sensors[4] = prox;
            if (rel < 0.0) {
                sensors[5] = std::min(1.0, -rel / M_PI);
            } else {
                sensors[6] = std::min(1.0, rel / M_PI);
            }
            sensors[7] = na.kin_sim * prox;
            if (na.distance < SOCIAL_RANGE) {
                sensors[11] = 1.0;
            }
        }
    }
    
    // Sensor 8: wall front
    double dist_left = pos_x - AGENT_RADIUS;
    double dist_right = WORLD_W - AGENT_RADIUS - pos_x;
    double dist_bottom = pos_y - AGENT_RADIUS;
    double dist_top = WORLD_H - AGENT_RADIUS - pos_y;
    double wall_dist = std::min(dist_left, std::min(dist_right, std::min(dist_bottom, dist_top)));
    double wall_front = std::max(0.0, 1.0 - wall_dist / SENSE_RANGE);
    sensors[8] = wall_front;
    
    // Sensor 9: pain
    sensors[9] = clamp(last_pain, 0.0, 1.0);
    
    // Sensor 10: cortisol
    sensors[10] = clamp(hormones.C / 2.0, 0.0, 1.0);
    
    return sensors;
}

void Agent::bounce() {
    double r = AGENT_RADIUS;
    
    if (pos_x < r) {
        pos_x = r;
        angle = M_PI - angle;
    } else if (pos_x > WORLD_W - r) {
        pos_x = WORLD_W - r;
        angle = M_PI - angle;
    }
    
    if (pos_y < r) {
        pos_y = r;
        angle = -angle;
    } else if (pos_y > WORLD_H - r) {
        pos_y = WORLD_H - r;
        angle = -angle;
    }
    
    angle = normalize_angle(angle);
}

Agent Agent::make_child(const Agent& mate, RNG* rng) const {
    RNG local_rng_copy = *rng_;  // Копируем RNG
    RNG* local_rng = rng ? rng : &local_rng_copy;
    
    // Кроссовер и мутация генома
    Genome child_genome = Genome::crossover(genome, mate.genome, local_rng);
    child_genome.mutate(local_rng);
    
    // Наследование весов мозга (Lamarckian)
    std::optional<std::vector<double>> parent_weights = std::nullopt;
    if (LAMARCKIAN && brain.W.size() == mate.brain.W.size()) {
        parent_weights = std::vector<double>(brain.W.size());
        for (size_t i = 0; i < brain.W.size(); ++i) {
            (*parent_weights)[i] = (brain.W[i] + mate.brain.W[i]) * 0.5;
        }
    }
    
    // Позиция потомка (средняя позиция родителей + небольшой разброс)
    double child_pos_x = (pos_x + mate.pos_x) * 0.5 + (local_rng->next_float() * 24.0 - 12.0);
    double child_pos_y = (pos_y + mate.pos_y) * 0.5 + (local_rng->next_float() * 24.0 - 12.0);
    
    // Clamp позиции к границам мира
    child_pos_x = clamp(child_pos_x, AGENT_RADIUS, WORLD_W - AGENT_RADIUS);
    child_pos_y = clamp(child_pos_y, AGENT_RADIUS, WORLD_H - AGENT_RADIUS);
    
    // Поколение потомка
    int child_generation = std::max(generation, mate.generation) + 1;
    
    return Agent(child_pos_x, child_pos_y, child_genome, child_generation, parent_weights, local_rng);
}

void Agent::update(World& world, double dt) {
    // Обновление возраста и cooldown
    age += dt;
    repro_cooldown -= dt;
    
    // Метаболизм
    energy -= genome["metabolism"] * dt;
    
    // Затухание боли
    last_pain *= 0.92;
    
    // Получение сенсоров
    double hunger = 1.0 - clamp(energy / MAX_ENERGY, 0.0, 1.0);
    std::vector<double> sensors = make_sensors();
    
    // Эффекты гормонов
    std::map<std::string, double> eff = hormones.effects(genome, hunger);
    
    // Нейромодуляторы для мозга
    std::map<std::string, double> neuromod;
    neuromod["plasticity"] = eff["plasticity"];
    neuromod["dopamine"] = eff["dopamine_signal"];
    neuromod["arousal"] = eff["arousal"];
    
    // Шаг мозга
    std::vector<double> out = brain.step(sensors, neuromod);
    
    // Выходные сигналы (clamped к [0, 1])
    double left = clamp(out[0], 0.0, 1.0);
    double right = clamp(out[1], 0.0, 1.0);
    double forward = clamp(out[2], 0.0, 1.0);
    double backward = clamp(out[3], 0.0, 1.0);
    double eat = clamp(out[4], 0.0, 1.0);
    double attack = clamp(out[5], 0.0, 1.0);
    
    // Рефлексная помощь
    double reflex_turn = 0.0;
    double reflex_forward = 0.0;
    double reflex_eat = 0.0;
    
    if (REFLEX_ASSIST) {
        // Избегание стен
        if (sensors[8] > 0.70) {
            reflex_turn += 0.22 * (rng_->next_float() < 0.5 ? 1.0 : -1.0);
        }
        
        // Движение к еде при голоде
        double food_prox = sensors[1];
        if (hunger > 0.35 && food_prox > 0.05) {
            reflex_turn += 0.22 * (sensors[3] - sensors[2]);
            reflex_forward += 0.15 * food_prox;
        }
        
        // Попытка есть при близости к еде
        if (food_prox > 0.8) {
            reflex_eat += 0.5;
        }
        
        // Дополнительное движение при сильном голоде
        if (hunger > 0.6) {
            reflex_forward += 0.05;
        }
    }
    
    // Вычисление поворота
    double turn = (left - right) * TURN_RATE * dt + reflex_turn * dt;
    
    // Слом: случайный поворот
    if (eff["breakdown"] > 0.5) {
        turn += (rng_->next_float() - 0.5) * dt;
    }
    
    // Шум в движении
    forward = clamp(forward + (rng_->next_float() * 0.7 - 0.2), 0.0, 1.0);
    attack = clamp(attack + rng_->next_float() * 0.4, 0.0, 1.0);
    
    // Депрессия: замедление
    if (eff["depression"] > 0.5) {
        forward *= 0.45;
        eat *= 0.55;
        attack *= 0.5;
        reflex_forward *= 0.3;
    }
    
    // Мощность движения
    double move_power = (forward - backward + reflex_forward);
    move_power *= (0.4 + 0.6 * clamp(energy / MAX_ENERGY, 0.0, 1.0));
    if (eff["depression"] > 0.5) {
        move_power *= 0.55;
    }
    
    // Применение движения
    angle += turn;
    pos_x += std::cos(angle) * move_power * MAX_SPEED * dt;
    pos_y += std::sin(angle) * move_power * MAX_SPEED * dt;
    bounce();
    
    // События для гормонов
    std::map<std::string, double> events;
    events["reward"] = pending_reward;
    events["punishment"] = pending_punishment;
    events["social"] = 0.0;
    events["kin"] = 0.0;
    events["conflict"] = 0.0;
    events["dominance"] = 0.0;
    events["hunger"] = hunger;
    events["injury"] = last_pain;
    events["fear"] = 0.0;
    
    pending_reward = 0.0;
    pending_punishment = 0.0;
    
    // Социальные события
    if (nearest_agent.has_value()) {
        const auto& na = nearest_agent.value();
        if (na.distance < SOCIAL_RANGE && na.alive) {
            events["social"] = 1.0;
            events["kin"] = na.kin_sim;
            
            if (eff["sociality"] > 0.6) {
                events["reward"] += 0.015 + 0.04 * na.kin_sim * eff["sociality"];
            }
        }
    }
    
    // Поедание еды
    if (nearest_food.has_value()) {
        const auto& nf = nearest_food.value();
        if (!nf.eaten && nf.distance < EAT_RANGE) {
            double eat_drive = eat + reflex_eat;
            if (eat_drive > EAT_THRESHOLD) {
                // Помечаем еду как съеденную через World
                world.mark_food_eaten(nf.pos_x, nf.pos_y);
                energy = std::min(MAX_ENERGY, energy + nf.nutrition);
                events["reward"] += 1.0;
            }
        }
    }
    
    // Атака других агентов
    if (nearest_agent.has_value()) {
        const auto& na = nearest_agent.value();
        if (na.distance < ATTACK_RANGE && na.alive) {
            double attack_drive = attack * eff["aggression"];
            
            if (REFLEX_ASSIST && hunger > 0.8) {
                attack_drive += 0.05;
            }
            
            if (eff["breakdown"] > 0.5) {
                attack_drive += rng_->next_float() * 0.3;
            }
            
            attack_drive *= (1.0 - clamp(0.65 * na.kin_sim * eff["sociality"], 0.0, 0.9));
            
            if (attack_drive > ATTACK_THRESHOLD) {
                // Наносим урон через World
                world.damage_agent(id, ATTACK_DAMAGE);
                
                last_pain = 1.0;
                pending_punishment += 0.8;
                
                // Атакующий тратит энергию
                energy -= ATTACK_COST;
                
                events["conflict"] = 1.0;
                
                if (eff["aggression_gain"] > 0.8) {
                    events["reward"] += 0.12;
                } else {
                    events["punishment"] += 0.05;
                }
            }
        }
    }
    
    // Слом: дополнительный расход энергии
    if (eff["breakdown"] > 0.5) {
        energy -= 0.05 * dt;
    }
    
    // Обновление гормонов
    hormones.update(dt, events, genome);
    
    // Проверка смерти
    if (energy <= 0.0 || age > MAX_AGE) {
        alive = false;
        return;
    }
    
    // Размножение
    if (can_reproduce() && nearest_agent.has_value()) {
        const auto& na = nearest_agent.value();
        if (na.distance < 55.0 && na.alive) {
            // Проверяем может ли партнёр размножаться (через World)
            if (world.can_agent_reproduce(na.abs_angle)) {  // Используем abs_angle как временный ID
                double compat = 0.35 + 0.65 * na.kin_sim;
                double mate_social = clamp(0.5, 0.0, 1.0);  // Заглушка, нужно получить от партнёра
                double chance = REPRO_BASE * eff["sociality"] * compat * (0.3 + mate_social);
                
                if (rng_->next_float() < chance) {
                    // Размножение будет обработано через World
                    world.request_reproduction(id, na.abs_angle, eff["sociality"]);
                }
            }
        }
    }
}

} // namespace alife
