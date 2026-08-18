/**
 * @file test_rng.cpp
 * @brief Тесты для детерминированного RNG (SplitMix64).
 * 
 * Проверяет совместимость с Python реализацией через golden-значения.
 */

#include <iostream>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>
#include <cassert>
#include "alife/rng.h"

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

#define ASSERT_TRUE(cond) do { \
    if (!(cond)) { \
        throw std::runtime_error("Assertion failed: " #cond); \
    } \
} while(0)

#define ASSERT_FALSE(cond) do { \
    if (cond) { \
        throw std::runtime_error("Assertion failed: !" #cond); \
    } \
} while(0)

#define ASSERT_NEAR(expected, actual, epsilon) do { \
    if (std::abs((expected) - (actual)) > (epsilon)) { \
        throw std::runtime_error("Assertion failed: " #expected " ~= " #actual); \
    } \
} while(0)

// Golden values из Python реализации
// Получены через: python3 -c "from alife.rng import RNG; rng = RNG(seed=42); [print(rng.next_int()) for _ in range(5)]"

// seed=42 golden values
const uint32_t SEED42_NEXT_INT[] = {803958421, 2993090819, 319790930, 239788948, 608707570};
const double SEED42_NEXT_FLOAT[] = {0.1871861566323787, 0.6968832619022578, 0.07445712806656957, 0.055830215103924274, 0.1417257753200829};

// seed=123 golden values
const uint32_t SEED123_NEXT_INT[] = {1658732843, 4033853308, 3547450344, 2425913855, 2014243122};
const double SEED123_NEXT_FLOAT[] = {0.3862038354855031, 0.9392046621069312, 0.8259551469236612, 0.5648270843084902, 0.46897752257063985};

// seed=2026 golden values
const uint32_t SEED2026_NEXT_INT[] = {2442431779, 3979691357, 3454187662, 3584099570, 127467337};
const double SEED2026_NEXT_FLOAT[] = {0.5686729631852359, 0.9265941001940519, 0.8042407366447151, 0.8344882098026574, 0.02967830211855471};

TEST(test_seed42_next_int) {
    RNG rng(42);
    for (int i = 0; i < 5; i++) {
        ASSERT_EQ(SEED42_NEXT_INT[i], rng.next_int());
    }
}

TEST(test_seed42_next_float) {
    RNG rng(42);
    for (int i = 0; i < 5; i++) {
        ASSERT_NEAR(SEED42_NEXT_FLOAT[i], rng.next_float(), 1e-10);
    }
}

TEST(test_seed123_next_int) {
    RNG rng(123);
    for (int i = 0; i < 5; i++) {
        ASSERT_EQ(SEED123_NEXT_INT[i], rng.next_int());
    }
}

TEST(test_seed123_next_float) {
    RNG rng(123);
    for (int i = 0; i < 5; i++) {
        ASSERT_NEAR(SEED123_NEXT_FLOAT[i], rng.next_float(), 1e-10);
    }
}

TEST(test_seed2026_next_int) {
    RNG rng(2026);
    for (int i = 0; i < 5; i++) {
        ASSERT_EQ(SEED2026_NEXT_INT[i], rng.next_int());
    }
}

TEST(test_seed2026_next_float) {
    RNG rng(2026);
    for (int i = 0; i < 5; i++) {
        ASSERT_NEAR(SEED2026_NEXT_FLOAT[i], rng.next_float(), 1e-10);
    }
}

TEST(test_same_seed_same_sequence) {
    RNG rng1(42);
    RNG rng2(42);
    for (int i = 0; i < 100; i++) {
        ASSERT_EQ(rng1.next_int(), rng2.next_int());
    }
}

TEST(test_zero_seed) {
    RNG rng1(0);
    RNG rng2(0);
    for (int i = 0; i < 10; i++) {
        ASSERT_EQ(rng1.next_int(), rng2.next_int());
    }
}

TEST(test_negative_seed) {
    RNG rng1(-42);
    RNG rng2(-42);
    for (int i = 0; i < 10; i++) {
        ASSERT_EQ(rng1.next_int(), rng2.next_int());
    }
}

TEST(test_large_seed) {
    // 2^63 + 12345
    RNG rng1(static_cast<int64_t>(1LL << 63) + 12345);
    RNG rng2(static_cast<int64_t>(1LL << 63) + 12345);
    for (int i = 0; i < 10; i++) {
        ASSERT_EQ(rng1.next_int(), rng2.next_int());
    }
}

TEST(test_next_int_range) {
    RNG rng(42);
    for (int i = 0; i < 1000; i++) {
        uint32_t value = rng.next_int();
        ASSERT_TRUE(value < (1ULL << 32));
    }
}

