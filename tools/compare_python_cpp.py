#!/usr/bin/env python3
"""
Сравнение результатов Python и C++ симуляций ALife MVP.

Использование:
    python tools/compare_python_cpp.py out_py.json out_cpp.json [--pos-tol 1e-3] [--value-tol 1e-3]
"""

import argparse
import json
import sys


def load_json(path):
    """Загрузка JSON файла."""
    with open(path, 'r') as f:
        return json.load(f)


def compare_values(py_val, cpp_val, tol, name):
    """Сравнение двух значений с допуском."""
    if py_val is None and cpp_val is None:
        return True, None
    
    try:
        py_f = float(py_val)
        cpp_f = float(cpp_val)
    except (TypeError, ValueError):
        if py_val == cpp_val:
            return True, None
        return False, f"{name}: {py_val} != {cpp_val}"
    
    diff = abs(py_f - cpp_f)
    max_val = max(abs(py_f), abs(cpp_f), 1e-10)
    rel_diff = diff / max_val
    
    if diff <= tol or rel_diff <= tol:
        return True, None
    return False, f"{name}: {py_f} vs {cpp_f} (diff={diff:.6e}, rel={rel_diff:.6e})"


def compare_positions(py_agents, cpp_agents, pos_tol):
    """Сравнение позиций агентов с допуском."""
    errors = []
    
    # Создаем словари по ID для сопоставления
    py_by_id = {a['id']: a for a in py_agents}
    cpp_by_id = {a['id']: a for a in cpp_agents}
    
    # Проверяем совпадение ID
    py_ids = set(py_by_id.keys())
    cpp_ids = set(cpp_by_id.keys())
    
    if py_ids != cpp_ids:
        missing_in_cpp = py_ids - cpp_ids
        missing_in_py = cpp_ids - py_ids
        if missing_in_cpp:
            errors.append(f"Агенты только в Python: {sorted(missing_in_cpp)}")
        if missing_in_py:
            errors.append(f"Агенты только в C++: {sorted(missing_in_py)}")
        return errors
    
    # Сравниваем позиции
    for agent_id in sorted(py_ids):
        py_agent = py_by_id[agent_id]
        cpp_agent = cpp_by_id[agent_id]
        
        # Получаем позиции (поддержка разных форматов)
        # Python формат: x, y отдельно
        # C++ формат: pos: [x, y]
        py_x = py_agent.get('x')
        py_y = py_agent.get('y')
        
        cpp_pos = cpp_agent.get('pos', [])
        cpp_x = cpp_pos[0] if len(cpp_pos) > 0 else None
        cpp_y = cpp_pos[1] if len(cpp_pos) > 1 else None
        
        ok_x, err_x = compare_values(py_x, cpp_x, pos_tol, f"Agent {agent_id} X")
        if not ok_x:
            errors.append(err_x)
        
        ok_y, err_y = compare_values(py_y, cpp_y, pos_tol, f"Agent {agent_id} Y")
        if not ok_y:
            errors.append(err_y)
    
    return errors


def compare_scalar_values(py_data, cpp_data, value_tol):
    """Сравнение скалярных значений."""
    errors = []
    
    # Итоговое число агентов
    py_count = py_data.get('agent_count')
    cpp_agents = cpp_data.get('agents', [])
    cpp_count = len(cpp_agents)
    ok, err = compare_values(py_count, cpp_count, value_tol, "agent_count")
    if not ok:
        errors.append(err)
    
    # Births
    py_births = py_data.get('births')
    cpp_births = cpp_data.get('births', 0)
    ok, err = compare_values(py_births, cpp_births, value_tol, "births")
    if not ok:
        errors.append(err)
    
    # Deaths
    py_deaths = py_data.get('deaths')
    cpp_deaths = cpp_data.get('deaths', 0)
    ok, err = compare_values(py_deaths, cpp_deaths, value_tol, "deaths")
    if not ok:
        errors.append(err)
    
    # Среднее поколение
    py_avg_gen = py_data.get('avg_generation')
    if cpp_agents:
        cpp_avg_gen = sum(a.get('generation', 0) for a in cpp_agents) / len(cpp_agents)
    else:
        cpp_avg_gen = 0.0
    ok, err = compare_values(py_avg_gen, cpp_avg_gen, value_tol, "avg_generation")
    if not ok:
        errors.append(err)
    
    # Число еды
    py_food = py_data.get('food_count')
    cpp_foods = cpp_data.get('foods', [])
    # C++ формат: foods - список словарей с eaten флагом
    cpp_food = len([f for f in cpp_foods if not f.get('eaten', False)])
    ok, err = compare_values(py_food, cpp_food, value_tol, "food_count")
    if not ok:
        errors.append(err)
    
    return errors


