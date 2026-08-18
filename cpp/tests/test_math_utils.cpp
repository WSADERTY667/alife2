/**
 * @file test_math_utils.cpp
 * @brief Тесты для математических утилит: clamp и normalize_angle.
 */

#include <iostream>
#include <cmath>
#include <cassert>
#include "alife/math_utils.h"

using namespace alife;

// Флаги для отслеживания результатов тестов
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) void name()
#define RUN_TEST(name) do { \
    std::cout << "Running " << #name << "... "; \
    try { \
        name(); \
        std::cout << "PASSED" << std::endl; \
        tests_passed++; \
    } catch (const std::exception& e) { \
        std::cout << "FAILED: " << e.what() << std::endl; \
        tests_failed++; \
    } \
} while(0)

#define ASSERT_EQ(expected, actual) do { \
    if ((expected) != (actual)) { \
        throw std::runtime_error("Assertion failed: " #expected " == " #actual); \
    } \
} while(0)

#define ASSERT_NEAR(expected, actual, epsilon) do { \
    if (std::abs((expected) - (actual)) > (epsilon)) { \
        throw std::runtime_error("Assertion failed: " #expected " ~= " #actual); \
    } \
} while(0)

#define ASSERT_TRUE(cond) do { \
    if (!(cond)) { \
        throw std::runtime_error("Assertion failed: " #cond); \
    } \
} while(0)

// ==================== CLAMP Tests ====================

TEST(test_clamp_int_within_range) {
    ASSERT_EQ(5, clamp(5, 0, 10));
    ASSERT_EQ(5, clamp(5, 5, 10));
    ASSERT_EQ(5, clamp(5, 0, 5));
}

TEST(test_clamp_int_below_min) {
    ASSERT_EQ(0, clamp(-5, 0, 10));
    ASSERT_EQ(0, clamp(0, 0, 10));
    ASSERT_EQ(-10, clamp(-100, -10, 10));
}

TEST(test_clamp_int_above_max) {
    ASSERT_EQ(10, clamp(15, 0, 10));
    ASSERT_EQ(10, clamp(100, 0, 10));
    ASSERT_EQ(10, clamp(100, -10, 10));
}

TEST(test_clamp_float_within_range) {
    ASSERT_NEAR(5.5f, clamp(5.5f, 0.0f, 10.0f), 1e-6f);
    ASSERT_NEAR(0.0f, clamp(0.0f, 0.0f, 10.0f), 1e-6f);
    ASSERT_NEAR(10.0f, clamp(10.0f, 0.0f, 10.0f), 1e-6f);
}

TEST(test_clamp_float_below_min) {
    ASSERT_NEAR(0.0f, clamp(-5.5f, 0.0f, 10.0f), 1e-6f);
    ASSERT_NEAR(-10.0f, clamp(-100.0f, -10.0f, 10.0f), 1e-6f);
}

TEST(test_clamp_float_above_max) {
    ASSERT_NEAR(10.0f, clamp(15.5f, 0.0f, 10.0f), 1e-6f);
    ASSERT_NEAR(10.0f, clamp(100.0f, -10.0f, 10.0f), 1e-6f);
}

TEST(test_clamp_double_precision) {
    ASSERT_NEAR(3.14159265, clamp(3.14159265, 0.0, 10.0), 1e-10);
    ASSERT_NEAR(0.0, clamp(-3.14159265, 0.0, 10.0), 1e-10);
    ASSERT_NEAR(10.0, clamp(20.0, 0.0, 10.0), 1e-10);
}

TEST(test_clamp_negative_range) {
    ASSERT_EQ(-5, clamp(-5, -10, 0));
    ASSERT_EQ(-10, clamp(-15, -10, 0));
    ASSERT_EQ(0, clamp(5, -10, 0));
}

TEST(test_clamp_equal_min_max) {
    ASSERT_EQ(5, clamp(5, 5, 5));
    ASSERT_EQ(5, clamp(0, 5, 5));
    ASSERT_EQ(5, clamp(10, 5, 5));
}

// ==================== NORMALIZE_ANGLE Tests ====================

TEST(test_normalize_angle_zero) {
    ASSERT_NEAR(0.0, normalize_angle(0.0), 1e-10);
}

TEST(test_normalize_angle_pi) {
    // pi должен остаться pi или стать -pi (оба валидны в диапазоне [-pi, pi])
    double result = normalize_angle(M_PI);
    ASSERT_TRUE(std::abs(result - M_PI) < 1e-10 || std::abs(result + M_PI) < 1e-10);
}

TEST(test_normalize_angle_negative_pi) {
    // -pi должен остаться -pi или стать pi
    double result = normalize_angle(-M_PI);
    ASSERT_TRUE(std::abs(result + M_PI) < 1e-10 || std::abs(result - M_PI) < 1e-10);
}

TEST(test_normalize_angle_two_pi) {
    ASSERT_NEAR(0.0, normalize_angle(2.0 * M_PI), 1e-10);
}

TEST(test_normalize_angle_negative_two_pi) {
    ASSERT_NEAR(0.0, normalize_angle(-2.0 * M_PI), 1e-10);
}

