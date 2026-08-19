/**
 * @file test_hormones.cpp
 * @brief Тесты для гормональной системы Hormones.
 * 
 * Проверяет:
 * - гормоны остаются в допустимых пределах;
 * - нет NaN после 1000 обновлений;
 * - depression и breakdown работают по тем же правилам;
 * - effects() возвращает все необходимые поля;
 * - совместимость с Python версией (golden values).
 */

#include <iostream>
#include <cmath>
#include <string>
#include <vector>
#include <map>
#include <cassert>
#include "alife/hormones.h"
#include "alife/math_utils.h"

// Золотые значения из Python версии
constexpr double INITIAL_D = 0.50000000000000000;
constexpr double INITIAL_S = 0.50000000000000000;
constexpr double INITIAL_O = 0.40000000000000002;
constexpr double INITIAL_C = 0.20000000000000001;
constexpr double INITIAL_T = 0.50000000000000000;
constexpr double INITIAL_allostatic = 0.00000000000000000;
constexpr double INITIAL_depression = 0.00000000000000000;
constexpr double INITIAL_breakdown = 0.00000000000000000;
constexpr double INITIAL_paranoia = 0.00000000000000000;
constexpr double INITIAL_trust = 0.50000000000000000;
constexpr double INITIAL_delayed_punishment = 0.00000000000000000;

constexpr double D_decay = 0.05000000000000000;
constexpr double S_decay = 0.05000000000000000;
constexpr double O_decay = 0.05000000000000000;
constexpr double C_decay = 0.05000000000000000;
constexpr double T_decay = 0.05000000000000000;
constexpr double S_sensitivity = 1.00000000000000000;
constexpr double O_sensitivity = 1.00000000000000000;
constexpr double C_sensitivity = 1.00000000000000000;
constexpr double T_sensitivity = 1.00000000000000000;
constexpr double D_sensitivity = 1.00000000000000000;
constexpr double stress_resilience = 0.50000000000000000;
constexpr double social_temperament = 0.50000000000000000;

// Финальные значения после 10 обновлений
constexpr double FINAL_D = 0.55196293121264650;
constexpr double FINAL_S = 0.48674439191709207;
constexpr double FINAL_O = 0.53794455499535554;
constexpr double FINAL_C = 0.54547317284904306;
constexpr double FINAL_T = 0.56830823440625000;
constexpr double FINAL_allostatic = 0.00000000000000000;
constexpr double FINAL_depression = 0.00000000000000000;
constexpr double FINAL_breakdown = 0.00000000000000000;
constexpr double FINAL_paranoia = 0.00000000000000000;
constexpr double FINAL_trust = 0.51313159754655013;
constexpr double FINAL_delayed_punishment = 0.49733333333333335;

// Эффекты при hunger=0.3
constexpr double EFFECTS_arousal = 0.57907564488097241;
constexpr double EFFECTS_plasticity = 0.19703897208395665;
constexpr double EFFECTS_aggression = 0.50632843949493134;
constexpr double EFFECTS_sociality = 0.26158897253873831;
constexpr double EFFECTS_dopamine_signal = 0.07794439681896975;
constexpr double EFFECTS_depression = 0.00000000000000000;
constexpr double EFFECTS_breakdown = 0.00000000000000000;
constexpr double EFFECTS_paranoia = 0.00000000000000000;
constexpr double EFFECTS_trust = 0.51313159754655013;
constexpr double EFFECTS_allostatic = 0.00000000000000000;

// Допустимая погрешность для сравнения с Python
constexpr double EPSILON = 1e-10;

struct Event {
    double dt;
    double reward;
    double punishment;
    double social;
    double kin;
    double conflict;
    double dominance;
    double hunger;
    double injury;
    double fear;
};

