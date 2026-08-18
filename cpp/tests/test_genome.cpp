/**
 * @file test_genome.cpp
 * @brief Тесты для Genome (C++ реализация).
 * 
 * Проверяет:
 * - мутация не выходит за границы;
 * - crossover создаёт валидный геном;
 * - genome_similarity возвращает значение от 0 до 1;
 * - одинаковый seed даёт одинаковый результат.
 */

#include <iostream>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>
#include <cassert>
#include <map>
#include "alife/genome.h"
#include "alife/rng.h"
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
// Получены через: python3 tools/export_genome_golden.py

// Parent A (seed=10) first 5 genes
constexpr double PARENT_A_MUTATION_RATE = 0.16258202844439074;
constexpr double PARENT_A_CONN_PROB = 0.11896431463304907;
constexpr double PARENT_A_WEIGHT_SCALE = 0.29311859878944235;
constexpr double PARENT_A_WEIGHT_MAX = 1.22187707293778658;
constexpr double PARENT_A_MEMBRANE_DECAY = 0.79031175963580602;
constexpr int PARENT_A_TAG = 0;
constexpr int PARENT_A_N_HIDDEN = 160;

// Parent B (seed=20) first 5 genes
constexpr double PARENT_B_MUTATION_RATE = 0.08519643107149749;
constexpr double PARENT_B_CONN_PROB = 0.17092834946466609;
constexpr double PARENT_B_WEIGHT_SCALE = 1.24028575712582101;
constexpr double PARENT_B_WEIGHT_MAX = 1.93926508491858840;
constexpr double PARENT_B_MEMBRANE_DECAY = 0.81866806351579724;
constexpr int PARENT_B_TAG = 0;
constexpr int PARENT_B_N_HIDDEN = 160;

// Child after crossover (crossover seed=123) first 5 genes
constexpr double CHILD_CROSSOVER_MUTATION_RATE = 0.16258202844439074;
constexpr double CHILD_CROSSOVER_CONN_PROB = 0.14494633204885760;
constexpr double CHILD_CROSSOVER_WEIGHT_SCALE = 1.24028575712582101;
constexpr double CHILD_CROSSOVER_WEIGHT_MAX = 1.93926508491858840;
constexpr double CHILD_CROSSOVER_MEMBRANE_DECAY = 0.81866806351579724;
constexpr int CHILD_CROSSOVER_TAG = 0;
constexpr int CHILD_CROSSOVER_N_HIDDEN = 160;

// Similarity golden values
constexpr double SIMILARITY_IDENTICAL = 0.80000000000000004;
constexpr double SIMILARITY_DIFFERENT = 0.31630424923496320;

TEST(test_genome_keys_not_empty) {
    ASSERT_TRUE(!GENOME_KEYS.empty());
    ASSERT_EQ(static_cast<size_t>(34), GENOME_KEYS.size());
}

TEST(test_bounds_contains_all_keys) {
    for (const auto& key : GENOME_KEYS) {
        auto it = BOUNDS.find(key);
        ASSERT_TRUE(it != BOUNDS.end());
    }
}

TEST(test_mut_scale_computed) {
    for (const auto& key : GENOME_KEYS) {
        auto it = MUT_SCALE.find(key);
        ASSERT_TRUE(it != MUT_SCALE.end());
        ASSERT_TRUE(it->second > 0.0);
    }
}

TEST(test_genome_creation_with_seed) {
    RNG rng(10);
    Genome g(nullptr, -1, {}, -1, &rng);
    
    // Проверяем первые 5 генов
    ASSERT_NEAR(PARENT_A_MUTATION_RATE, g["mutation_rate"], 1e-10);
    ASSERT_NEAR(PARENT_A_CONN_PROB, g["conn_prob"], 1e-10);
    ASSERT_NEAR(PARENT_A_WEIGHT_SCALE, g["weight_scale"], 1e-10);
    ASSERT_NEAR(PARENT_A_WEIGHT_MAX, g["weight_max"], 1e-10);
    ASSERT_NEAR(PARENT_A_MEMBRANE_DECAY, g["membrane_decay"], 1e-10);
    
    // Проверяем tag и n_hidden
    ASSERT_EQ(PARENT_A_TAG, g.tag);
    ASSERT_EQ(PARENT_A_N_HIDDEN, g.n_hidden);
}

