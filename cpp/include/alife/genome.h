/**
 * @file genome.h
 * @brief Геном агента и генетические операции.
 * 
 * Перенесено из Python реализации без изменения логики.
 * Использует детерминированный RNG из rng.h.
 */

#ifndef ALIFE_GENOME_H
#define ALIFE_GENOME_H

#include <string>
#include <vector>
#include <map>
#include <cstdint>
#include "alife/rng.h"

namespace alife {

// Количество скрытых нейронов по умолчанию
constexpr int DEFAULT_N_HIDDEN = 160;

// Цвета тегов (племен) - 8 цветов
constexpr int TAG_COLOR_COUNT = 8;

// Список ключей генома
extern const std::vector<std::string> GENOME_KEYS;

// Границы значений для каждого гена
extern const std::map<std::string, std::pair<double, double>> BOUNDS;

// Масштаб мутации для каждого гена (вычисляется как 8% от диапазона)
extern const std::map<std::string, double> MUT_SCALE;

// Ключи для вычисления схожести геномов
extern const std::vector<std::string> KIN_KEYS;

/**
 * @class Genome
 * @brief Класс генома агента, содержащий гены и методы для генетических операций.
 */
class Genome {
public:
    /**
     * @brief Конструктор генома.
     * @param genes Карта генов (если nullptr, генерируются случайные значения).
     * @param tag Тег племени (если -1, выбирается случайно).
     * @param tribal_tags Племенные теги (наследуемые маркеры линии).
     * @param n_hidden Количество скрытых нейронов (если -1, используется значение по умолчанию).
     * @param rng Генератор случайных чисел для детерминированности.
     */
    Genome(
        const std::map<std::string, double>* genes = nullptr,
        int tag = -1,
        const std::vector<std::string>& tribal_tags = {},
        int n_hidden = -1,
        RNG* rng = nullptr
    );

    /**
     * @brief Получить значение гена по ключу.
     * @param key Ключ гена.
     * @return Значение гена.
     * @throws std::out_of_range Если ключ не найден.
     */
    double operator[](const std::string& key) const;

    /**
     * @brief Получить значение гена по ключу (не-const версия).
     * @param key Ключ гена.
     * @return Ссылка на значение гена.
     * @throws std::out_of_range Если ключ не найден.
     */
    double& operator[](const std::string& key);

    /**
     * @brief Получить значение гена с дефолтным значением.
     * @param key Ключ гена.
     * @param default_value Значение по умолчанию.
     * @return Значение гена или default_value если ключ не найден.
     */
    double get(const std::string& key, double default_value = 0.0) const;

    /**
     * @brief Мутировать геном.
     * @param rng Генератор случайных чисел (опционально, используется внутренний если не указан).
     */
    void mutate(RNG* rng = nullptr);

    /**
     * @brief Выполнить кроссовер двух геномов.
     * @param a Первый родитель.
     * @param b Второй родитель.
     * @param rng Генератор случайных чисел (опционально).
     * @return Новый геном-потомок.
     */
    static Genome crossover(const Genome& a, const Genome& b, RNG* rng = nullptr);

    // Публичные поля для совместимости с Python
    std::map<std::string, double> genes;      ///< Гены
    int tag;                                   ///< Тег племени
    std::vector<std::string> tribal_tags;     ///< Племенные теги
    int n_hidden;                             ///< Количество скрытых нейронов

private:
    RNG* rng_;         ///< Указатель на RNG (может быть nullptr)
    RNG default_rng_;  ///< RNG по умолчанию для внутреннего использования
};

/**
 * @brief Вычислить схожесть двух геномов.
 * @param g1 Первый геном.
 * @param g2 Второй геном.
 * @return Значение схожести от 0.0 до 1.0.
 * 
 * Формула:
 * - 50% - схожесть генов (по KIN_KEYS)
 * - 15% - схожесть визуального тега
 * - 20% - перекрытие племенных тегов
 * - 15% - схожесть архитектуры мозга (n_hidden)
 */
double genome_similarity(const Genome& g1, const Genome& g2);

} // namespace alife

#endif // ALIFE_GENOME_H
