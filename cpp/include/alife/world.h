/**
 * @file world.h
 * @brief Класс мира симуляции ALife.
 * 
 * Перенесено из Python реализации без изменения логики.
 * Реализует полный цикл симуляции:
 * - спавн еды;
 * - спавн агентов;
 * - поиск ближайших объектов;
 * - обновление агентов;
 * - удаление съеденной еды;
 * - добавление новорождённых;
 * - удаление мёртвых агентов;
 * - защита от вымирания.
 */

#ifndef ALIFE_WORLD_H
#define ALIFE_WORLD_H

#include <vector>
#include <map>
#include <string>
#include <optional>
#include "alife/agent.h"
#include "alife/genome.h"
#include "alife/rng.h"

namespace alife {

// Константы популяции из config.py
constexpr int AGENT_COUNT = 24;
constexpr int MIN_AGENTS = 6;
constexpr int FOOD_MAX = 90;
constexpr double FOOD_RESPAWN = 0.22;

/**
 * @struct Food
 * @brief Структура еды.
 */
struct Food {
    double pos_x;        ///< Позиция X
    double pos_y;        ///< Позиция Y
    double nutrition;    ///< Питательность
    bool eaten;          ///< Съедена ли
};

/**
 * @struct GenerationStats
 * @brief Статистика поколений.
 */
struct GenerationStats {
    int max_generation;                              ///< Максимальное поколение
    std::map<int, int> generation_counts;            ///< Распределение по поколениям
    std::map<std::string, std::map<std::string, double>> lineage_stats;  ///< Статистика линий
};

/**
 * @class World
 * @brief Класс мира симуляции.
 * 
 * Содержит:
 * - всех агентов;
 * - всю еду;
 * - новорождённых (ожидают добавления);
 * - статистику поколений.
 */
class World {
public:
    /**
     * @brief Конструктор мира.
     * @param seed Seed для RNG (по умолчанию 42).
     * @param initial_agents Количество начальных агентов (по умолчанию AGENT_COUNT).
     * @param initial_food Количество начальной еды (по умолчанию FOOD_MAX).
     */
    World(
        uint64_t seed = 42,
        int initial_agents = AGENT_COUNT,
        int initial_food = FOOD_MAX
    );

    /**
     * @brief Сделать один тик симуляции.
     * 
     * Порядок выполнения (как в Python):
     * 1. Поиск ближайших объектов для каждого агента.
     * 2. Обновление агентов (сенсоры, мозг, движение, события).
     * 3. Удаление съеденной еды.
     * 4. Добавление новорождённых.
     * 5. Удаление мёртвых агентов.
     * 6. Спавн новых агентов при низкой популяции.
     * 7. Спавн новой еды.
     */
    void update();

    /**
     * @brief Спавнить еду в случайном месте.
     */
    void spawn_food();

    /**
     * @brief Спавнить случайного агента.
     */
    void spawn_random_agent();

    /**
     * @brief Найти ближайшую еду к позиции.
     * @param pos_x Позиция X.
     * @param pos_y Позиция Y.
     * @return NearestFood или nullopt если еды нет.
     */
    std::optional<NearestFood> find_nearest_food(double pos_x, double pos_y) const;

    /**
     * @brief Найти ближайшего агента к агенту.
     * @param agent_id ID агента.
     * @return NearestAgent или nullopt если агентов нет.
     */
    std::optional<NearestAgent> find_nearest_agent(int agent_id) const;

    /**
     * @brief Пометить еду как съеденную.
     * @param pos_x Позиция X еды.
     * @param pos_y Позиция Y еды.
     */
    void mark_food_eaten(double pos_x, double pos_y);

    /**
     * @brief Нанести урон агенту.
     * @param agent_id ID агента.
     * @param damage Количество урона.
     */
    void damage_agent(int agent_id, double damage);

    /**
     * @brief Проверить может ли агент размножаться.
     * @param agent_id ID агента.
     * @return true если агент может размножаться.
     */
    bool can_agent_reproduce(int agent_id) const;

    /**
     * @brief Запросить размножение.
     * @param parent1_id ID первого родителя.
     * @param parent2_id ID второго родителя.
     * @param sociality Социальность первого родителя.
     */
    void request_reproduction(int parent1_id, int parent2_id, double sociality);

    /**
     * @brief Получить текущий тик симуляции.
     * @return Номер тика.
     */
    int get_tick() const { return tick_; }

    /**
     * @brief Получить количество агентов.
     * @return Количество живых агентов.
     */
    size_t get_agent_count() const { return agents_.size(); }

    /**
     * @brief Получить количество еды.
     * @return Количество несъеденной еды.
     */
    size_t get_food_count() const;

    /**
     * @brief Получить агентов.
     * @return Вектор агентов.
     */
    const std::vector<Agent>& get_agents() const { return agents_; }

    /**
     * @brief Получить еду.
     * @return Вектор еды.
     */
    const std::vector<Food>& get_foods() const { return foods_; }

    /**
     * @brief Экспорт состояния в JSON.
     * @param path Путь к файлу (опционально).
     * @return JSON строка.
     */
    std::string to_json(const std::optional<std::string>& path = std::nullopt) const;

    /**
     * @brief Обновить статистику поколений.
     */
    void update_generation_stats();

private:
    std::vector<Agent> agents_;           ///< Все агенты
    std::vector<Food> foods_;             ///< Вся еда
    std::vector<Agent> newborns_;         ///< Новорождённые (ожидают добавления)
    int tick_;                            ///< Текущий тик
    uint64_t seed_;                       ///< Seed RNG
    RNG rng_;                             ///< Генератор случайных чисел
    GenerationStats gen_stats_;           ///< Статистика поколений
    
    // Для размножения: накапливаем запросы во время update
    std::vector<std::tuple<int, int, double>> reproduction_requests_;
};

} // namespace alife

#endif // ALIFE_WORLD_H