TEST(test_genome_same_seed_same_result) {
    RNG rng1(10);
    Genome g1(nullptr, -1, {}, -1, &rng1);
    
    RNG rng2(10);
    Genome g2(nullptr, -1, {}, -1, &rng2);
    
    // Все гены должны совпадать
    for (const auto& key : GENOME_KEYS) {
        ASSERT_NEAR(g1[key], g2[key], 1e-10);
    }
    
    ASSERT_EQ(g1.tag, g2.tag);
    ASSERT_EQ(g1.n_hidden, g2.n_hidden);
}

TEST(test_mutation_keeps_bounds) {
    RNG rng_init(777);
    Genome g(nullptr, -1, {}, -1, &rng_init);
    
    // Выполняем 100 мутаций с разными seed
    for (int i = 0; i < 100; i++) {
        RNG mut_rng(i);
        g.mutate(&mut_rng);
    }
    
    // Проверяем, что все гены в границах
    for (const auto& key : GENOME_KEYS) {
        auto bounds_it = BOUNDS.find(key);
        ASSERT_TRUE(bounds_it != BOUNDS.end());
        
        double value = g[key];
        double lo = bounds_it->second.first;
        double hi = bounds_it->second.second;
        
        ASSERT_TRUE(value >= lo && value <= hi);
    }
}

TEST(test_crossover_creates_valid_genome) {
    RNG rng_a(10);
    Genome parent_a(nullptr, -1, {}, -1, &rng_a);
    
    RNG rng_b(20);
    Genome parent_b(nullptr, -1, {}, -1, &rng_b);
    
    RNG rng_c(123);
    Genome child = Genome::crossover(parent_a, parent_b, &rng_c);
    
    // Проверяем первые 5 генов
    ASSERT_NEAR(CHILD_CROSSOVER_MUTATION_RATE, child["mutation_rate"], 1e-10);
    ASSERT_NEAR(CHILD_CROSSOVER_CONN_PROB, child["conn_prob"], 1e-10);
    ASSERT_NEAR(CHILD_CROSSOVER_WEIGHT_SCALE, child["weight_scale"], 1e-10);
    ASSERT_NEAR(CHILD_CROSSOVER_WEIGHT_MAX, child["weight_max"], 1e-10);
    ASSERT_NEAR(CHILD_CROSSOVER_MEMBRANE_DECAY, child["membrane_decay"], 1e-10);
    
    // Проверяем, что все гены в границах
    for (const auto& key : GENOME_KEYS) {
        auto bounds_it = BOUNDS.find(key);
        ASSERT_TRUE(bounds_it != BOUNDS.end());
        
        double value = child[key];
        double lo = bounds_it->second.first;
        double hi = bounds_it->second.second;
        
        ASSERT_TRUE(value >= lo && value <= hi);
    }
}

TEST(test_crossover_same_seed_same_result) {
    RNG rng_a1(10);
    Genome pa1(nullptr, -1, {}, -1, &rng_a1);
    RNG rng_b1(20);
    Genome pb1(nullptr, -1, {}, -1, &rng_b1);
    RNG rng_c1(123);
    Genome child1 = Genome::crossover(pa1, pb1, &rng_c1);
    
    RNG rng_a2(10);
    Genome pa2(nullptr, -1, {}, -1, &rng_a2);
    RNG rng_b2(20);
    Genome pb2(nullptr, -1, {}, -1, &rng_b2);
    RNG rng_c2(123);
    Genome child2 = Genome::crossover(pa2, pb2, &rng_c2);
    
    // Все гены должны совпадать
    for (const auto& key : GENOME_KEYS) {
        ASSERT_NEAR(child1[key], child2[key], 1e-10);
    }
    
    ASSERT_EQ(child1.tag, child2.tag);
    ASSERT_EQ(child1.n_hidden, child2.n_hidden);
}