def compare_agent_properties(py_agents, cpp_agents, value_tol):
    """Сравнение свойств агентов (энергия, гормоны, depression, breakdown)."""
    errors = []
    
    py_by_id = {a['id']: a for a in py_agents}
    cpp_by_id = {a['id']: a for a in cpp_agents}
    
    common_ids = set(py_by_id.keys()) & set(cpp_by_id.keys())
    
    for agent_id in sorted(common_ids):
        py_agent = py_by_id[agent_id]
        cpp_agent = cpp_by_id[agent_id]
        
        # Энергия
        py_energy = py_agent.get('energy')
        cpp_energy = cpp_agent.get('energy')
        ok, err = compare_values(py_energy, cpp_energy, value_tol, f"Agent {agent_id} energy")
        if not ok:
            errors.append(err)
        
        # Гормоны (Python имеет гормоны, C++ может не иметь)
        py_hormones = py_agent.get('hormones', {})
        cpp_hormones = cpp_agent.get('hormones', {})
        
        for hormone in ['D', 'S', 'O', 'C', 'T']:
            py_h = py_hormones.get(hormone)
            cpp_h = cpp_hormones.get(hormone)
            # Сравниваем только если гормон есть в обоих файлах
            if py_h is not None and cpp_h is not None:
                ok, err = compare_values(py_h, cpp_h, value_tol, f"Agent {agent_id} hormone {hormone}")
                if not ok:
                    errors.append(err)
        
        # Depression (сравниваем только если есть в обоих файлах)
        py_depression = py_agent.get('depression')
        cpp_depression = cpp_agent.get('depression')
        if py_depression is not None and cpp_depression is not None:
            ok, err = compare_values(py_depression, cpp_depression, value_tol, f"Agent {agent_id} depression")
            if not ok:
                errors.append(err)
        
        # Breakdown (сравниваем только если есть в обоих файлах)
        py_breakdown = py_agent.get('breakdown')
        cpp_breakdown = cpp_agent.get('breakdown')
        if py_breakdown is not None and cpp_breakdown is not None:
            ok, err = compare_values(py_breakdown, cpp_breakdown, value_tol, f"Agent {agent_id} breakdown")
            if not ok:
                errors.append(err)
    
    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Сравнение результатов Python и C++ симуляций ALife MVP"
    )
    parser.add_argument("py_output", help="JSON файл с результатами Python симуляции")
    parser.add_argument("cpp_output", help="JSON файл с результатами C++ симуляции")
    parser.add_argument(
        "--pos-tol", 
        type=float, 
        default=1e-3,
        help="Допуск для сравнения позиций (по умолчанию: 1e-3)"
    )
    parser.add_argument(
        "--value-tol", 
        type=float, 
        default=1e-3,
        help="Допуск для сравнения значений (по умолчанию: 1e-3)"
    )
    
    args = parser.parse_args()
    
    # Загрузка данных
    try:
        py_data = load_json(args.py_output)
    except Exception as e:
        print(f"FAIL: Ошибка загрузки Python файла: {e}")
        sys.exit(1)
    
    try:
        cpp_data = load_json(args.cpp_output)
    except Exception as e:
        print(f"FAIL: Ошибка загрузки C++ файла: {e}")
        sys.exit(1)
    
    all_errors = []
    
    # Сравнение скалярных значений
    scalar_errors = compare_scalar_values(py_data, cpp_data, args.value_tol)
    all_errors.extend(scalar_errors)
    
    # Получение списков агентов
    py_agents = py_data.get('agents', [])
    cpp_agents = cpp_data.get('agents', [])
    
    # Сравнение позиций
    pos_errors = compare_positions(py_agents, cpp_agents, args.pos_tol)
    all_errors.extend(pos_errors)
    
    # Сравнение свойств агентов
    prop_errors = compare_agent_properties(py_agents, cpp_agents, args.value_tol)
    all_errors.extend(prop_errors)
    
    # Вывод результатов
    if all_errors:
        print("FAIL")
        print(f"\nНайдено расхождений: {len(all_errors)}")
        for err in all_errors[:20]:  # Показываем первые 20 ошибок
            print(f"  - {err}")
        if len(all_errors) > 20:
            print(f"  ... и ещё {len(all_errors) - 20} расхождений")
        sys.exit(1)
    else:
        print("PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