const std::vector<Event> test_events = {
    {1.0, 0.5, 0.0, 0.3, 0.0, 0.0, 0.0, 0.2, 0.0, 0.0},  // step 0
    {1.0, 0.0, 0.3, 0.0, 0.0, 0.0, 0.0, 0.3, 0.0, 0.1},  // step 1
    {1.0, 0.8, 0.0, 0.5, 0.2, 0.0, 0.0, 0.1, 0.0, 0.0},  // step 2
    {1.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.2, 0.4, 0.0, 0.0},  // step 3
    {1.0, 0.0, 0.6, 0.0, 0.0, 0.0, 0.0, 0.5, 0.3, 0.4},  // step 4
    {1.0, 0.3, 0.0, 0.8, 0.5, 0.0, 0.0, 0.2, 0.0, 0.0},  // step 5
    {1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.3, 0.0, 0.0},  // step 6
    {1.0, 0.0, 0.8, 0.0, 0.0, 0.0, 0.0, 0.6, 0.0, 0.5},  // step 7
    {1.0, 0.5, 0.0, 0.4, 0.0, 0.0, 0.0, 0.1, 0.0, 0.0},  // step 8
    {1.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.0, 0.4, 0.0, 0.2},  // step 9
};

bool approx_equal(double a, double b, double eps = EPSILON) {
    return std::abs(a - b) < eps;
}

bool is_nan(double value) {
    return std::isnan(value);
}

alife::Genome create_test_genome() {
    std::map<std::string, double> genes = {
        {"mutation_rate", 0.05},
        {"conn_prob", 0.1},
        {"weight_scale", 0.5},
        {"weight_max", 1.5},
        {"membrane_decay", 0.9},
        {"threshold", 1.0},
        {"stdp_rate", 0.01},
        {"plasticity_gain", 1.0},
        {"dopamine_base", 0.5},
        {"dopamine_reactivity", 1.0},
        {"dopamine_decay", 0.05},
        {"dopamine_sensitivity", 1.0},
        {"serotonin_base", 0.5},
        {"serotonin_decay", 0.05},
        {"serotonin_sensitivity", 1.0},
        {"oxytocin_base", 0.4},
        {"oxytocin_gain", 1.0},
        {"oxytocin_decay", 0.05},
        {"oxytocin_sensitivity", 1.0},
        {"cortisol_base", 0.2},
        {"cortisol_reactivity", 1.0},
        {"cortisol_decay", 0.05},
        {"cortisol_sensitivity", 1.0},
        {"testosterone_base", 0.5},
        {"testosterone_reactivity", 1.0},
        {"testosterone_decay", 0.05},
        {"testosterone_sensitivity", 1.0},
        {"aggression_gain", 1.0},
        {"social_gain", 1.0},
        {"lamarckian_weight", 0.5},
        {"metabolism", 0.05},
        {"brain_arch_mutability", 0.05},
        {"stress_resilience", 0.5},
        {"social_temperament", 0.5},
    };
    return alife::Genome(&genes);
}

int test_initial_state() {
    std::cout << "Test: Initial state... ";
    
    alife::Genome genome = create_test_genome();
    alife::Hormones hormones(genome);
    
    bool pass = true;
    pass &= approx_equal(hormones.D, INITIAL_D);
    pass &= approx_equal(hormones.S, INITIAL_S);
    pass &= approx_equal(hormones.O, INITIAL_O);
    pass &= approx_equal(hormones.C, INITIAL_C);
    pass &= approx_equal(hormones.T, INITIAL_T);
    pass &= approx_equal(hormones.allostatic, INITIAL_allostatic);
    pass &= approx_equal(hormones.depression, INITIAL_depression);
    pass &= approx_equal(hormones.breakdown, INITIAL_breakdown);
    pass &= approx_equal(hormones.paranoia, INITIAL_paranoia);
    pass &= approx_equal(hormones.trust, INITIAL_trust);
    
    if (pass) {
        std::cout << "PASSED" << std::endl;
        return 0;
    } else {
        std::cout << "FAILED" << std::endl;
        return 1;
    }
}

