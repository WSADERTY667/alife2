/**
 * @file math_utils.h
 * @brief Математические утилиты: clamp и normalize_angle.
 */

#ifndef ALIFE_MATH_UTILS_H
#define ALIFE_MATH_UTILS_H

#include <cmath>

namespace alife {

/**
 * @brief Ограничить значение в заданных пределах [min_val, max_val].
 * 
 * Если value меньше min_val, возвращает min_val.
 * Если value больше max_val, возвращает max_val.
 * Иначе возвращает value.
 * 
 * @tparam T Числовой тип (int, float, double, etc.)
 * @param value Значение для ограничения.
 * @param min_val Минимальное значение (включительно).
 * @param max_val Максимальное значение (включительно).
 * @return Значение в диапазоне [min_val, max_val].
 */
template<typename T>
T clamp(T value, T min_val, T max_val);

/**
 * @brief Нормализовать угол к диапазону [-pi, pi].
 * 
 * Преобразует любой угол (в радианах) к эквивалентному углу
 * в диапазоне [-π, π].
 * 
 * Примеры:
 * - normalize_angle(0) = 0
 * - normalize_angle(pi) = pi (или -pi, зависит от реализации)
 * - normalize_angle(-pi) = -pi (или pi, зависит от реализации)
 * - normalize_angle(2*pi) = 0
 * - normalize_angle(3*pi) = pi
 * - normalize_angle(-3*pi) = -pi
 * 
 * @param angle Угол в радианах.
 * @return Нормализованный угол в диапазоне [-pi, pi].
 */
double normalize_angle(double angle);

} // namespace alife

#endif // ALIFE_MATH_UTILS_H
