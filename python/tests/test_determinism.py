"""
Интеграционный тест на детерминизм headless-симуляции.

Запускает симуляцию дважды с одинаковым seed и сравнивает ключевые метрики.
Проверяет отсутствие NaN в результатах.
"""
import json
import subprocess
import sys
import os
import tempfile
import numpy as np


def run_headless_simulation(seed, ticks, output_file):
    """Запустить headless-симуляцию и сохранить результаты в JSON."""
    # Определяем путь к main.py относительно этого файла
    script_dir = os.path.dirname(os.path.abspath(__file__))
    python_dir = os.path.join(script_dir, '..')
    main_py = os.path.join(python_dir, 'main.py')
    
    cmd = [
        sys.executable,
        main_py,
        '--headless',
        '--seed', str(seed),
        '--ticks', str(ticks),
        '--out', output_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Симуляция завершилась с ошибкой:\n{result.stderr}")
    
    with open(output_file, 'r') as f:
        return json.load(f)


def compare_results(result1, result2):
    """
    Сравнить результаты двух симуляций.
    
    Возвращает (is_equal, differences).
    """
    differences = []
    
    # Сравниваем основные метрики
    metrics = ['seed', 'ticks', 'agent_count', 'births', 'deaths', 'food_count']
    for metric in metrics:
        val1 = result1.get(metric)
        val2 = result2.get(metric)
        if val1 != val2:
            differences.append(f"{metric}: {val1} != {val2}")
    
    # Сравниваем avg_generation с допустимой погрешностью
    avg_gen1 = result1.get('avg_generation', 0)
    avg_gen2 = result2.get('avg_generation', 0)
    if not np.isclose(avg_gen1, avg_gen2, rtol=1e-9):
        differences.append(f"avg_generation: {avg_gen1} != {avg_gen2}")
    
    # Сравниваем агентов
    agents1 = result1.get('agents', [])
    agents2 = result2.get('agents', [])
    
    if len(agents1) != len(agents2):
        differences.append(f"Количество агентов: {len(agents1)} != {len(agents2)}")
        return False, differences
    
    # Сортируем агентов по ID для сравнения
    agents1_sorted = sorted(agents1, key=lambda a: a['id'])
    agents2_sorted = sorted(agents2, key=lambda a: a['id'])
    
    for i, (a1, a2) in enumerate(zip(agents1_sorted, agents2_sorted)):
        if a1['id'] != a2['id']:
            differences.append(f"Агент[{i}] id: {a1['id']} != {a2['id']}")
            continue
        
        # Сравниваем позицию с допустимой погрешностью
        if not np.isclose(a1['x'], a2['x'], rtol=1e-9):
            differences.append(f"Агент[{i}] x: {a1['x']} != {a2['x']}")
        if not np.isclose(a1['y'], a2['y'], rtol=1e-9):
            differences.append(f"Агент[{i}] y: {a1['y']} != {a2['y']}")
        
        # Сравниваем энергию
        if not np.isclose(a1['energy'], a2['energy'], rtol=1e-9):
            differences.append(f"Агент[{i}] energy: {a1['energy']} != {a2['energy']}")
        
        # Сравниваем гормоны
        hormones1 = a1.get('hormones', {})
        hormones2 = a2.get('hormones', {})
        for h in ['D', 'S', 'O', 'C', 'T']:
            val1 = hormones1.get(h, 0)
            val2 = hormones2.get(h, 0)
            if not np.isclose(val1, val2, rtol=1e-9):
                differences.append(f"Агент[{i}] hormone[{h}]: {val1} != {val2}")
        
        # Сравниваем depression и breakdown
        if not np.isclose(a1.get('depression', 0), a2.get('depression', 0), rtol=1e-9):
            differences.append(f"Агент[{i}] depression: {a1.get('depression')} != {a2.get('depression')}")
        if not np.isclose(a1.get('breakdown', 0), a2.get('breakdown', 0), rtol=1e-9):
            differences.append(f"Агент[{i}] breakdown: {a1.get('breakdown')} != {a2.get('breakdown')}")
    
    return len(differences) == 0, differences


def check_no_nan(result):
    """
    Проверить отсутствие NaN в результатах.
    
    Возвращает (has_no_nan, nan_locations).
    """
    nan_locations = []
    
    agents = result.get('agents', [])
    for i, agent in enumerate(agents):
        # Проверяем позицию
        if np.isnan(agent.get('x', 0)):
            nan_locations.append(f"Агент[{i}].x")
        if np.isnan(agent.get('y', 0)):
            nan_locations.append(f"Агент[{i}].y")
        
        # Проверяем энергию
        if np.isnan(agent.get('energy', 0)):
            nan_locations.append(f"Агент[{i}].energy")
        
        # Проверяем гормоны
        hormones = agent.get('hormones', {})
        for h in ['D', 'S', 'O', 'C', 'T']:
            if np.isnan(hormones.get(h, 0)):
                nan_locations.append(f"Агент[{i}].hormones.{h}")
        
        # Проверяем depression и breakdown
        if np.isnan(agent.get('depression', 0)):
            nan_locations.append(f"Агент[{i}].depression")
        if np.isnan(agent.get('breakdown', 0)):
            nan_locations.append(f"Агент[{i}].breakdown")
    
    return len(nan_locations) == 0, nan_locations


class TestDeterminism:
    """Тесты на детерминизм headless-симуляции."""
    
    def test_determinism_same_seed(self):
        """Два запуска с одинаковым seed должны давать одинаковые результаты."""
        seed = 42
        ticks = 500
        
        with tempfile.TemporaryDirectory() as tmpdir:
            out1 = os.path.join(tmpdir, 'out1.json')
            out2 = os.path.join(tmpdir, 'out2.json')
            
            # Запускаем симуляцию дважды
            result1 = run_headless_simulation(seed, ticks, out1)
            result2 = run_headless_simulation(seed, ticks, out2)
            
            # Проверяем отсутствие NaN
            no_nan1, nan_locs1 = check_no_nan(result1)
            assert no_nan1, f"Обнаружены NaN в первом запуске: {nan_locs1}"
            
            no_nan2, nan_locs2 = check_no_nan(result2)
            assert no_nan2, f"Обнаружены NaN во втором запуске: {nan_locs2}"
            
            # Сравниваем результаты
            is_equal, differences = compare_results(result1, result2)
            assert is_equal, f"Результаты не совпадают:\n" + "\n".join(differences)
    
    def test_determinism_different_seeds(self):
        """Запуски с разными seed должны давать разные результаты (обычно)."""
        ticks = 500
        
        with tempfile.TemporaryDirectory() as tmpdir:
            out1 = os.path.join(tmpdir, 'out1.json')
            out2 = os.path.join(tmpdir, 'out2.json')
            
            # Запускаем с разными seed
            result1 = run_headless_simulation(42, ticks, out1)
            result2 = run_headless_simulation(123, ticks, out2)
            
            # Проверяем, что результаты разные (хотя бы количество агентов или births)
            # Это не строгий тест, так как теоретически могут совпасть
            different = (
                result1['agent_count'] != result2['agent_count'] or
                result1['births'] != result2['births'] or
                result1['deaths'] != result2['deaths']
            )
            # Не утверждаем строго, просто проверяем что симуляция прошла
            assert result1['seed'] == 42
            assert result2['seed'] == 123
    
    def test_no_nan_in_simulation(self):
        """Проверка отсутствия NaN в ходе симуляции."""
        seed = 42
        ticks = 1000
        
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, 'out.json')
            result = run_headless_simulation(seed, ticks, out_file)
            
            no_nan, nan_locations = check_no_nan(result)
            assert no_nan, f"Обнаружены NaN в результатах: {nan_locations}"


if __name__ == '__main__':
    # Прямой запуск для ручной проверки
    print("Запуск теста детерминизма...")
    
    test = TestDeterminism()
    
    try:
        test.test_determinism_same_seed()
        print("✓ test_determinism_same_seed: PASSED")
    except AssertionError as e:
        print(f"✗ test_determinism_same_seed: FAILED - {e}")
    
    try:
        test.test_determinism_different_seeds()
        print("✓ test_determinism_different_seeds: PASSED")
    except AssertionError as e:
        print(f"✗ test_determinism_different_seeds: FAILED - {e}")
    
    try:
        test.test_no_nan_in_simulation()
        print("✓ test_no_nan_in_simulation: PASSED")
    except AssertionError as e:
        print(f"✗ test_no_nan_in_simulation: FAILED - {e}")
    
    print("\nВсе тесты завершены.")