int test_update_sequence() {
    std::cout << "Test: Update sequence (10 steps)... ";
    
    alife::Genome genome = create_test_genome();
    alife::Hormones hormones(genome);
    
    for (const auto& ev : test_events) {
        std::map<std::string, double> events = {
            {"reward", ev.reward},
            {"punishment", ev.punishment},
            {"social", ev.social},
            {"kin", ev.kin},
            {"conflict", ev.conflict},
            {"dominance", ev.dominance},
            {"hunger", ev.hunger},
            {"injury", ev.injury},
            {"fear", ev.fear},
        };
        hormones.update(ev.dt, events, genome);
    }
    
    bool pass = true;
    pass &= approx_equal(hormones.D, FINAL_D);
    pass &= approx_equal(hormones.S, FINAL_S);
    pass &= approx_equal(hormones.O, FINAL_O);
    pass &= approx_equal(hormones.C, FINAL_C);
    pass &= approx_equal(hormones.T, FINAL_T);
    pass &= approx_equal(hormones.allostatic, FINAL_allostatic);
    pass &= approx_equal(hormones.depression, FINAL_depression);
    pass &= approx_equal(hormones.breakdown, FINAL_breakdown);
    pass &= approx_equal(hormones.paranoia, FINAL_paranoia);
    pass &= approx_equal(hormones.trust, FINAL_trust);
    pass &= approx_equal(hormones.delayed_punishment, FINAL_delayed_punishment);
    
    if (pass) {
        std::cout << "PASSED" << std::endl;
        return 0;
    } else {
        std::cout << "FAILED" << std::endl;
        std::cout << "  D: " << hormones.D << " (expected " << FINAL_D << ")" << std::endl;
        std::cout << "  S: " << hormones.S << " (expected " << FINAL_S << ")" << std::endl;
        std::cout << "  O: " << hormones.O << " (expected " << FINAL_O << ")" << std::endl;
        std::cout << "  C: " << hormones.C << " (expected " << FINAL_C << ")" << std::endl;
        std::cout << "  T: " << hormones.T << " (expected " << FINAL_T << ")" << std::endl;
        std::cout << "  trust: " << hormones.trust << " (expected " << FINAL_trust << ")" << std::endl;
        std::cout << "  delayed_punishment: " << hormones.delayed_punishment << " (expected " << FINAL_delayed_punishment << ")" << std::endl;
        return 1;
    }
}

int test_effects() {
    std::cout << "Test: Effects calculation... ";
    
    alife::Genome genome = create_test_genome();
    alife::Hormones hormones(genome);
    
    // Применяем ту же последовательность событий
    for (const auto& ev : test_events) {
        std::map<std::string, double> events = {
            {"reward", ev.reward},
            {"punishment", ev.punishment},
            {"social", ev.social},
            {"kin", ev.kin},
            {"conflict", ev.conflict},
            {"dominance", ev.dominance},
            {"hunger", ev.hunger},
            {"injury", ev.injury},
            {"fear", ev.fear},
        };
        hormones.update(ev.dt, events, genome);
    }
    
    auto effects = hormones.effects(genome, 0.3);
    
    bool pass = true;
    pass &= approx_equal(effects["arousal"], EFFECTS_arousal);
    pass &= approx_equal(effects["plasticity"], EFFECTS_plasticity);
    pass &= approx_equal(effects["aggression"], EFFECTS_aggression);
    pass &= approx_equal(effects["sociality"], EFFECTS_sociality);
    pass &= approx_equal(effects["dopamine_signal"], EFFECTS_dopamine_signal);
    pass &= approx_equal(effects["depression"], EFFECTS_depression);
    pass &= approx_equal(effects["breakdown"], EFFECTS_breakdown);
    pass &= approx_equal(effects["paranoia"], EFFECTS_paranoia);
    pass &= approx_equal(effects["trust"], EFFECTS_trust);
    pass &= approx_equal(effects["allostatic"], EFFECTS_allostatic);
    
    // Проверка наличия всех полей
    pass &= (effects.find("arousal") != effects.end());
    pass &= (effects.find("plasticity") != effects.end());
    pass &= (effects.find("aggression") != effects.end());
    pass &= (effects.find("sociality") != effects.end());
    pass &= (effects.find("dopamine_signal") != effects.end());
    pass &= (effects.find("depression") != effects.end());
    pass &= (effects.find("breakdown") != effects.end());
    pass &= (effects.find("paranoia") != effects.end());
    pass &= (effects.find("trust") != effects.end());
    pass &= (effects.find("allostatic") != effects.end());
    
    if (pass) {
        std::cout << "PASSED" << std::endl;
        return 0;
    } else {
        std::cout << "FAILED" << std::endl;
        std::cout << "  arousal: " << effects["arousal"] << " (expected " << EFFECTS_arousal << ")" << std::endl;
        std::cout << "  plasticity: " << effects["plasticity"] << " (expected " << EFFECTS_plasticity << ")" << std::endl;
        std::cout << "  aggression: " << effects["aggression"] << " (expected " << EFFECTS_aggression << ")" << std::endl;
        std::cout << "  sociality: " << effects["sociality"] << " (expected " << EFFECTS_sociality << ")" << std::endl;
        return 1;
    }
}