TEST(test_mutation_same_seed_same_result) {
    // Создаём идентичные геномы
    RNG rng1(99);
    Genome g1(nullptr, -1, {}, -1, &rng1);
    g1.tag = 3;
    g1.n_hidden = 200;
    
    RNG rng2(99);
    Genome g2(nullptr, -1, {}, -1, &rng2);
    g2.tag = 3;
    g2.n_hidden = 200;
    
    // Мутируем с одинаковым seed
    RNG mut_rng1(456);
    g1.mutate(&mut_rng1);
    
    RNG mut_rng2(456);
    g2.mutate(&mut_rng2);
    
    // Все гены должны совпадать после мутации
    for (const auto& key : GENOME_KEYS) {
        ASSERT_NEAR(g1[key], g2[key], 1e-10);
    }
    
    ASSERT_EQ(g1.tag, g2.tag);
    ASSERT_EQ(g1.n_hidden, g2.n_hidden);
}

TEST(test_full_lifecycle_determinism) {
    // Первый прогон
    RNG rng_pa1(1);
    Genome pa1(nullptr, -1, {}, -1, &rng_pa1);
    RNG rng_pb1(2);
    Genome pb1(nullptr, -1, {}, -1, &rng_pb1);
    RNG rng_c1(3);
    Genome child1 = Genome::crossover(pa1, pb1, &rng_c1);
    RNG rng_m1(4);
    child1.mutate(&rng_m1);
    
    // Второй прогон с теми же seed
    RNG rng_pa2(1);
    Genome pa2(nullptr, -1, {}, -1, &rng_pa2);
    RNG rng_pb2(2);
    Genome pb2(nullptr, -1, {}, -1, &rng_pb2);
    RNG rng_c2(3);
    Genome child2 = Genome::crossover(pa2, pb2, &rng_c2);
    RNG rng_m2(4);
    child2.mutate(&rng_m2);
    
    // Проверяем идентичность финального генома
    for (const auto& key : GENOME_KEYS) {
        ASSERT_NEAR(child1[key], child2[key], 1e-10);
    }
    
    ASSERT_EQ(child1.tag, child2.tag);
    ASSERT_EQ(child1.n_hidden, child2.n_hidden);
}

TEST(test_genome_similarity_range) {
    RNG rng1(100);
    Genome g1(nullptr, -1, {}, -1, &rng1);
    
    RNG rng2(200);
    Genome g2(nullptr, -1, {}, -1, &rng2);
    
    double sim = genome_similarity(g1, g2);
    
    // Similarity должна быть в диапазоне [0, 1]
    ASSERT_TRUE(sim >= 0.0 && sim <= 1.0);
}

TEST(test_genome_similarity_identical) {
    // Создаём два одинаковых генома
    RNG rng1(999);
    Genome g1(nullptr, -1, {}, -1, &rng1);
    g1.tag = 3;
    g1.n_hidden = 200;
    
    RNG rng2(999);
    Genome g2(nullptr, -1, {}, -1, &rng2);
    g2.tag = 3;
    g2.n_hidden = 200;
    
    double sim = genome_similarity(g1, g2);
    
    // Оживаем схожесть ~0.8 (идентичные гены + тег + n_hidden)
    ASSERT_NEAR(SIMILARITY_IDENTICAL, sim, 1e-10);
}

TEST(test_genome_similarity_different) {
    // Создаём два разных генома
    RNG rng1(100);
    Genome g1(nullptr, -1, {}, -1, &rng1);
    g1.tag = 0;
    g1.n_hidden = 100;
    
    RNG rng2(200);
    Genome g2(nullptr, -1, {}, -1, &rng2);
    g2.tag = 7;
    g2.n_hidden = 300;
    
    double sim = genome_similarity(g1, g2);
    
    // Оживаем низкую схожесть
    ASSERT_NEAR(SIMILARITY_DIFFERENT, sim, 1e-10);
}

TEST(test_genome_similarity_same_object) {
    RNG rng(42);
    Genome g(nullptr, -1, {}, -1, &rng);
    
    double sim = genome_similarity(g, g);
    
    // Схожесть объекта с самим собой должна быть 0.8 (т.к. tribal_tags пустые)
    // gene_sim = 1.0, tag_sim = 1.0, tag_overlap = 0.0 (пустые), arch_sim = 1.0
    // result = 0.5 * 1.0 + 0.15 * 1.0 + 0.2 * 0.0 + 0.15 * 1.0 = 0.8
    ASSERT_NEAR(0.8, sim, 1e-10);
}

