#!/usr/bin/env python3
"""
export_brain_golden.py - Экспорт golden-данных для C++ тестов Brain

Выводит:
- начальные веса или выбранные значения;
- output rates после N шагов;
- финальные веса или выбранные значения.
"""

import sys
import json
import numpy as np

# Добавляем путь к модулям
sys.path.insert(0, '/workspace')

from alife.config import INPUT_SIZE, OUTPUT_SIZE, N_HIDDEN, SYNAPTIC_SCALE, clamp
from alife.brain import Brain


def create_default_genome():
    """Создать геном с параметрами по умолчанию."""
    return {
        "conn_prob": 0.1,
        "weight_scale": 0.5,
        "membrane_decay": 0.85,
        "threshold": 1.0,
        "stdp_rate": 0.01,
        "weight_max": 2.0,
        "lamarckian_weight": 0.0,
    }


def export_golden(seed=42, n_steps=10, n_hidden=64):
    """Экспортировать golden-данные для заданного seed."""
    
    # Установка seed для воспроизводимости
    np.random.seed(seed)
    
    # Создание генома
    genome = create_default_genome()
    
    # Создание мозга
    brain = Brain(genome, n_hidden=n_hidden)
    
    # Сбор данных
    data = {
        "seed": seed,
        "n_hidden": n_hidden,
        "n_in": INPUT_SIZE,
        "n_out": OUTPUT_SIZE,
        "synaptic_scale": SYNAPTIC_SCALE,
        
        # Начальные параметры
        "initial_params": {
            "decay_base": brain.decay_base,
            "threshold_base": brain.threshold_base,
            "stdp_rate": brain.stdp_rate,
            "max_w": brain.max_w,
        },
        
        # Начальные веса (выборочные значения для компактности)
        "initial_weights_sample": {
            "W_0_1": float(brain.W[0, 1]),
            "W_1_0": float(brain.W[1, 0]),
            "W_10_20": float(brain.W[10, 20]),
            "W_50_60": float(brain.W[50, 60]) if n_hidden > 40 else 0.0,
        },
        
        # Маска связей (количество активных связей)
        "mask_connections": int(np.sum(brain.mask)),
        
        # Выходы после N шагов
        "outputs": [],
        
        # Финальные веса (выборочные значения)
        "final_weights_sample": {},
        
        # Финальные параметры
        "final_params": {},
    }
    
    # Запуск шагов
    sensors = [0.5] * INPUT_SIZE
    mod = {"dopamine": 0.5, "plasticity": 0.5}
    
    for i in range(n_steps):
        # Разные сенсоры на каждом шаге
        sensors = [(i % 10) / 10.0] * INPUT_SIZE
        output = brain.step(sensors, mod)
        data["outputs"].append([float(x) for x in output])
    
    # Финальные веса
    data["final_weights_sample"] = {
        "W_0_1": float(brain.W[0, 1]),
        "W_1_0": float(brain.W[1, 0]),
        "W_10_20": float(brain.W[10, 20]),
        "W_50_60": float(brain.W[50, 60]) if n_hidden > 40 else 0.0,
    }
    
    # Финальные параметры E trace (если есть)
    if brain.E is not None:
        data["final_params"]["E_trace_count"] = int(np.sum(np.abs(brain.E) > 1e-10))
    
    return data


def export_parent_inheritance_test(seed_parent=100, seed_child=200, n_hidden=64):
    """Тест наследования родительских весов."""
    
    np.random.seed(seed_parent)
    genome_parent = create_default_genome()
    parent = Brain(genome_parent, n_hidden=n_hidden)
    
    # Сохранение весов родителя
    parent_weights = parent.W.copy()
    
    # Создание потомка с lamarckian_weight = 0.5
    np.random.seed(seed_child)
    genome_child = create_default_genome()
    genome_child["lamarckian_weight"] = 0.5
    
    # Создаём child с parent_weights
    child = Brain(genome_child, n_hidden=n_hidden, parent_weights=parent_weights)
    
    data = {
        "seed_parent": seed_parent,
        "seed_child": seed_child,
        "n_hidden": n_hidden,
        "lamarckian_weight": 0.5,
        
        # Выборочные веса родителя
        "parent_weights_sample": {
            "W_0_1": float(parent_weights[0, 1]),
            "W_1_0": float(parent_weights[1, 0]),
            "W_10_20": float(parent_weights[10, 20]),
        },
        
        # Выборочные веса ребёнка
        "child_weights_sample": {
            "W_0_1": float(child.W[0, 1]),
            "W_1_0": float(child.W[1, 0]),
            "W_10_20": float(child.W[10, 20]),
        },
    }
    
    return data


def main():
    print("Exporting Brain golden data...")
    
    # Основной тест
    golden_data = export_golden(seed=42, n_steps=10, n_hidden=64)
    
    # Тест наследования
    inheritance_data = export_parent_inheritance_test(seed_parent=100, seed_child=200, n_hidden=64)
    
    # Объединение данных
    full_data = {
        "golden_test": golden_data,
        "inheritance_test": inheritance_data,
    }
    
    # Вывод JSON
    output = json.dumps(full_data, indent=2)
    print(output)
    
    # Сохранение в файл
    with open("/workspace/cpp/tests/brain_golden.json", "w") as f:
        f.write(output)
    
    print("\nGolden data saved to /workspace/cpp/tests/brain_golden.json")


if __name__ == "__main__":
    main()
