/**
 * @file agent.h
 * @brief Класс агента симуляции ALife.
 * 
 * Перенесено из Python реализации без изменения логики.
 * Реализует полный цикл поведения агента:
 * - сенсоры;
 * - движение;
 * - еду;
 * - атаку;
 * - размножение;
 * - смерть.
 */

#ifndef ALIFE_AGENT_H
#define ALIFE_AGENT_H

#include <vector>
#include <map>
#include <optional>
#include <memory>
#include "alife/genome.h"
#include "alife/brain.h"
#include "alife/hormones.h"
#include "alife/rng.h"

namespace alife {

// Константы из config.py
constexpr double MAX_ENERGY = 100.0;
constexpr double START_ENERGY = 70.0;
constexpr double REPRO_ENERGY = 78.0;
constexpr double REPRO_COST = 28.0;
constexpr double REPRO_BASE = 0.035;
constexpr int REPRODUCE_COOLDOWN = 900;
constexpr double MATURE_AGE = 500;
constexpr double MAX_AGE = 26000;

constexpr double SENSE_RANGE = 230.0;
constexpr double SOCIAL_RANGE = 85.0;
constexpr double EAT_RANGE = 18.0;
constexpr double ATTACK_RANGE = 24.0;

constexpr double TURN_RATE = 0.38;
constexpr double MAX_SPEED = 2.2;
constexpr double AGENT_RADIUS = 6.0;

constexpr double EAT_THRESHOLD = 0.35;
constexpr double ATTACK_THRESHOLD = 0.45;
constexpr double ATTACK_DAMAGE = 12.0;
constexpr double ATTACK_COST = 3.0;

constexpr bool REFLEX_ASSIST = true;
constexpr bool LAMARCKIAN = true;

// Размеры мира
constexpr double WORLD_W = 1000.0;
constexpr double WORLD_H = 640.0;

/**
 * @struct NearestFood
 * @brief Данные о ближайшей еде.
 */
struct NearestFood {
    double distance;      ///< Расстояние до еды
    double abs_angle;     ///< Абсолютный угол направления
    bool eaten;           ///< Съедена ли еда
    double nutrition;     ///< Питательность
    double pos_x;         ///< Позиция X
    double pos_y;         ///< Позиция Y
};

/**
 * @struct NearestAgent
 * @brief Данные о ближайшем агенте.
 */
struct NearestAgent {
    double distance;      ///< Расстояние до агента
    double abs_angle;     ///< Абсолютный угол направления
    bool alive;           ///< Жив ли агент
    double kin_sim;       ///< Схожесть геномов (kinship similarity)
    // Ссылка на агента не хранится, передаётся через World
};

/**
 * @class Agent
 * @brief Класс агента симуляции.
 * 
 * Содержит:
 * - позицию и угол;
 * - геном;
 * - мозг (SNN);
 * - гормональную систему;
 * - энергию и возраст;
 * - состояние размножения;
 * - сенсорные данные.
 */
class Agent {
public:
    /**
     * @brief Конструктор агента.
     * @param pos_x Позиция X.
     * @param pos_y Позиция Y.
     * @param genome Геном агента.
     * @param generation Поколение (по умолчанию 0).
     * @param parent_weights Веса мозга родителя для наследования (опционально).
     * @param rng Генератор случайных чисел (опционально).
     */
    Agent(
        double pos_x,
        double pos_y,
        const Genome& genome,
        int generation = 0,
        const std::optional<std::vector<double>>& parent_weights = std::nullopt,
        RNG* rng = nullptr
    );

    /**
     * @brief Проверить возможность размножения.
     * @return true если агент может размножаться.
     */
    bool can_reproduce() const;

    /**
     * @brief Создать сенсорные данные для мозга.
     * @return Вектор из 12 сенсорных значений.
     */
    std::vector<double> make_sensors() const;

    /**
     * @brief Обновить состояние агента.
     * @param world Мир симуляции (для доступа к другим агентам и еде).
     * @param dt Время шага (по умолчанию 1.0).
     * 
     * Порядок обновления:
     * 1. Увеличить возраст и уменьшить cooldown размножения.
     * 2. Потратить энергию на метаболизм.
     * 3. Получить сенсоры и вычислить гормоны.
     * 4. Сделать шаг мозга.
     * 5. Применить рефлексную помощь.
     * 6. Двигаться.
     * 7. Обработать события (социальные, еда, атака).
     * 8. Обновить гормоны.
     * 9. Проверить смерть.
     * 10. Проверить размножение.
     */
    void update(class World& world, double dt = 1.0);

    /**
     * @brief Отскочить от стен.
     * 
     * Если агент выходит за границы мира, отражает угол и возвращает в границы.
     */
    void bounce();

    /**
     * @brief Создать потомка с партнёром.
     * @param mate Агент-партнёр.
     * @param rng Генератор случайных чисел (опционально).
     * @return Новый агент-потомок.
     */
    Agent make_child(const Agent& mate, RNG* rng = nullptr) const;

    // Публичные поля для совместимости с Python
    int id;                          ///< Уникальный ID агента
    double pos_x;                    ///< Позиция X
    double pos_y;                    ///< Позиция Y
    double angle;                    ///< Угол направления
    Genome genome;                   ///< Геном
    Brain brain;                     ///< Мозг
    Hormones hormones;               ///< Гормональная система
    double energy;                   ///< Энергия
    double age;                      ///< Возраст
    int generation;                  ///< Поколение
    bool alive;                      ///< Жив ли агент
    double repro_cooldown;           ///< Cooldown до размножения
    double last_pain;                ///< Последняя боль
    double pending_reward;           ///< Ожидаемая награда
    double pending_punishment;       ///< Ожидаемое наказание
    
    // Сенсорные данные (устанавливаются World перед update)
    std::optional<NearestFood> nearest_food;      ///< Ближайшая еда
    std::optional<NearestAgent> nearest_agent;    ///< Ближайший агент

private:
    RNG* rng_;              ///< Указатель на RNG
    RNG default_rng_;       ///< RNG по умолчанию
    static int next_id_;    ///< Счётчик ID для новых агентов
};

} // namespace alife

#endif // ALIFE_AGENT_H
