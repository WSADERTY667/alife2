/**
 * @file genome.cpp
 * @brief Реализация генома и генетических операций.
 */

#include "alife/genome.h"
#include "alife/math_utils.h"
#include <algorithm>
#include <stdexcept>
#include <set>

namespace alife {

// Инициализация GENOME_KEYS
const std::vector<std::string> GENOME_KEYS = {
    "mutation_rate", "conn_prob", "weight_scale", "weight_max",
    "membrane_decay", "threshold", "stdp_rate", "plasticity_gain",
    "dopamine_base", "dopamine_reactivity", "dopamine_decay", "dopamine_sensitivity",
    "serotonin_base", "serotonin_decay", "serotonin_sensitivity",
    "oxytocin_base", "oxytocin_gain", "oxytocin_decay", "oxytocin_sensitivity",
    "cortisol_base", "cortisol_reactivity", "cortisol_decay", "cortisol_sensitivity",
    "testosterone_base", "testosterone_reactivity", "testosterone_decay", "testosterone_sensitivity",
    "aggression_gain", "social_gain",
    "lamarckian_weight", "metabolism",
    "brain_arch_mutability",
    "stress_resilience",
    "social_temperament",
};

// Инициализация BOUNDS
const std::map<std::string, std::pair<double, double>> BOUNDS = {
    {"mutation_rate", {0.001, 0.30}},
    {"conn_prob", {0.02, 0.25}},
    {"weight_scale", {0.05, 1.5}},
    {"weight_max", {0.5, 3.0}},
    {"membrane_decay", {0.70, 0.98}},
    {"threshold", {0.5, 1.8}},
    {"stdp_rate", {0.0005, 0.05}},
    {"plasticity_gain", {0.1, 2.5}},
    {"dopamine_base", {0.2, 1.0}},
    {"dopamine_reactivity", {0.1, 2.0}},
    {"dopamine_decay", {0.01, 0.20}},
    {"dopamine_sensitivity", {0.5, 2.0}},
    {"serotonin_base", {0.2, 1.0}},
    {"serotonin_decay", {0.01, 0.20}},
    {"serotonin_sensitivity", {0.5, 2.0}},
    {"oxytocin_base", {0.1, 0.8}},
    {"oxytocin_gain", {0.1, 2.0}},
    {"oxytocin_decay", {0.01, 0.20}},
    {"oxytocin_sensitivity", {0.5, 2.0}},
    {"cortisol_base", {0.05, 0.6}},
    {"cortisol_reactivity", {0.1, 2.0}},
    {"cortisol_decay", {0.01, 0.30}},
    {"cortisol_sensitivity", {0.5, 2.0}},
    {"testosterone_base", {0.1, 1.0}},
    {"testosterone_reactivity", {0.1, 2.0}},
    {"testosterone_decay", {0.01, 0.30}},
    {"testosterone_sensitivity", {0.5, 2.0}},
    {"aggression_gain", {0.0, 2.0}},
    {"social_gain", {0.0, 2.0}},
    {"lamarckian_weight", {0.0, 0.9}},
    {"metabolism", {0.01, 0.10}},
    {"brain_arch_mutability", {0.0, 0.15}},
    {"stress_resilience", {0.1, 0.9}},
    {"social_temperament", {0.1, 0.9}},
};

// Инициализация MUT_SCALE
const std::map<std::string, double> MUT_SCALE = []() {
    std::map<std::string, double> scale;
    for (const auto& key : GENOME_KEYS) {
        auto it = BOUNDS.find(key);
        if (it != BOUNDS.end()) {
            double range = it->second.second - it->second.first;
            scale[key] = std::max(1e-5, range * 0.08);
        }
    }
    return scale;
}();

// Инициализация KIN_KEYS
const std::vector<std::string> KIN_KEYS = {
    "conn_prob", "threshold",
    "dopamine_base", "serotonin_base",
    "oxytocin_gain", "cortisol_decay",
    "aggression_gain", "social_gain",
    "cortisol_sensitivity", "oxytocin_sensitivity",
};

Genome::Genome(
    const std::map<std::string, double>* genes,
    int tag,
    const std::vector<std::string>& tribal_tags,
    int n_hidden,
    RNG* rng
) : rng_(rng ? rng : &default_rng_),
    tribal_tags(tribal_tags),
    n_hidden(n_hidden >= 0 ? n_hidden : DEFAULT_N_HIDDEN) {
    
    if (genes) {
        this->genes = *genes;
    } else {
        // Генерируем случайные значения для всех генов
        for (const auto& key : GENOME_KEYS) {
            auto it = BOUNDS.find(key);
            if (it != BOUNDS.end()) {
                this->genes[key] = rng_->uniform(it->second.first, it->second.second);
            }
        }
    }
    
    if (tag >= 0) {
        this->tag = tag;
    } else {
        this->tag = rng_->randint(0, TAG_COLOR_COUNT - 1);
    }
}

double Genome::operator[](const std::string& key) const {
    auto it = genes.find(key);
    if (it == genes.end()) {
        throw std::out_of_range("Ген не найден: " + key);
    }
    return it->second;
}

double& Genome::operator[](const std::string& key) {
    auto it = genes.find(key);
    if (it == genes.end()) {
        throw std::out_of_range("Ген не найден: " + key);
    }
    return it->second;
}

double Genome::get(const std::string& key, double default_value) const {
    auto it = genes.find(key);
    if (it == genes.end()) {
        return default_value;
    }
    return it->second;
}

void Genome::mutate(RNG* rng) {
    RNG* r = rng ? rng : rng_;
    
    double mr = clamp(get("mutation_rate", 0.08), 0.0, 0.5);
    
    // Мутация генов
    for (const auto& key : GENOME_KEYS) {
        if (r->next_float() < mr) {
            auto scale_it = MUT_SCALE.find(key);
            auto bounds_it = BOUNDS.find(key);
            if (scale_it != MUT_SCALE.end() && bounds_it != BOUNDS.end()) {
                double mutation = r->gauss(0.0, scale_it->second);
                genes[key] = clamp(genes[key] + mutation, bounds_it->second.first, bounds_it->second.second);
            }
        }
    }
    
    // Мутация тега
    if (r->next_float() < mr * 0.35) {
        tag = r->randint(0, TAG_COLOR_COUNT - 1);
    }
    
    // Мутация архитектуры мозга
    double arch_mut = clamp(get("brain_arch_mutability", 0.05), 0.0, 0.5);
    if (r->next_float() < arch_mut) {
        static const std::vector<int> deltas = {-8, -4, 4, 8};
        int delta = r->choice(deltas);
        n_hidden = std::max(40, std::min(400, n_hidden + delta));
    }
    
    // Мутация племенных тегов
    if (r->next_float() < mr * 0.05) {
        std::string new_tag = "mut_" + std::to_string(r->randint(1000, 9999));
        
        // Проверяем, есть ли уже такой тег
        bool exists = false;
        for (const auto& t : tribal_tags) {
            if (t == new_tag) {
                exists = true;
                break;
            }
        }
        
        if (!exists) {
            tribal_tags.push_back(new_tag);
            if (static_cast<int>(tribal_tags.size()) > 5) {
                tribal_tags.erase(tribal_tags.begin());
            }
        }
    }
}

Genome Genome::crossover(const Genome& a, const Genome& b, RNG* rng) {
    RNG r_local(0);
    RNG* r = rng ? rng : &r_local;
    
    std::map<std::string, double> child_genes;
    for (const auto& key : GENOME_KEYS) {
        double rv = r->next_float();
        double value;
        if (rv < 0.45) {
            value = a[key];
        } else if (rv < 0.90) {
            value = b[key];
        } else {
            value = (a[key] + b[key]) * 0.5;
        }
        child_genes[key] = value;
    }
    
    int child_tag = (r->next_float() < 0.5) ? a.tag : b.tag;
    
    // Наследование племенных тегов - комбинация от обоих родителей
    std::set<std::string> unique_tags;
    for (const auto& t : a.tribal_tags) {
        unique_tags.insert(t);
    }
    for (const auto& t : b.tribal_tags) {
        unique_tags.insert(t);
    }
    
    std::vector<std::string> child_tribal_tags;
    int count = 0;
    for (const auto& t : unique_tags) {
        if (count >= 5) break;
        child_tribal_tags.push_back(t);
        count++;
    }
    
    // Наследование архитектуры мозга
    int child_n_hidden = static_cast<int>((a.n_hidden + b.n_hidden) / 2);
    static const std::vector<int> variations = {-4, 0, 0, 0, 4};
    int variation = r->choice(variations);
    child_n_hidden = std::max(40, std::min(400, child_n_hidden + variation));
    
    return Genome(&child_genes, child_tag, child_tribal_tags, child_n_hidden, rng);
}

double genome_similarity(const Genome& g1, const Genome& g2) {
    double total = 0.0;
    
    // Схожесть по генам
    for (const auto& key : KIN_KEYS) {
        auto it = BOUNDS.find(key);
        if (it != BOUNDS.end()) {
            double lo = it->second.first;
            double hi = it->second.second;
            double rng_val = std::max(1e-6, hi - lo);
            double diff = std::abs(g1[key] - g2[key]);
            total += diff / rng_val;
        }
    }
    
    double gene_sim = 1.0 - clamp(total / static_cast<double>(KIN_KEYS.size()), 0.0, 1.0);
    
    // Схожесть визуального тега
    double tag_sim = (g1.tag == g2.tag) ? 1.0 : 0.0;
    
    // Учет племенных тегов
    double tag_overlap = 0.0;
    if (!g1.tribal_tags.empty() && !g2.tribal_tags.empty()) {
        std::set<std::string> set1(g1.tribal_tags.begin(), g1.tribal_tags.end());
        std::set<std::string> set2(g2.tribal_tags.begin(), g2.tribal_tags.end());
        
        int shared_count = 0;
        for (const auto& t : set1) {
            if (set2.count(t) > 0) {
                shared_count++;
            }
        }
        
        size_t max_size = std::max(set1.size(), set2.size());
        tag_overlap = static_cast<double>(shared_count) / static_cast<double>(max_size);
    }
    
    // Схожесть архитектуры мозга
    int n_hidden_diff = std::abs(g1.n_hidden - g2.n_hidden);
    double arch_sim = 1.0 - clamp(static_cast<double>(n_hidden_diff) / 200.0, 0.0, 1.0);
    
    // Комбинированная схожесть
    double result = 0.5 * gene_sim + 0.15 * tag_sim + 0.2 * tag_overlap + 0.15 * arch_sim;
    return clamp(result, 0.0, 1.0);
}

} // namespace alife
