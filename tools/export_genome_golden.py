#!/usr/bin/env python3
"""
Экспорт эталонных значений Genome для вставки в C++ тесты.

Генерирует родительские геномы, child genome после crossover и mutation
с фиксированными seed для обеспечения детерминированности.
"""

import sys
import os

# Добавляем путь к модулю alife
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from alife.genome import Genome, GENOME_KEYS, BOUNDS
from alife.rng import RNG


def format_double(value, indent=4):
    """Форматировать double значение для C++ кода."""
    return f"{' ' * indent}{value:.17f}"


def export_genome(name, genome, indent=4):
    """Экспортировать геном в формате C++."""
    print(f"// {name}")
    print(f"std::map<std::string, double> {name}_genes = {{")
    for key in GENOME_KEYS:
        value = genome[key]
        print(f'    {{"{key}", {value:.17f}}},')
    print("};")
    print(f"const int {name}_tag = {genome.tag};")
    print(f"const int {name}_n_hidden = {genome.n_hidden};")
    print()


def main():
    """Основная функция экспорта эталонных значений."""
    print("// Эталонные значения Genome")
    print("// Сгенерировано с помощью tools/export_genome_golden.py")
    print("// Для использования в C++ тестах")
    print()
    
    # Создаём родителей с фиксированными seed
    rng_a = RNG(10)
    parent_a = Genome(rng=rng_a)
    
    rng_b = RNG(20)
    parent_b = Genome(rng=rng_b)
    
    print("// === Родитель A (seed=10) ===")
    export_genome("parent_a", parent_a)
    
    print("// === Родитель B (seed=20) ===")
    export_genome("parent_b", parent_b)
    
    # Кроссовер с фиксированным seed
    rng_c = RNG(123)
    child_after_crossover = Genome.crossover(parent_a, parent_b, rng=rng_c)
    
    print("// === Child после crossover (crossover seed=123) ===")
    export_genome("child_crossover", child_after_crossover)
    
    # Мутация с фиксированным seed
    rng_m = RNG(456)
    child_after_mutation = Genome.crossover(parent_a, parent_b, rng=RNG(123))
    child_after_mutation.mutate(rng=rng_m)
    
    print("// === Child после mutation (mutation seed=456) ===")
    export_genome("child_mutation", child_after_mutation)
    
    # Также экспортируем все гены в виде массива для удобного сравнения
    print()
    print("// === Golden values для тестов ===")
    print()
    
    # Parent A первые 5 генов
    print("// Parent A first 5 genes:")
    for i, key in enumerate(GENOME_KEYS[:5]):
        print(f"constexpr double PARENT_A_{key.upper()} = {parent_a[key]:.17f};")
    print()
    
    # Parent B первые 5 генов
    print("// Parent B first 5 genes:")
    for i, key in enumerate(GENOME_KEYS[:5]):
        print(f"constexpr double PARENT_B_{key.upper()} = {parent_b[key]:.17f};")
    print()
    
    # Child после crossover первые 5 генов
    print("// Child after crossover first 5 genes:")
    for i, key in enumerate(GENOME_KEYS[:5]):
        print(f"constexpr double CHILD_CROSSOVER_{key.upper()} = {child_after_crossover[key]:.17f};")
    print()
    
    # Child после mutation первые 5 генов
    print("// Child after mutation first 5 genes:")
    for i, key in enumerate(GENOME_KEYS[:5]):
        print(f"constexpr double CHILD_MUTATION_{key.upper()} = {child_after_mutation[key]:.17f};")
    print()
    
    # Similarity test
    print("// === Genome similarity test ===")
    from alife.genome import genome_similarity
    
    # Создаём два одинаковых генома
    rng_same1 = RNG(999)
    g1 = Genome(rng=rng_same1)
    g1.tag = 3
    g1.n_hidden = 200
    
    rng_same2 = RNG(999)
    g2 = Genome(rng=rng_same2)
    g2.tag = 3
    g2.n_hidden = 200
    
    sim_same = genome_similarity(g1, g2)
    print(f"// Similarity of identical genomes (seed=999): {sim_same:.17f}")
    print(f"constexpr double SIMILARITY_IDENTICAL = {sim_same:.17f};")
    print()
    
    # Создаём два разных генома
    rng_diff1 = RNG(100)
    g3 = Genome(rng=rng_diff1)
    g3.tag = 0
    g3.n_hidden = 100
    
    rng_diff2 = RNG(200)
    g4 = Genome(rng=rng_diff2)
    g4.tag = 7
    g4.n_hidden = 300
    
    sim_diff = genome_similarity(g3, g4)
    print(f"// Similarity of different genomes (seeds 100, 200): {sim_diff:.17f}")
    print(f"constexpr double SIMILARITY_DIFFERENT = {sim_diff:.17f};")
    print()
    
    # Проверка bounds после мутации
    print("// === Bounds check after multiple mutations ===")
    rng_test = RNG(777)
    g_test = Genome(rng=rng_test)
    for _ in range(100):
        g_test.mutate(rng=RNG(_))
    
    print("// After 100 mutations with varying seeds, all genes should be within bounds")
    for key in GENOME_KEYS:
        lo, hi = BOUNDS[key]
        value = g_test[key]
        in_bounds = lo <= value <= hi
        status = "OK" if in_bounds else "FAIL"
        print(f"// {key}: {value:.6f} in [{lo}, {hi}] - {status}")


if __name__ == "__main__":
    main()