TEST(test_next_float_range) {
    RNG rng(42);
    for (int i = 0; i < 1000; i++) {
        double value = rng.next_float();
        ASSERT_TRUE(value >= 0.0 && value < 1.0);
    }
}

TEST(test_randint_range) {
    RNG rng(42);
    for (int i = 0; i < 1000; i++) {
        int32_t value = rng.randint(10, 20);
        ASSERT_TRUE(value >= 10 && value <= 20);
    }
}

TEST(test_randint_single_value) {
    RNG rng(42);
    for (int i = 0; i < 10; i++) {
        ASSERT_EQ(42, rng.randint(42, 42));
    }
}

TEST(test_randint_invalid_range) {
    RNG rng(42);
    bool threw = false;
    try {
        rng.randint(10, 5);
    } catch (const std::invalid_argument&) {
        threw = true;
    }
    ASSERT_TRUE(threw);
}

TEST(test_choice_from_vector) {
    RNG rng(42);
    std::vector<int> items = {1, 2, 3, 4, 5};
    for (int i = 0; i < 100; i++) {
        int value = rng.choice(items);
        ASSERT_TRUE(value >= 1 && value <= 5);
    }
}

TEST(test_choice_from_string) {
    RNG rng(42);
    std::string s = "hello";
    for (int i = 0; i < 50; i++) {
        char c = rng.choice(s);
        ASSERT_TRUE(c == 'h' || c == 'e' || c == 'l' || c == 'l' || c == 'o');
    }
}

TEST(test_choice_empty_vector) {
    RNG rng(42);
    std::vector<int> empty;
    bool threw = false;
    try {
        rng.choice(empty);
    } catch (const std::out_of_range&) {
        threw = true;
    }
    ASSERT_TRUE(threw);
}

TEST(test_choice_deterministic) {
    RNG rng1(999);
    RNG rng2(999);
    std::vector<char> items = {'a', 'b', 'c', 'd', 'e'};
    for (int i = 0; i < 50; i++) {
        ASSERT_EQ(rng1.choice(items), rng2.choice(items));
    }
}

TEST(test_gauss_returns_finite) {
    RNG rng(42);
    for (int i = 0; i < 100; i++) {
        double value = rng.gauss();
        ASSERT_TRUE(std::isfinite(value));
    }
}

TEST(test_gauss_mean_approximation) {
    RNG rng(42);
    double mu = 5.0;
    double sigma = 1.0;
    
    std::vector<double> values;
    for (int i = 0; i < 1000; i++) {
        values.push_back(rng.gauss(mu, sigma));
    }
    
    double sum = 0.0;
    for (double v : values) {
        sum += v;
    }
    double mean = sum / values.size();
    
    // Среднее должно быть близко к mu (с допуском для случайности)
    ASSERT_NEAR(mu, mean, 0.5);
}

TEST(test_gauss_invalid_sigma) {
    RNG rng(42);
    bool threw = false;
    try {
        rng.gauss(0.0, 0.0);
    } catch (const std::invalid_argument&) {
        threw = true;
    }
    ASSERT_TRUE(threw);
}

TEST(test_gauss_deterministic) {
    RNG rng1(777);
    RNG rng2(777);
    for (int i = 0; i < 50; i++) {
        ASSERT_EQ(rng1.gauss(), rng2.gauss());
    }
}

TEST(test_shuffle_preserves_elements) {
    RNG rng(42);
    std::vector<int> original = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    std::vector<int> shuffled = original;
    rng.shuffle(shuffled);
    
    std::sort(shuffled.begin(), shuffled.end());
    ASSERT_EQ(original, shuffled);
}

TEST(test_shuffle_deterministic) {
    std::vector<int> original = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    
    RNG rng1(555);
    RNG rng2(555);
    
    std::vector<int> lst1 = original;
    std::vector<int> lst2 = original;
    
    rng1.shuffle(lst1);
    rng2.shuffle(lst2);
    
    ASSERT_EQ(lst1, lst2);
}

TEST(test_shuffle_empty_list) {
    RNG rng(42);
    std::vector<int> lst;
    rng.shuffle(lst);
    ASSERT_TRUE(lst.empty());
}

TEST(test_shuffle_single_element) {
    RNG rng(42);
    std::vector<int> lst = {42};
    rng.shuffle(lst);
    ASSERT_EQ(lst.size(), 1);
    ASSERT_EQ(lst[0], 42);
}

TEST(test_copy_same_state) {
    RNG rng1(42);
    // Прогоним несколько значений
    for (int i = 0; i < 10; i++) {
        rng1.next_int();
    }
    
    RNG rng2 = rng1.copy();
    
    // Копия должна давать те же значения
    for (int i = 0; i < 100; i++) {
        ASSERT_EQ(rng1.next_int(), rng2.next_int());
    }
}