int test_bounds() {
    std::cout << "Test: Hormones stay in bounds... ";
    
    alife::Genome genome = create_test_genome();
    alife::Hormones hormones(genome);
    
    bool pass = true;
    
    // Много обновлений с разными событиями
    for (int i = 0; i < 100; i++) {
        for (const auto& ev : test_events) {
            std::map<std::string, double> events = {
                {"reward", ev.reward},
                {"punishment", ev.punishment},
                {"social", ev.social},
                {"kin", ev.kin},
                {"conflict", ev.conflict},
                {"dominance", ev.dominance},
                {"hunger", ev.hunger},
                {"injury", ev.injury},
                {"fear", ev.fear},
            };
            hormones.update(ev.dt, events, genome);
            
            // Проверка границ [0, 2] для основных гормонов
            if (hormones.D < 0.0 || hormones.D > 2.0) pass = false;
            if (hormones.S < 0.0 || hormones.S > 2.0) pass = false;
            if (hormones.O < 0.0 || hormones.O > 2.0) pass = false;
            if (hormones.C < 0.0 || hormones.C > 2.0) pass = false;
            if (hormones.T < 0.0 || hormones.T > 2.0) pass = false;
            
            // Проверка границ [0, 1] для состояний
            if (hormones.allostatic < 0.0) pass = false;
            if (hormones.depression < 0.0 || hormones.depression > 1.0) pass = false;
            if (hormones.breakdown < 0.0 || hormones.breakdown > 1.0) pass = false;
            if (hormones.paranoia < 0.0 || hormones.paranoia > 1.0) pass = false;
            if (hormones.trust < 0.0 || hormones.trust > 1.0) pass = false;
        }
    }
    
    if (pass) {
        std::cout << "PASSED" << std::endl;
        return 0;
    } else {
        std::cout << "FAILED" << std::endl;
        return 1;
    }
}

int test_no_nan() {
    std::cout << "Test: No NaN after 1000 updates... ";
    
    alife::Genome genome = create_test_genome();
    alife::Hormones hormones(genome);
    
    bool has_nan = false;
    for (int i = 0; i < 1000; i++) {
        const auto& ev = test_events[i % test_events.size()];
        std::map<std::string, double> events = {
            {"reward", ev.reward},
            {"punishment", ev.punishment},
            {"social", ev.social},
            {"kin", ev.kin},
            {"conflict", ev.conflict},
            {"dominance", ev.dominance},
            {"hunger", ev.hunger},
            {"injury", ev.injury},
            {"fear", ev.fear},
        };
        hormones.update(ev.dt, events, genome);
        
        if (is_nan(hormones.D) || is_nan(hormones.S) || is_nan(hormones.O) ||
            is_nan(hormones.C) || is_nan(hormones.T) || is_nan(hormones.allostatic) ||
            is_nan(hormones.depression) || is_nan(hormones.breakdown) ||
            is_nan(hormones.paranoia) || is_nan(hormones.trust)) {
            has_nan = true;
            break;
        }
    }
    
    if (!has_nan) {
        std::cout << "PASSED" << std::endl;
        return 0;
    } else {
        std::cout << "FAILED (NaN detected)" << std::endl;
        return 1;
    }
}