TEST(test_normalize_angle_three_pi) {
    // 3*pi = 2*pi + pi -> pi
    double result = normalize_angle(3.0 * M_PI);
    ASSERT_TRUE(std::abs(result - M_PI) < 1e-10 || std::abs(result + M_PI) < 1e-10);
}

TEST(test_normalize_angle_negative_three_pi) {
    // -3*pi = -2*pi - pi -> -pi
    double result = normalize_angle(-3.0 * M_PI);
    ASSERT_TRUE(std::abs(result + M_PI) < 1e-10 || std::abs(result - M_PI) < 1e-10);
}

TEST(test_normalize_angle_positive_small) {
    ASSERT_NEAR(M_PI / 4.0, normalize_angle(M_PI / 4.0), 1e-10);
    ASSERT_NEAR(M_PI / 2.0, normalize_angle(M_PI / 2.0), 1e-10);
}

TEST(test_normalize_angle_negative_small) {
    ASSERT_NEAR(-M_PI / 4.0, normalize_angle(-M_PI / 4.0), 1e-10);
    ASSERT_NEAR(-M_PI / 2.0, normalize_angle(-M_PI / 2.0), 1e-10);
}

TEST(test_normalize_angle_large_positive) {
    // 100*pi = 50 * 2*pi -> 0
    ASSERT_NEAR(0.0, normalize_angle(100.0 * M_PI), 1e-10);
    // 101*pi = 50 * 2*pi + pi -> pi
    double result = normalize_angle(101.0 * M_PI);
    ASSERT_TRUE(std::abs(result - M_PI) < 1e-10 || std::abs(result + M_PI) < 1e-10);
}

TEST(test_normalize_angle_large_negative) {
    // -100*pi = -50 * 2*pi -> 0
    ASSERT_NEAR(0.0, normalize_angle(-100.0 * M_PI), 1e-10);
    // -101*pi = -50 * 2*pi - pi -> -pi
    double result = normalize_angle(-101.0 * M_PI);
    ASSERT_TRUE(std::abs(result + M_PI) < 1e-10 || std::abs(result - M_PI) < 1e-10);
}

TEST(test_normalize_angle_quarter_turns) {
    ASSERT_NEAR(M_PI / 2.0, normalize_angle(M_PI / 2.0), 1e-10);
    // pi остается в диапазоне [-pi, pi], может быть pi или -pi
    double pi_result = normalize_angle(M_PI);
    ASSERT_TRUE(std::abs(pi_result - M_PI) < 1e-10 || std::abs(pi_result + M_PI) < 1e-10);
    ASSERT_NEAR(-M_PI / 2.0, normalize_angle(3.0 * M_PI / 2.0), 1e-10);  // 3*pi/2 -> -pi/2
    ASSERT_NEAR(0.0, normalize_angle(4.0 * M_PI / 2.0), 1e-10);  // 2*pi -> 0
}

TEST(test_normalize_angle_result_in_range) {
    // Проверяем, что результат всегда в диапазоне [-pi, pi]
    double test_angles[] = {0.1, 1.0, 10.0, 100.0, 1000.0, -0.1, -1.0, -10.0, -100.0, -1000.0};
    for (double angle : test_angles) {
        double result = normalize_angle(angle);
        ASSERT_TRUE(result >= -M_PI && result <= M_PI);
    }
}

int main() {
    std::cout << "=== Math Utils Tests ===" << std::endl;
    std::cout << std::endl;
    
    // Clamp tests
    std::cout << "--- Clamp Tests ---" << std::endl;
    RUN_TEST(test_clamp_int_within_range);
    RUN_TEST(test_clamp_int_below_min);
    RUN_TEST(test_clamp_int_above_max);
    RUN_TEST(test_clamp_float_within_range);
    RUN_TEST(test_clamp_float_below_min);
    RUN_TEST(test_clamp_float_above_max);
    RUN_TEST(test_clamp_double_precision);
    RUN_TEST(test_clamp_negative_range);
    RUN_TEST(test_clamp_equal_min_max);
    std::cout << std::endl;
    
    // Normalize angle tests
    std::cout << "--- Normalize Angle Tests ---" << std::endl;
    RUN_TEST(test_normalize_angle_zero);
    RUN_TEST(test_normalize_angle_pi);
    RUN_TEST(test_normalize_angle_negative_pi);
    RUN_TEST(test_normalize_angle_two_pi);
    RUN_TEST(test_normalize_angle_negative_two_pi);
    RUN_TEST(test_normalize_angle_three_pi);
    RUN_TEST(test_normalize_angle_negative_three_pi);
    RUN_TEST(test_normalize_angle_positive_small);
    RUN_TEST(test_normalize_angle_negative_small);
    RUN_TEST(test_normalize_angle_large_positive);
    RUN_TEST(test_normalize_angle_large_negative);
    RUN_TEST(test_normalize_angle_quarter_turns);
    RUN_TEST(test_normalize_angle_result_in_range);
    std::cout << std::endl;
    
    std::cout << "=== Test Summary ===" << std::endl;
    std::cout << "Passed: " << tests_passed << std::endl;
    std::cout << "Failed: " << tests_failed << std::endl;
    
    return tests_failed == 0 ? 0 : 1;
}
