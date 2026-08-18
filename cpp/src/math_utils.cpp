/**
 * @file math_utils.cpp
 * @brief Файл реализации для математических утилит.
 */

#include "alife/math_utils.h"

namespace alife {

template<typename T>
T clamp(T value, T min_val, T max_val) {
    if (value < min_val) {
        return min_val;
    }
    if (value > max_val) {
        return max_val;
    }
    return value;
}

// Явная инстанциация шаблона для распространенных типов
template int clamp<int>(int, int, int);
template float clamp<float>(float, float, float);
template double clamp<double>(double, double, double);

double normalize_angle(double angle) {
    // Нормализуем угол к диапазону [-pi, pi]
    // Используем fmod для приведения к диапазону [0, 2*pi) или (-2*pi, 2*pi)
    const double TWO_PI = 2.0 * M_PI;
    
    // Приводим к диапазону (-2*pi, 2*pi)
    angle = std::fmod(angle, TWO_PI);
    
    // Теперь приводим к диапазону [-pi, pi]
    if (angle > M_PI) {
        angle -= TWO_PI;
    } else if (angle <= -M_PI) {
        angle += TWO_PI;
    }
    
    return angle;
}

} // namespace alife