int test_depression_breakdown_rules() {
    std::cout << "Test: Depression and breakdown rules... ";
    
    // Тест 1: депрессия не должна расти при нормальных гормонах
    {
        std::map<std::string, double> genes = {
            {"mutation_rate", 0.05},
            {"conn_prob", 0.1},
            {"weight_scale", 0.5},
            {"weight_max", 1.5},
            {"membrane_decay", 0.9},
            {"threshold", 1.0},
            {"stdp_rate", 0.01},
            {"plasticity_gain", 1.0},
            {"dopamine_base", 0.5},
            {"dopamine_reactivity", 1.0},
            {"dopamine_decay", 0.05},
            {"dopamine_sensitivity", 1.0},
            {"serotonin_base", 0.5},
            {"serotonin_decay", 0.05},
            {"serotonin_sensitivity", 1.0},
            {"oxytocin_base", 0.4},
            {"oxytocin_gain", 1.0},
            {"oxytocin_decay", 0.05},
            {"oxytocin_sensitivity", 1.0},
            {"cortisol_base", 0.2},
            {"cortisol_reactivity", 1.0},
            {"cortisol_decay", 0.05},
            {"cortisol_sensitivity", 1.0},
            {"testosterone_base", 0.5},
            {"testosterone_reactivity", 1.0},
            {"testosterone_decay", 0.05},
            {"testosterone_sensitivity", 1.0},
            {"aggression_gain", 1.0},
            {"social_gain", 1.0},
            {"lamarckian_weight", 0.5},
            {"metabolism", 0.05},
            {"brain_arch_mutability", 0.05},
            {"stress_resilience", 0.5},
            {"social_temperament", 0.5},
        };
        alife::Genome genome(&genes);
        alife::Hormones hormones(genome);
        
        // Много шагов без стресса
        for (int i = 0; i < 100; i++) {
            std::map<std::string, double> events = {
                {"reward", 0.5},
                {"punishment", 0.0},
                {"social", 0.5},
                {"kin", 0.3},
                {"conflict", 0.0},
                {"dominance", 0.0},
                {"hunger", 0.1},
                {"injury", 0.0},
                {"fear", 0.0},
            };
            hormones.update(1.0, events, genome);
        }
        
        // Депрессия должна быть низкой
        if (hormones.depression > 0.1) {
            std::cout << "FAILED (depression too high: " << hormones.depression << ")" << std::endl;
            return 1;
        }
    }
    
    // Тест 2: is_broken() и is_depressed() работают корректно
    {
        std::map<std::string, double> genes = {
            {"mutation_rate", 0.05},
            {"conn_prob", 0.1},
            {"weight_scale", 0.5},
            {"weight_max", 1.5},
            {"membrane_decay", 0.9},
            {"threshold", 1.0},
            {"stdp_rate", 0.01},
            {"plasticity_gain", 1.0},
            {"dopamine_base", 0.5},
            {"dopamine_reactivity", 1.0},
            {"dopamine_decay", 0.05},
            {"dopamine_sensitivity", 1.0},
            {"serotonin_base", 0.5},
            {"serotonin_decay", 0.05},
            {"serotonin_sensitivity", 1.0},
            {"oxytocin_base", 0.4},
            {"oxytocin_gain", 1.0},
            {"oxytocin_decay", 0.05},
            {"oxytocin_sensitivity", 1.0},
            {"cortisol_base", 0.2},
            {"cortisol_reactivity", 1.0},
            {"cortisol_decay", 0.05},
            {"cortisol_sensitivity", 1.0},
            {"testosterone_base", 0.5},
            {"testosterone_reactivity", 1.0},
            {"testosterone_decay", 0.05},
            {"testosterone_sensitivity", 1.0},
            {"aggression_gain", 1.0},
            {"social_gain", 1.0},
            {"lamarckian_weight", 0.5},
            {"metabolism", 0.05},
            {"brain_arch_mutability", 0.05},
            {"stress_resilience", 0.5},
            {"social_temperament", 0.5},
        };
        alife::Genome genome(&genes);
        alife::Hormones hormones(genome);
        
        // Начальное состояние - не сломан и не депрессивен
        if (hormones.is_broken() || hormones.is_depressed()) {
            std::cout << "FAILED (initial state should not be broken/depressed)" << std::endl;
            return 1;
        }
    }
    
    std::cout << "PASSED" << std::endl;
    return 0;
}

int test_mood() {
    std::cout << "Test: get_mood()... ";
    
    alife::Genome genome = create_test_genome();
    alife::Hormones hormones(genome);
    
    // Начальное настроение должно быть "нормальное"
    std::string mood = hormones.get_mood();
    if (mood != "нормальное") {
        std::cout << "FAILED (expected 'нормальное', got '" << mood << "')" << std::endl;
        return 1;
    }
    
    std::cout << "PASSED" << std::endl;
    return 0;
}

int main() {
    std::cout << "=== Hormones Tests ===" << std::endl;
    std::cout << std::endl;
    
    int failures = 0;
    failures += test_initial_state();
    failures += test_update_sequence();
    failures += test_effects();
    failures += test_bounds();
    failures += test_no_nan();
    failures += test_depression_breakdown_rules();
    failures += test_mood();
    
    std::cout << std::endl;
    if (failures == 0) {
        std::cout << "All tests PASSED!" << std::endl;
        return 0;
    } else {
        std::cout << failures << " test(s) FAILED!" << std::endl;
        return 1;
    }
}
