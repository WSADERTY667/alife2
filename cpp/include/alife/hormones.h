/**
 * @file hormones.h
 * @brief Гормональная система агента с расширенной моделью эмоций.
 * 
 * Перенесено из Python реализации без изменения логики.
 * Использует double на этапе parity.
 */

#ifndef ALIFE_HORMONES_H
#define ALIFE_HORMONES_H

#include <map>
#include <vector>
#include <string>
#include "alife/genome.h"

namespace alife {

/**
 * @class Hormones
 * @brief Класс гормональной системы агента.
 * 
 * Содержит состояния гормонов и методы для их обновления.
 */
class Hormones {
public:
    // Базовые уровни гормонов
    double D;  ///< Дофамин
    double S;  ///< Серотонин
    double O;  ///< Окситоцин
    double C;  ///< Кортизол
    double T;  ///< Тестостерон
    
    // Аллостатическая нагрузка - накопленный ущерб от хронического стресса
    double allostatic;
    // Депрессия - состояние низкого настроения и мотивации
    double depression;
    // Слом - критическое состояние после чрезмерного стресса
    double breakdown;
    // Паранойя - недоверие к окружению, растёт от наказания и стресса
    double paranoia;
    // Доверие - склонность к социальному взаимодействию
    double trust;
    // Отложенное наказание - след от прошлых негативных событий
    double delayed_punishment;
    
    // Полу-распады гормонов - наследуемые параметры распада
    double D_decay;
    double S_decay;
    double O_decay;
    double C_decay;
    double T_decay;
    
    // Чувствительность к гормонам - наследуемые множители эффекта
    double S_sensitivity;
    double O_sensitivity;
    double C_sensitivity;
    double T_sensitivity;
    double D_sensitivity;
    
    // Индивидуальный профиль реактивности
    double stress_resilience;
    double social_temperament;
    
    // История наказаний для отложенной реакции
    std::vector<std::pair<double, double>> punishment_history;

    /**
     * @brief Конструктор гормональной системы.
     * @param genome Геном агента.
     */
    explicit Hormones(const Genome& genome);

    /**
     * @brief Обновить состояние гормонов.
     * @param dt Время шага симуляции.
     * @param events События (reward, punishment, social, kin, conflict, dominance, hunger, injury, fear).
     * @param genome Геном агента.
     */
    void update(double dt, const std::map<std::string, double>& events, const Genome& genome);

    /**
     * @brief Вычислить эффекты гормонов.
     * @param genome Геном агента.
     * @param hunger Уровень голода (опционально).
     * @return Карта эффектов (arousal, plasticity, aggression, sociality, dopamine_signal, depression, breakdown, paranoia, trust, allostatic).
     */
    std::map<std::string, double> effects(const Genome& genome, double hunger = 0.0) const;

    /**
     * @brief Получить текущее настроение.
     * @return Строка с названием настроения.
     */
    std::string get_mood() const;

    /**
     * @brief Проверить, сломано ли существо от хронического стресса.
     * @return true если breakdown > 0.5.
     */
    bool is_broken() const;

    /**
     * @brief Проверить, находится ли существо в депрессии.
     * @return true если depression > 0.5.
     */
    bool is_depressed() const;

    /**
     * @brief Проверить, параноидально ли настроено существо.
     * @return true если paranoia > 0.5.
     */
    bool is_paranoid() const;

    /**
     * @brief Проверить, доверяет ли существо окружению.
     * @return true если trust >= 0.5.
     */
    bool is_trusting() const;
};

} // namespace alife

#endif // ALIFE_HORMONES_H
