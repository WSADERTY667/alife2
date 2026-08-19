/**
 * @file brain.h
 * @brief Спайковая нейронная сеть (SNN) агента.
 * 
 * Перенесено из Python реализации без изменения логики.
 * Использует детерминированный RNG из rng.h.
 * Реализует dense MVP-версию мозга.
 */

#ifndef ALIFE_BRAIN_H
#define ALIFE_BRAIN_H

#include <vector>
#include <map>
#include <cstdint>
#include <optional>
#include "alife/rng.h"
#include "alife/genome.h"

namespace alife {

// Размеры по умолчанию из config.py (используем уже определённые в genome.h)
constexpr int DEFAULT_INPUT_SIZE = 12;
constexpr int DEFAULT_OUTPUT_SIZE = 6;
constexpr double DEFAULT_SYNAPTIC_SCALE = 0.085;

/**
 * @class Brain
 * @brief Класс спайковой нейронной сети агента.
 * 
 * Реализует:
 * - обновление мембранного потенциала;
 * - спайки;
 * - входные сенсорные нейроны;
 * - выходные rates;
 * - eligibility trace;
 * - reward-modulated STDP;
 * - наследование родительских весов.
 */
class Brain {
public:
    /**
     * @brief Конструктор мозга.
     * @param genome Геном с параметрами нейросети.
     * @param n_hidden Количество скрытых нейронов (опционально, берётся из генома).
     * @param parent_weights Веса родителя для наследования (опционально).
     * @param rng Генератор случайных чисел для детерминированности.
     */
    Brain(
        const Genome& genome,
        std::optional<int> n_hidden = std::nullopt,
        const std::optional<std::vector<double>>& parent_weights = std::nullopt,
        RNG* rng = nullptr
    );

    /**
     * @brief Сделать шаг симуляции.
     * @param sensors Входные сенсорные данные (INPUT_SIZE значений).
     * @param mod Модуляторы (dopamine, plasticity, arousal).
     * @return Выходные rates (OUTPUT_SIZE значений).
     */
    std::vector<double> step(
        const std::vector<double>& sensors,
        const std::map<std::string, double>& mod
    );

    // Публичные поля для доступа в тестах
    std::vector<double> v;              ///< Мембранные потенциалы
    std::vector<double> spikes;         ///< Спайки
    std::vector<double> out_rate;       ///< Выходные rates
    std::vector<double> W;              ///< Веса (плоский массив N x N)
    std::vector<bool> mask;             ///< Маска связей (плоский массив N x N)
    std::vector<double> E;              ///< Eligibility trace (плоский массив N x N)

    // Параметры
    int n_in;                           ///< Количество входных нейронов
    int n_out;                          ///< Количество выходных нейронов
    int n_hidden;                       ///< Количество скрытых нейронов
    int n;                              ///< Общее количество нейронов
    double decay_base;                  ///< Базовое затухание мембраны
    double threshold_base;              ///< Базовый порог активации
    double stdp_rate;                   ///< Скорость STDP обучения
    double max_w;                       ///< Максимальный вес
    bool learning;                      ///< Флаг обучения

private:
    RNG* rng_;                          ///< Указатель на RNG
    RNG default_rng_;                   ///< RNG по умолчанию
    
    /// Получить индекс в плоском массиве
    inline size_t idx(int row, int col) const {
        return static_cast<size_t>(row) * static_cast<size_t>(n) + static_cast<size_t>(col);
    }
};

} // namespace alife

#endif // ALIFE_BRAIN_H