TEST(test_tribal_tags_inheritance) {
    Genome parent_a(nullptr, 0, {"tag_a1", "tag_a2"}, 160);
    Genome parent_b(nullptr, 1, {"tag_b1", "tag_b2", "tag_b3"}, 200);
    
    RNG rng(42);
    Genome child = Genome::crossover(parent_a, parent_b, &rng);
    
    // Проверяем, что у ребёнка есть теги от обоих родителей
    ASSERT_TRUE(!child.tribal_tags.empty());
    
    // Проверяем, что количество тегов <= 5
    ASSERT_TRUE(static_cast<int>(child.tribal_tags.size()) <= 5);
}

TEST(test_n_hidden_bounds) {
    Genome g(nullptr, 0, {}, 200);
    
    // Мутации, которые могут изменить n_hidden
    for (int i = 0; i < 100; i++) {
        RNG rng(i);
        g.mutate(&rng);
    }
    
    // Проверяем, что n_hidden в границах [40, 400]
    ASSERT_TRUE(g.n_hidden >= 40 && g.n_hidden <= 400);
}

TEST(test_get_method) {
    RNG rng(42);
    Genome g(nullptr, -1, {}, -1, &rng);
    
    double value = g.get("mutation_rate", 0.0);
    ASSERT_TRUE(value > 0.0);
    
    double default_value = g.get("nonexistent_key", 42.0);
    ASSERT_EQ(42.0, default_value);
}

TEST(test_operator_bracket) {
    RNG rng(42);
    Genome g(nullptr, -1, {}, -1, &rng);
    
    double value = g["mutation_rate"];
    ASSERT_TRUE(value > 0.0);
    
    // Модификация через operator[]
    g["mutation_rate"] = 0.5;
    ASSERT_NEAR(0.5, g["mutation_rate"], 1e-10);
}

int main() {
    std::cout << "=== Genome Tests ===" << std::endl;
    std::cout << std::endl;
    
    // Basic structure tests
    std::cout << "--- Structure Tests ---" << std::endl;
    RUN_TEST(test_genome_keys_not_empty);
    RUN_TEST(test_bounds_contains_all_keys);
    RUN_TEST(test_mut_scale_computed);
    std::cout << std::endl;
    
    // Creation tests
    std::cout << "--- Creation Tests ---" << std::endl;
    RUN_TEST(test_genome_creation_with_seed);
    RUN_TEST(test_genome_same_seed_same_result);
    std::cout << std::endl;
    
    // Mutation tests
    std::cout << "--- Mutation Tests ---" << std::endl;
    RUN_TEST(test_mutation_keeps_bounds);
    RUN_TEST(test_mutation_same_seed_same_result);
    std::cout << std::endl;
    
    // Crossover tests
    std::cout << "--- Crossover Tests ---" << std::endl;
    RUN_TEST(test_crossover_creates_valid_genome);
    RUN_TEST(test_crossover_same_seed_same_result);
    std::cout << std::endl;
    
    // Lifecycle tests
    std::cout << "--- Lifecycle Tests ---" << std::endl;
    RUN_TEST(test_full_lifecycle_determinism);
    std::cout << std::endl;
    
    // Similarity tests
    std::cout << "--- Similarity Tests ---" << std::endl;
    RUN_TEST(test_genome_similarity_range);
    RUN_TEST(test_genome_similarity_identical);
    RUN_TEST(test_genome_similarity_different);
    RUN_TEST(test_genome_similarity_same_object);
    std::cout << std::endl;
    
    // Tribal tags tests
    std::cout << "--- Tribal Tags Tests ---" << std::endl;
    RUN_TEST(test_tribal_tags_inheritance);
    std::cout << std::endl;
    
    // n_hidden bounds tests
    std::cout << "--- n_hidden Bounds Tests ---" << std::endl;
    RUN_TEST(test_n_hidden_bounds);
    std::cout << std::endl;
    
    // Accessor tests
    std::cout << "--- Accessor Tests ---" << std::endl;
    RUN_TEST(test_get_method);
    RUN_TEST(test_operator_bracket);
    std::cout << std::endl;
    
    std::cout << "=== Test Summary ===" << std::endl;
    std::cout << "Passed: " << tests_passed << std::endl;
    std::cout << "Failed: " << tests_failed << std::endl;
    
    return tests_failed == 0 ? 0 : 1;
}