TEST(test_copy_independent) {
    RNG rng1(42);
    RNG rng2 = rng1.copy();
    
    // Продвигаем только оригинал на несколько шагов
    for (int i = 0; i < 5; i++) {
        rng1.next_int();
    }
    
    // Копия должна оставаться в исходном состоянии
    RNG rng3(42);  // Третий RNG с тем же начальным seed
    
    // Теперь rng2 (копия) должен давать те же значения, что rng3
    for (int i = 0; i < 10; i++) {
        ASSERT_EQ(rng2.next_int(), rng3.next_int());
    }
}

TEST(test_get_set_state) {
    RNG rng1(42);
    for (int i = 0; i < 10; i++) {
        rng1.next_int();
    }
    
    uint64_t state = rng1.get_state();
    
    RNG rng2(0);
    rng2.set_state(static_cast<int64_t>(state));
    
    for (int i = 0; i < 100; i++) {
        ASSERT_EQ(rng1.next_int(), rng2.next_int());
    }
}

TEST(test_uniform_range) {
    RNG rng(42);
    for (int i = 0; i < 1000; i++) {
        double value = rng.uniform(10.0, 20.0);
        ASSERT_TRUE(value >= 10.0 && value <= 20.0);
    }
}

TEST(test_uniform_deterministic) {
    RNG rng1(12345);
    RNG rng2(12345);
    for (int i = 0; i < 50; i++) {
        ASSERT_EQ(rng1.uniform(0.0, 100.0), rng2.uniform(0.0, 100.0));
    }
}

int main() {
    std::cout << "=== RNG Tests ===" << std::endl;
    std::cout << std::endl;
    
    // Golden value tests
    std::cout << "--- Golden Value Tests ---" << std::endl;
    RUN_TEST(test_seed42_next_int);
    RUN_TEST(test_seed42_next_float);
    RUN_TEST(test_seed123_next_int);
    RUN_TEST(test_seed123_next_float);
    RUN_TEST(test_seed2026_next_int);
    RUN_TEST(test_seed2026_next_float);
    std::cout << std::endl;
    
    // Determinism tests
    std::cout << "--- Determinism Tests ---" << std::endl;
    RUN_TEST(test_same_seed_same_sequence);
    RUN_TEST(test_zero_seed);
    RUN_TEST(test_negative_seed);
    RUN_TEST(test_large_seed);
    std::cout << std::endl;
    
    // next_int tests
    std::cout << "--- next_int Tests ---" << std::endl;
    RUN_TEST(test_next_int_range);
    std::cout << std::endl;
    
    // next_float tests
    std::cout << "--- next_float Tests ---" << std::endl;
    RUN_TEST(test_next_float_range);
    std::cout << std::endl;
    
    // randint tests
    std::cout << "--- randint Tests ---" << std::endl;
    RUN_TEST(test_randint_range);
    RUN_TEST(test_randint_single_value);
    RUN_TEST(test_randint_invalid_range);
    std::cout << std::endl;
    
    // choice tests
    std::cout << "--- choice Tests ---" << std::endl;
    RUN_TEST(test_choice_from_vector);
    RUN_TEST(test_choice_from_string);
    RUN_TEST(test_choice_empty_vector);
    RUN_TEST(test_choice_deterministic);
    std::cout << std::endl;
    
    // gauss tests
    std::cout << "--- gauss Tests ---" << std::endl;
    RUN_TEST(test_gauss_returns_finite);
    RUN_TEST(test_gauss_mean_approximation);
    RUN_TEST(test_gauss_invalid_sigma);
    RUN_TEST(test_gauss_deterministic);
    std::cout << std::endl;
    
    // shuffle tests
    std::cout << "--- shuffle Tests ---" << std::endl;
    RUN_TEST(test_shuffle_preserves_elements);
    RUN_TEST(test_shuffle_deterministic);
    RUN_TEST(test_shuffle_empty_list);
    RUN_TEST(test_shuffle_single_element);
    std::cout << std::endl;
    
    // copy tests
    std::cout << "--- copy Tests ---" << std::endl;
    RUN_TEST(test_copy_same_state);
    RUN_TEST(test_copy_independent);
    std::cout << std::endl;
    
    // state tests
    std::cout << "--- get_state/set_state Tests ---" << std::endl;
    RUN_TEST(test_get_set_state);
    std::cout << std::endl;
    
    // uniform tests
    std::cout << "--- uniform Tests ---" << std::endl;
    RUN_TEST(test_uniform_range);
    RUN_TEST(test_uniform_deterministic);
    std::cout << std::endl;
    
    std::cout << "=== Test Summary ===" << std::endl;
    std::cout << "Passed: " << tests_passed << std::endl;
    std::cout << "Failed: " << tests_failed << std::endl;
    
    return tests_failed == 0 ? 0 : 1;
}
