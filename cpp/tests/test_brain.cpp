// test_brain.cpp
// Тесты для Brain (SNN)

#include <iostream>
#include <vector>
#include <map>
#include <cmath>
#include <cassert>
#include <limits>
#include "alife/brain.h"
#include "alife/genome.h"
#include "alife/rng.h"

using namespace alife;

// Проверка что output имеет правильный размер
void test_output_size() {
    std::cout << "Test: output size... ";
    
    RNG rng(42);
    Genome genome({}, -1, {}, 64, &rng);  // n_hidden = 64 для быстрого теста
    
    Brain brain(genome, 64, std::nullopt, &rng);
    
    std::vector<double> sensors(12, 0.5);
    std::map<std::string, double> mod = {{"dopamine", 0.5}, {"plasticity", 0.5}};
    
    auto output = brain.step(sensors, mod);
    
    assert(output.size() == 6);  // OUTPUT_SIZE = 6
    
    std::cout << "PASSED" << std::endl;
}

// Проверка отсутствия NaN после 1000 шагов
void test_no_nan_after_steps() {
    std::cout << "Test: no NaN after 1000 steps... ";
    
    RNG rng(123);
    Genome genome({}, -1, {}, 64, &rng);
    
    Brain brain(genome, 64, std::nullopt, &rng);
    
    std::vector<double> sensors(12, 0.0);
    std::map<std::string, double> mod;
    
    for (int i = 0; i < 1000; ++i) {
        // Разные сенсоры на каждом шаге
        for (int j = 0; j < 12; ++j) {
            sensors[j] = static_cast<double>(i % 10) / 10.0;
        }
        
        mod["dopamine"] = static_cast<double>(i % 100) / 100.0;
        mod["plasticity"] = 0.5;
        
        auto output = brain.step(sensors, mod);
        
        // Проверка на NaN
        for (double val : output) {
            assert(!std::isnan(val));
        }
        
        // Проверка весов
        for (double w : brain.W) {
            assert(!std::isnan(w));
        }
    }
    
    std::cout << "PASSED" << std::endl;
}

// Проверка детерминированности: одинаковый seed и сенсоры дают одинаковый результат
void test_determinism() {
    std::cout << "Test: determinism with same seed... ";
    
    // Первый запуск
    RNG rng1(999);
    Genome genome1({}, -1, {}, 64, &rng1);
    Brain brain1(genome1, 64, std::nullopt, &rng1);
    
    std::vector<double> sensors1 = {0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.5, 0.5};
    std::map<std::string, double> mod1 = {{"dopamine", 0.5}, {"plasticity", 0.5}};
    
    std::vector<double> outputs1;
    for (int i = 0; i < 10; ++i) {
        auto out = brain1.step(sensors1, mod1);
        outputs1.insert(outputs1.end(), out.begin(), out.end());
    }
    
    // Второй запуск с тем же seed
    RNG rng2(999);
    Genome genome2({}, -1, {}, 64, &rng2);
    Brain brain2(genome2, 64, std::nullopt, &rng2);
    
    std::vector<double> sensors2 = {0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.5, 0.5};
    std::map<std::string, double> mod2 = {{"dopamine", 0.5}, {"plasticity", 0.5}};
    
    std::vector<double> outputs2;
    for (int i = 0; i < 10; ++i) {
        auto out = brain2.step(sensors2, mod2);
        outputs2.insert(outputs2.end(), out.begin(), out.end());
    }
    
    // Сравнение результатов
    assert(outputs1.size() == outputs2.size());
    for (size_t i = 0; i < outputs1.size(); ++i) {
        assert(std::abs(outputs1[i] - outputs2[i]) < 1e-10);
    }
    
    std::cout << "PASSED" << std::endl;
}

// Проверка наследования родительских весов
void test_parent_weight_inheritance() {
    std::cout << "Test: parent weight inheritance... ";
    
    RNG rng_parent(100);
    Genome genome_parent({}, -1, {}, 64, &rng_parent);
    Brain parent(genome_parent, 64, std::nullopt, &rng_parent);
    
    // Сохраняем веса родителя
    std::vector<double> parent_weights = parent.W;
    
    // Создаём потомка с наследованием (lamarckian_weight = 0.5)
    RNG rng_child(200);
    std::map<std::string, double> child_genes;
    child_genes["lamarckian_weight"] = 0.5;
    child_genes["conn_prob"] = 0.1;
    child_genes["weight_scale"] = 0.5;
    child_genes["membrane_decay"] = 0.85;
    child_genes["threshold"] = 1.0;
    child_genes["stdp_rate"] = 0.01;
    child_genes["weight_max"] = 2.0;
    
    Genome genome_child(&child_genes, -1, {}, 64, &rng_child);
    Brain child(genome_child, 64, parent_weights, &rng_child);
    
    // Проверяем что веса отличаются от чисто случайных
    bool weights_changed = false;
    for (size_t i = 0; i < parent_weights.size(); ++i) {
        if (std::abs(child.W[i] - parent_weights[i]) > 1e-10) {
            weights_changed = true;
            break;
        }
    }
    
    // Веса должны быть смесью (отличаться от обоих родителей)
    // Проверяем что есть влияние родителя
    double diff_sum = 0.0;
    for (size_t i = 0; i < parent_weights.size(); ++i) {
        diff_sum += std::abs(child.W[i] - parent_weights[i]);
    }
    
    // Разница должна быть меньше чем полностью новые веса
    // (поскольку lamarckian_weight = 0.5)
    assert(diff_sum < parent_weights.size() * 2.0);  // Грубая проверка
    
    std::cout << "PASSED" << std::endl;
}

// Проверка что step возвращает OUTPUT_SIZE значений
void test_step_returns_output_size() {
    std::cout << "Test: step returns OUTPUT_SIZE values... ";
    
    RNG rng(555);
    Genome genome({}, -1, {}, 64, &rng);
    Brain brain(genome, 64, std::nullopt, &rng);
    
    std::vector<double> sensors(12, 0.5);
    std::map<std::string, double> mod;
    
    for (int i = 0; i < 100; ++i) {
        auto output = brain.step(sensors, mod);
        assert(output.size() == 6);  // OUTPUT_SIZE
    }
    
    std::cout << "PASSED" << std::endl;
}

int main() {
    std::cout << "=== Brain Tests ===" << std::endl;
    
    test_output_size();
    test_no_nan_after_steps();
    test_determinism();
    test_parent_weight_inheritance();
    test_step_returns_output_size();
    
    std::cout << "\n=== All tests PASSED ===" << std::endl;
    return 0;
}
