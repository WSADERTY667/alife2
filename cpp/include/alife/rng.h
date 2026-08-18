/**
 * @file rng.h
 * @brief Детерминированный RNG на основе алгоритма SplitMix64.
 * 
 * Обеспечивает воспроизводимую последовательность чисел при одинаковом seed.
 * Полностью совместим с Python реализацией в python/alife/rng.py
 */

#ifndef ALIFE_RNG_H
#define ALIFE_RNG_H

#include <cstdint>
#include <vector>
#include <string>
#include <cmath>
#include <stdexcept>

namespace alife {

/**
 * @class RNG
 * @brief Детерминированный генератор псевдослучайных чисел на основе SplitMix64.
 * 
 * SplitMix64 — простой и быстрый алгоритм, обеспечивающий хорошее качество
 * случайности и полную детерминированность при одинаковом начальном seed.
 */
class RNG {
public:
    /**
     * @brief Инициализировать RNG с заданным seed.
     * @param seed Начальное значение (целое число). Может быть отрицательным.
     */
    explicit RNG(int64_t seed = 0) : state_(static_cast<uint64_t>(seed) & MASK64) {}

    /**
     * @brief Вернуть следующее случайное целое число в диапазоне [0, 2^32).
     * @return Случайное 32-битное неотрицательное целое число.
     */
    uint32_t next_int() {
        return static_cast<uint32_t>(_next_state() & MASK32);
    }

    /**
     * @brief Вернуть следующее случайное число с плавающей точкой в диапазоне [0.0, 1.0).
     * @return Случайное float значение от 0.0 (включительно) до 1.0 (исключительно).
     */
    double next_float() {
        return static_cast<double>(next_int()) / static_cast<double>(MASK32 + 1);
    }

    /**
     * @brief Вернуть случайное число с плавающей точкой в диапазоне [a, b].
     * @param a Нижняя граница (включительно).
     * @param b Верхняя граница (включительно).
     * @return Случайное float значение от a до b включительно.
     */
    double uniform(double a, double b) {
        return a + next_float() * (b - a);
    }

    /**
     * @brief Вернуть случайное целое число в диапазоне [a, b] (оба конца включены).
     * @param a Нижняя граница (включительно).
     * @param b Верхняя граница (включительно).
     * @return Случайное целое число от a до b включительно.
     * @throws std::invalid_argument Если a > b.
     */
    int32_t randint(int32_t a, int32_t b) {
        if (a > b) {
            throw std::invalid_argument("Нижняя граница (" + std::to_string(a) + 
                                        ") не может быть больше верхней (" + std::to_string(b) + ")");
        }
        if (a == b) {
            return a;
        }
        int64_t range_size = static_cast<int64_t>(b) - static_cast<int64_t>(a) + 1;
        return a + static_cast<int32_t>(next_int() % static_cast<uint32_t>(range_size));
    }

    /**
     * @brief Вернуть случайный элемент из непустой последовательности.
     * @tparam T Тип элемента.
     * @param seq Непустая последовательность (вектор).
     * @return Случайный элемент из последовательности.
     * @throws std::out_of_range Если последовательность пуста.
     */
    template<typename T>
    const T& choice(const std::vector<T>& seq) {
        if (seq.empty()) {
            throw std::out_of_range("choice из пустой последовательности");
        }
        return seq[static_cast<size_t>(randint(0, static_cast<int32_t>(seq.size()) - 1))];
    }

    /**
     * @brief Вернуть случайный символ из непустой строки.
     * @param s Непустая строка.
     * @return Случайный символ из строки.
     * @throws std::out_of_range Если строка пуста.
     */
    char choice(const std::string& s) {
        if (s.empty()) {
            throw std::out_of_range("choice из пустой последовательности");
        }
        return s[static_cast<size_t>(randint(0, static_cast<int32_t>(s.size()) - 1))];
    }

    /**
     * @brief Вернуть случайное число с нормальным (Гауссовым) распределением.
     * 
     * Использует метод Бокса-Мюллера для преобразования двух равномерных
     * случайных величин в нормально распределённую.
     * 
     * @param mu Математическое ожидание (среднее значение). По умолчанию 0.0.
     * @param sigma Стандартное отклонение (должно быть > 0). По умолчанию 1.0.
     * @return Случайное число с нормальным распределением N(mu, sigma^2).
     * @throws std::invalid_argument Если sigma <= 0.
     */
    double gauss(double mu = 0.0, double sigma = 1.0) {
        if (sigma <= 0.0) {
            throw std::invalid_argument("sigma должно быть положительным");
        }

        // Метод Бокса-Мюллера
        double u1 = next_float();
        double u2 = next_float();

        // Избегаем log(0)
        while (u1 == 0.0) {
            u1 = next_float();
        }

        double z0 = std::sqrt(-2.0 * std::log(u1)) * std::cos(2.0 * M_PI * u2);
        return mu + sigma * z0;
    }

    /**
     * @brief Перемешать вектор на месте (алгоритм Фишера-Йетса).
     * @tparam T Тип элемента.
     * @param lst Вектор для перемешивания (изменяется на месте).
     */
    template<typename T>
    void shuffle(std::vector<T>& lst) {
        int32_t n = static_cast<int32_t>(lst.size());
        for (int32_t i = n - 1; i > 0; --i) {
            int32_t j = randint(0, i);
            std::swap(lst[static_cast<size_t>(i)], lst[static_cast<size_t>(j)]);
        }
    }

    /**
     * @brief Создать копию RNG с тем же состоянием.
     * @return Новый экземпляр RNG с идентичным внутренним состоянием.
     */
    RNG copy() const {
        RNG new_rng(0);
        new_rng.state_ = state_;
        return new_rng;
    }

    /**
     * @brief Установить внутреннее состояние вручную.
     * @param state Новое значение состояния (будет приведено к 64 битам).
     */
    void set_state(int64_t state) {
        state_ = static_cast<uint64_t>(state) & MASK64;
    }

    /**
     * @brief Получить текущее внутреннее состояние.
     * @return Текущее 64-битное состояние генератора.
     */
    uint64_t get_state() const {
        return state_;
    }

private:
    /**
     * @brief Обновить внутреннее состояние и вернуть следующее 64-битное значение.
     * Реализация SplitMix64.
     * @return Следующее 64-битное значение.
     */
    uint64_t _next_state() {
        state_ = (state_ + 0x9E3779B97F4A7C15ULL) & MASK64;
        uint64_t z = state_;
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL) & MASK64;
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EBULL) & MASK64;
        return z ^ (z >> 31);
    }

    static constexpr uint64_t MASK64 = ~UINT64_C(0);  // Все биты установлены в 1 (0xFFFFFFFFFFFFFFFF)
    static constexpr uint64_t MASK32 = UINT32_C(0xFFFFFFFF);  // 0xFFFFFFFF

    uint64_t state_;
};

} // namespace alife

#endif // ALIFE_RNG_H
