/**
 * @file hormones.cpp
 * @brief Реализация гормональной системы агента.
 * 
 * Перенесено из Python реализации без изменения логики.
 * Использует double на этапе parity.
 */

#include "alife/hormones.h"
#include "alife/math_utils.h"
#include <cmath>

namespace alife {

Hormones::Hormones(const Genome& genome)
    : D(genome["dopamine_base"])
    , S(genome["serotonin_base"])
    , O(genome["oxytocin_base"])
    , C(genome["cortisol_base"])
    , T(genome["testosterone_base"])
    , allostatic(0.0)
    , depression(0.0)
    , breakdown(0.0)
    , paranoia(0.0)
    , trust(0.5)
    , delayed_punishment(0.0)
    , D_decay(genome.get("dopamine_decay", 0.05))
    , S_decay(genome.get("serotonin_decay", 0.05))
    , O_decay(genome.get("oxytocin_decay", 0.05))
    , C_decay(genome.get("cortisol_decay", 0.05))
    , T_decay(genome.get("testosterone_decay", 0.05))
    , S_sensitivity(genome.get("serotonin_sensitivity", 1.0))
    , O_sensitivity(genome.get("oxytocin_sensitivity", 1.0))
    , C_sensitivity(genome.get("cortisol_sensitivity", 1.0))
    , T_sensitivity(genome.get("testosterone_sensitivity", 1.0))
    , D_sensitivity(genome.get("dopamine_sensitivity", 1.0))
    , stress_resilience(genome.get("stress_resilience", 0.5))
    , social_temperament(genome.get("social_temperament", 0.5))
{
}

void Hormones::update(double dt, const std::map<std::string, double>& events, const Genome& genome) {
    auto get_event = [&events](const std::string& name) -> double {
        auto it = events.find(name);
        return (it != events.end()) ? it->second : 0.0;
    };

    double reward = get_event("reward");
    double punishment = get_event("punishment");
    double social = get_event("social");
    double kin = get_event("kin");
    double conflict = get_event("conflict");
    double dominance = get_event("dominance");
    double hunger = get_event("hunger");
    double injury = get_event("injury");
    double fear = get_event("fear");

    // Сохраняем историю наказания для отложенной реакции
    if (punishment > 0.1) {
        punishment_history.push_back({punishment, dt});
    }
    
    // Обрабатываем отложенное наказание - эффект проявляется постепенно
    double delayed_effect = 0.0;
    if (!punishment_history.empty()) {
        for (auto& item : punishment_history) {
            item.second += dt;
        }
        // Старые события затухают, но влияют на текущее состояние
        std::vector<std::pair<double, double>> active_punishments;
        for (const auto& item : punishment_history) {
            if (item.second < 50.0) {
                active_punishments.push_back(item);
            }
        }
        if (!active_punishments.empty()) {
            double sum = 0.0;
            for (const auto& item : active_punishments) {
                sum += item.first * std::max(0.1, 1.0 - item.second / 50.0);
            }
            delayed_effect = sum / static_cast<double>(active_punishments.size());
        }
        punishment_history = active_punishments;
    }
    delayed_punishment = clamp(delayed_effect, 0.0, 1.0);

    // Дофамин с учетом наследуемого распада и чувствительности
    double D_sens = D_sensitivity;
    D += (
        genome["dopamine_reactivity"] * (reward - punishment) * 0.25 * D_sens
        + D_decay * (genome["dopamine_base"] - D)
    );
    D = clamp(D, 0.0, 2.0);

    // Кортизол с учетом наследуемой чувствительности и распада
    double C_sens = C_sensitivity;
    // Стресс зависит от индивидуальной устойчивости
    double resilience_factor = 1.0 - stress_resilience * 0.4;
    double stress = (punishment * 1.0 + conflict * 0.6 + hunger * 0.35 + injury * 0.9 + fear * 0.8) * resilience_factor;
    C += (
        genome["cortisol_reactivity"] * stress * 0.12 * C_sens
        - C_decay * (C - genome["cortisol_base"])
    );
    C = clamp(C, 0.0, 2.0);

    // Серотонин с учетом наследуемой чувствительности и распада
    double S_sens = S_sensitivity;
    S += (
        S_decay * (genome["serotonin_base"] - S) * S_sens
        + reward * 0.03
        - std::max(0.0, C - 0.8) * 0.05
        - delayed_punishment * 0.02
    );
    S = clamp(S, 0.0, 2.0);

    // Окситоцин с учетом наследуемой чувствительности и распада
    double O_sens = O_sensitivity;
    double social_temper = social_temperament;
    O += (
        genome["oxytocin_gain"] * (social * 0.06 + kin * 0.08) * O_sens * (0.7 + social_temper * 0.6)
        - O_decay * (O - genome["oxytocin_base"])
    );
    O = clamp(O, 0.0, 2.0);

    // Тестостерон с учетом наследуемой чувствительности и распада
    double T_sens = T_sensitivity;
    T += (
        genome["testosterone_reactivity"] * (conflict * 0.08 + dominance * 0.05) * T_sens
        - T_decay * (T - genome["testosterone_base"])
    );
    T = clamp(T, 0.0, 2.0);

    // Аллостатическая нагрузка - накопленный ущерб от хронического стресса
    if (C > 0.85) {
        double allostatic_increase = (C - 0.85) * 0.03 * (1.0 - stress_resilience * 0.3);
        allostatic += allostatic_increase;
    } else {
        allostatic = std::max(0.0, allostatic - 0.004);
    }
    
    // Слом происходит при критической аллостатической нагрузке
    if (allostatic > 1.8) {
        breakdown = std::min(1.0, breakdown + 0.01);
    } else {
        breakdown = std::max(0.0, breakdown - 0.006);
    }

    // Депрессия - развивается при низком серотонине и дофамине
    double low_S_threshold = 0.30 * (2.0 - S_sensitivity);
    double low_D_threshold = 0.35 * (2.0 - D_sensitivity);
    if (S < low_S_threshold && D < low_D_threshold) {
        double depression_rate = 0.004 * (1.0 + delayed_punishment);
        depression = std::min(1.0, depression + depression_rate);
    } else {
        double recovery_rate = 0.002 * (1.0 + O * 0.3);
        depression = std::max(0.0, depression - recovery_rate);
    }

    // Паранойя - растёт от наказания, стресса и одиночества
    double paranoia_triggers = punishment * 0.4 + C * 0.2 + fear * 0.3;
    if (paranoia_triggers > 0.3) {
        paranoia = std::min(1.0, paranoia + 0.003 * paranoia_triggers);
    } else {
        // Снижается от окситоцина и социальных контактов
        double paranoia_reduction = (O * 0.3 + social * 0.2) * (1.0 - paranoia);
        paranoia = std::max(0.0, paranoia - paranoia_reduction * 0.005);
    }

    // Доверие - зависит от окситоцина, серотонина и позитивного социального опыта
    double trust_boost = (O * 0.4 + S * 0.2 + reward * 0.1) * (1.0 - trust);
    double trust_decline = (punishment * 0.3 + paranoia * 0.4) * trust;
    trust = clamp(trust + (trust_boost - trust_decline) * 0.01, 0.0, 1.0);
}

std::map<std::string, double> Hormones::effects(const Genome& genome, double hunger) const {
    double dopamine_error = D - genome["dopamine_base"];
    
    // Учет чувствительности к гормонам в эффектах
    double C_eff = C * C_sensitivity;
    double T_eff = T * T_sensitivity;
    double S_eff = S * S_sensitivity;
    double O_eff = O * O_sensitivity;
    double D_eff = D * D_sensitivity;
    
    double arousal = clamp(
        0.15 + C_eff * 0.55 + T_eff * 0.25 - S_eff * 0.15 + hunger * 0.20,
        -0.5, 1.5
    );
    
    double plasticity = genome["plasticity_gain"] * (
        0.15 + std::max(0.0, dopamine_error) * 1.8
    ) * (1.0 - std::min(0.75, C_eff * 0.35));
    
    if (depression > 0.5) {
        plasticity *= 0.45;
    }
    if (breakdown > 0.5) {
        plasticity *= 0.20;
    }
    
    // Агрессия зависит от тестостерона, кортизола, паранойи и низкого доверия
    double paranoia_factor = 1.0 + paranoia * 0.5;
    double distrust_factor = 1.0 + (1.0 - trust) * 0.3;
    double aggression = genome["aggression_gain"] * (
        T_eff * 0.55 + C_eff * 0.35 - S_eff * 0.25 + hunger * 0.20
    ) * paranoia_factor * distrust_factor;
    
    // Социальность зависит от окситоцина, доверия и снижена паранойей
    double trust_factor = trust * 0.7 + 0.3;
    double paranoia_social_penalty = 1.0 - paranoia * 0.6;
    double sociality = genome["social_gain"] * (
        O_eff * 0.85 + S_eff * 0.10 - C_eff * 0.20
    ) * trust_factor * paranoia_social_penalty;
    
    double dopamine_signal = clamp(dopamine_error * 1.5, -1.0, 1.0);
    
    std::map<std::string, double> result;
    result["arousal"] = clamp(arousal, -1.0, 2.0);
    result["plasticity"] = clamp(plasticity, 0.0, 3.0);
    result["aggression"] = clamp(aggression, 0.0, 3.0);
    result["sociality"] = clamp(sociality, 0.0, 3.0);
    result["dopamine_signal"] = dopamine_signal;
    result["depression"] = depression;
    result["breakdown"] = breakdown;
    result["paranoia"] = paranoia;
    result["trust"] = trust;
    result["allostatic"] = allostatic;
    
    return result;
}

std::string Hormones::get_mood() const {
    // Сначала проверяем критические состояния
    if (breakdown > 0.5) {
        return "ярость";
    }
    
    if (depression > 0.5) {
        return "грусть";
    }
    
    // Паранойя влияет на восприятие
    if (paranoia > 0.7) {
        return "подозрительность";
    }
    
    // Очень низкие все гормоны или диссоциация = отрешённость (проверяем до скуки)
    if (D < 0.3 && S < 0.3 && O < 0.3) {
        return "отрешённость";
    }
    
    // Высокий кортизол + отстранённость = отрешённость
    if (C > 0.8 && S < 0.4) {
        return "отрешённость";
    }
    
    // Высокий дофамин + высокий серотонин = радость
    if (D > 0.7 && S > 0.6) {
        return "радость";
    }
    
    // Низкий дофамин + низкий кортизол + низкий тестостерон = скука
    if (D < 0.4 && C < 0.4 && T < 0.4) {
        return "скука";
    }
    
    // Высокий кортизол + высокий тестостерон + низкий серотонин = ярость
    if (C > 0.7 && T > 0.6 && S < 0.5) {
        return "ярость";
    }
    
    // Высокое доверие + окситоцин = спокойствие
    if (trust > 0.6 && O > 0.5) {
        return "спокойствие";
    }
    
    return "нормальное";
}

bool Hormones::is_broken() const {
    return breakdown > 0.5;
}

bool Hormones::is_depressed() const {
    return depression > 0.5;
}

bool Hormones::is_paranoid() const {
    return paranoia > 0.5;
}

bool Hormones::is_trusting() const {
    return trust >= 0.5;
}

} // namespace alife
