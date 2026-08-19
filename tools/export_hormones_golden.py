#!/usr/bin/env python3
"""
Экспорт эталонных значений Hormones для вставки в C++ тесты.

Генерирует начальное состояние гормонов, последовательность событий
и финальное состояние после update() с фиксированными seed для обеспечения детерминированности.
"""

import sys
import os
import json

# Добавляем путь к модулю alife
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from alife.hormones import Hormones


def format_double(value, precision=17):
    """Форматировать double значение для C++ кода."""
    return f"{value:.{precision}f}"


def export_genome(name, genes, indent=4):
    """Экспортировать геном в формате C++."""
    print(f"// {name}")
    print(f"std::map<std::string, double> {name}_genes = {{")
    for key in sorted(genes.keys()):
        value = genes[key]
        print(f'    {{"{key}", {value:.17f}}},')
    print("};")
    print()


def main():
    """Основная функция экспорта эталонных значений."""
    print("// Эталонные значения Hormones")
    print("// Сгенерировано с помощью tools/export_hormones_golden.py")
    print("// Для использования в C++ тестах")
    print()
    
    # Создаём тестовый геном с фиксированными значениями
    genes = {
        'mutation_rate': 0.05,
        'conn_prob': 0.1,
        'weight_scale': 0.5,
        'weight_max': 1.5,
        'membrane_decay': 0.9,
        'threshold': 1.0,
        'stdp_rate': 0.01,
        'plasticity_gain': 1.0,
        'dopamine_base': 0.5,
        'dopamine_reactivity': 1.0,
        'dopamine_decay': 0.05,
        'dopamine_sensitivity': 1.0,
        'serotonin_base': 0.5,
        'serotonin_decay': 0.05,
        'serotonin_sensitivity': 1.0,
        'oxytocin_base': 0.4,
        'oxytocin_gain': 1.0,
        'oxytocin_decay': 0.05,
        'oxytocin_sensitivity': 1.0,
        'cortisol_base': 0.2,
        'cortisol_reactivity': 1.0,
        'cortisol_decay': 0.05,
        'cortisol_sensitivity': 1.0,
        'testosterone_base': 0.5,
        'testosterone_reactivity': 1.0,
        'testosterone_decay': 0.05,
        'testosterone_sensitivity': 1.0,
        'aggression_gain': 1.0,
        'social_gain': 1.0,
        'lamarckian_weight': 0.5,
        'metabolism': 0.05,
        'brain_arch_mutability': 0.05,
        'stress_resilience': 0.5,
        'social_temperament': 0.5,
    }
    
    class MockGenome:
        def __init__(self, genes):
            self.genes = genes
        def __getitem__(self, key):
            return self.genes[key]
        def get(self, key, default=None):
            return self.genes.get(key, default)
    
    genome = MockGenome(genes)
    hormones = Hormones(genome)
    
    print("// === Начальное состояние гормонов ===")
    print(f"constexpr double INITIAL_D = {format_double(hormones.D)};")
    print(f"constexpr double INITIAL_S = {format_double(hormones.S)};")
    print(f"constexpr double INITIAL_O = {format_double(hormones.O)};")
    print(f"constexpr double INITIAL_C = {format_double(hormones.C)};")
    print(f"constexpr double INITIAL_T = {format_double(hormones.T)};")
    print(f"constexpr double INITIAL_allostatic = {format_double(hormones.allostatic)};")
    print(f"constexpr double INITIAL_depression = {format_double(hormones.depression)};")
    print(f"constexpr double INITIAL_breakdown = {format_double(hormones.breakdown)};")
    print(f"constexpr double INITIAL_paranoia = {format_double(hormones.paranoia)};")
    print(f"constexpr double INITIAL_trust = {format_double(hormones.trust)};")
    print(f"constexpr double INITIAL_delayed_punishment = {format_double(hormones.delayed_punishment)};")
    print()
    
    print("// === Параметры распада и чувствительности ===")
    print(f"constexpr double D_decay = {format_double(hormones.D_decay)};")
    print(f"constexpr double S_decay = {format_double(hormones.S_decay)};")
    print(f"constexpr double O_decay = {format_double(hormones.O_decay)};")
    print(f"constexpr double C_decay = {format_double(hormones.C_decay)};")
    print(f"constexpr double T_decay = {format_double(hormones.T_decay)};")
    print(f"constexpr double S_sensitivity = {format_double(hormones.S_sensitivity)};")
    print(f"constexpr double O_sensitivity = {format_double(hormones.O_sensitivity)};")
    print(f"constexpr double C_sensitivity = {format_double(hormones.C_sensitivity)};")
    print(f"constexpr double T_sensitivity = {format_double(hormones.T_sensitivity)};")
    print(f"constexpr double D_sensitivity = {format_double(hormones.D_sensitivity)};")
    print(f"constexpr double stress_resilience = {format_double(hormones.stress_resilience)};")
    print(f"constexpr double social_temperament = {format_double(hormones.social_temperament)};")
    print()
    
    # Фиксированная последовательность событий
    events_sequence = [
        {"dt": 1.0, "reward": 0.5, "punishment": 0.0, "social": 0.3, "kin": 0.0, "conflict": 0.0, "dominance": 0.0, "hunger": 0.2, "injury": 0.0, "fear": 0.0},
        {"dt": 1.0, "reward": 0.0, "punishment": 0.3, "social": 0.0, "kin": 0.0, "conflict": 0.0, "dominance": 0.0, "hunger": 0.3, "injury": 0.0, "fear": 0.1},
        {"dt": 1.0, "reward": 0.8, "punishment": 0.0, "social": 0.5, "kin": 0.2, "conflict": 0.0, "dominance": 0.0, "hunger": 0.1, "injury": 0.0, "fear": 0.0},
        {"dt": 1.0, "reward": 0.0, "punishment": 0.0, "social": 0.0, "kin": 0.0, "conflict": 0.4, "dominance": 0.2, "hunger": 0.4, "injury": 0.0, "fear": 0.0},
        {"dt": 1.0, "reward": 0.0, "punishment": 0.6, "social": 0.0, "kin": 0.0, "conflict": 0.0, "dominance": 0.0, "hunger": 0.5, "injury": 0.3, "fear": 0.4},
        {"dt": 1.0, "reward": 0.3, "punishment": 0.0, "social": 0.8, "kin": 0.5, "conflict": 0.0, "dominance": 0.0, "hunger": 0.2, "injury": 0.0, "fear": 0.0},
        {"dt": 1.0, "reward": 0.0, "punishment": 0.0, "social": 0.0, "kin": 0.0, "conflict": 0.0, "dominance": 0.5, "hunger": 0.3, "injury": 0.0, "fear": 0.0},
        {"dt": 1.0, "reward": 0.0, "punishment": 0.8, "social": 0.0, "kin": 0.0, "conflict": 0.0, "dominance": 0.0, "hunger": 0.6, "injury": 0.0, "fear": 0.5},
        {"dt": 1.0, "reward": 0.5, "punishment": 0.0, "social": 0.4, "kin": 0.0, "conflict": 0.0, "dominance": 0.0, "hunger": 0.1, "injury": 0.0, "fear": 0.0},
        {"dt": 1.0, "reward": 0.0, "punishment": 0.0, "social": 0.0, "kin": 0.0, "conflict": 0.2, "dominance": 0.0, "hunger": 0.4, "injury": 0.0, "fear": 0.2},
    ]
    
    print("// === Последовательность событий (10 шагов) ===")
    print("struct Event { double dt; double reward; double punishment; double social; double kin; double conflict; double dominance; double hunger; double injury; double fear; };")
    print("const std::vector<Event> test_events = {")
    for i, ev in enumerate(events_sequence):
        print(f"    {{{ev['dt']}, {ev['reward']}, {ev['punishment']}, {ev['social']}, {ev['kin']}, {ev['conflict']}, {ev['dominance']}, {ev['hunger']}, {ev['injury']}, {ev['fear']}}},  // step {i}")
    print("};")
    print()
    
    # Применяем события
    for ev in events_sequence:
        hormones.update(ev["dt"], ev, genome)
    
    print("// === Финальное состояние после 10 обновлений ===")
    print(f"constexpr double FINAL_D = {format_double(hormones.D)};")
    print(f"constexpr double FINAL_S = {format_double(hormones.S)};")
    print(f"constexpr double FINAL_O = {format_double(hormones.O)};")
    print(f"constexpr double FINAL_C = {format_double(hormones.C)};")
    print(f"constexpr double FINAL_T = {format_double(hormones.T)};")
    print(f"constexpr double FINAL_allostatic = {format_double(hormones.allostatic)};")
    print(f"constexpr double FINAL_depression = {format_double(hormones.depression)};")
    print(f"constexpr double FINAL_breakdown = {format_double(hormones.breakdown)};")
    print(f"constexpr double FINAL_paranoia = {format_double(hormones.paranoia)};")
    print(f"constexpr double FINAL_trust = {format_double(hormones.trust)};")
    print(f"constexpr double FINAL_delayed_punishment = {format_double(hormones.delayed_punishment)};")
    print()
    
    # Вычисляем эффекты
    effects = hormones.effects(genome, hunger=0.3)
    print("// === Эффекты (effects) при hunger=0.3 ===")
    print(f"constexpr double EFFECTS_arousal = {format_double(effects['arousal'])};")
    print(f"constexpr double EFFECTS_plasticity = {format_double(effects['plasticity'])};")
    print(f"constexpr double EFFECTS_aggression = {format_double(effects['aggression'])};")
    print(f"constexpr double EFFECTS_sociality = {format_double(effects['sociality'])};")
    print(f"constexpr double EFFECTS_dopamine_signal = {format_double(effects['dopamine_signal'])};")
    print(f"constexpr double EFFECTS_depression = {format_double(effects['depression'])};")
    print(f"constexpr double EFFECTS_breakdown = {format_double(effects['breakdown'])};")
    print(f"constexpr double EFFECTS_paranoia = {format_double(effects['paranoia'])};")
    print(f"constexpr double EFFECTS_trust = {format_double(effects['trust'])};")
    print(f"constexpr double EFFECTS_allostatic = {format_double(effects['allostatic'])};")
    print()
    
    # Mood
    mood = hormones.get_mood()
    print(f"// === Настроение ===")
    print(f'const std::string MOOD = "{mood}";')
    print()
    
    # Проверка границ
    print("// === Проверка границ ===")
    all_in_bounds = True
    hormone_values = [
        ("D", hormones.D),
        ("S", hormones.S),
        ("O", hormones.O),
        ("C", hormones.C),
        ("T", hormones.T),
        ("allostatic", hormones.allostatic),
        ("depression", hormones.depression),
        ("breakdown", hormones.breakdown),
        ("paranoia", hormones.paranoia),
        ("trust", hormones.trust),
    ]
    for name, value in hormone_values:
        in_bounds = 0.0 <= value <= 2.0 if name in ["D", "S", "O", "C", "T"] else (0.0 <= value <= 1.0)
        status = "OK" if in_bounds else "FAIL"
        if not in_bounds:
            all_in_bounds = False
        print(f"// {name}: {value:.6f} - {status}")
    print()
    
    # Тест на отсутствие NaN после многих обновлений
    print("// === Тест на отсутствие NaN после 1000 обновлений ===")
    hormones_test = Hormones(genome)
    has_nan = False
    for i in range(1000):
        ev = events_sequence[i % len(events_sequence)]
        hormones_test.update(ev["dt"], ev, genome)
        for attr in ["D", "S", "O", "C", "T", "allostatic", "depression", "breakdown", "paranoia", "trust"]:
            val = getattr(hormones_test, attr)
            if val != val:  # NaN check
                has_nan = True
                print(f"// NaN detected at step {i} in {attr}")
                break
        if has_nan:
            break
    
    if not has_nan:
        print("// No NaN detected after 1000 updates - OK")
    print()
    
    # JSON вывод для удобного парсинга
    print("// === JSON output для парсинга ===")
    golden_data = {
        "initial": {
            "D": hormones.D, "S": hormones.S, "O": hormones.O, "C": hormones.C, "T": hormones.T,
            "allostatic": hormones.allostatic, "depression": hormones.depression,
            "breakdown": hormones.breakdown, "paranoia": hormones.paranoia,
            "trust": hormones.trust, "delayed_punishment": hormones.delayed_punishment
        },
        "final": {
            "D": hormones.D, "S": hormones.S, "O": hormones.O, "C": hormones.C, "T": hormones.T,
            "allostatic": hormones.allostatic, "depression": hormones.depression,
            "breakdown": hormones.breakdown, "paranoia": hormones.paranoia,
            "trust": hormones.trust, "delayed_punishment": hormones.delayed_punishment
        },
        "effects": effects,
        "mood": mood,
    }
    print(json.dumps(golden_data, indent=2))


if __name__ == "__main__":
    main()
