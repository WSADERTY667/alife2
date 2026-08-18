#!/usr/bin/env python3
"""
Экспорт эталонных значений RNG для вставки в C++ тесты.

Генерирует первые N значений RNG для заданных seed и выводит их
в формате, удобном для вставки в C++ код.
"""

import sys
import os

# Добавляем путь к модулю alife напрямую, чтобы избежать импорта pygame
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python', 'alife'))

# Импортируем только класс RNG напрямую из файла
import importlib.util
rng_path = os.path.join(os.path.dirname(__file__), '..', 'python', 'alife', 'rng.py')
spec = importlib.util.spec_from_file_location("rng", rng_path)
rng_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rng_module)
RNG = rng_module.RNG


def export_golden_values(seed: int, count: int = 10) -> None:
    """
    Вывести эталонные значения RNG для данного seed.

    Args:
        seed: Начальное значение RNG.
        count: Количество значений для генерации.
    """
    rng = RNG(seed=seed)

    print(f"// Seed: {seed}")
    print(f"const std::uint32_t golden_seed_{seed}[] = {{")

    values = []
    for i in range(count):
        val = rng.next_int()
        values.append(val)

    # Форматируем вывод: по 8 значений на строку
    for i, val in enumerate(values):
        if i % 8 == 0:
            if i > 0:
                print()
            print("    ", end="")
        print(f"{val}", end="")
        if i < len(values) - 1:
            print(", ", end="")

    print()
    print("};")
    print()


def main():
    """Основная функция экспорта эталонных значений."""
    seeds = [42, 123, 2026]
    count = 10  # Количество значений для каждого seed

    print("// Эталонные значения RNG (SplitMix64)")
    print("// Сгенерировано с помощью tools/export_rng_golden.py")
    print()

    for seed in seeds:
        export_golden_values(seed, count)


if __name__ == "__main__":
    main()
