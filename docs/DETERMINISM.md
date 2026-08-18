# Детерминизм симуляции ALife MVP

## Описание

Симуляция ALife MVP является **детерминированной**: при использовании одинакового начального seed (`--seed`) все аспекты симуляции воспроизводятся бит-в-бит. Это достигается за счёт:

1. Использования собственного генератора случайных чисел (`alife.rng.RNG`), основанного на `numpy.random.Generator` с PCG64.
2. Отсутствия любых других источников случайности (глобальный `random`, `np.random` без явного указания RNG).
3. Детерминированного порядка обновления агентов (сортировка по ID).
4. Детерминированной инициализации мира, агентов, еды и геномов.

## Гарантия детерминизма

**Два запуска с одинаковым seed дают идентичные результаты:**
- Одинаковое количество агентов в каждый момент времени
- Одинаковые позиции, углы, энергию каждого агента
- Одинаковые значения гормонов (D, S, O, C, T)
- Одинаковые показатели depression и breakdown
- Одинаковое количество рождений и смертей

## Автоматическая проверка

Для автоматической проверки детерминизма используйте тест:

```bash
cd python
python -m pytest tests/test_determinism.py -v
```

Или запустите напрямую:

```bash
cd python
python tests/test_determinism.py
```

Тест выполняет:
1. Два запуска headless-симуляции с одинаковым seed.
2. Сравнение всех ключевых метрик (агент count, births, deaths, позиции, гормоны и т.д.).
3. Проверку отсутствия NaN в результатах.

## Ручная проверка детерминизма

### Шаг 1: Запуск двух симуляций с одинаковым seed

```bash
cd python

# Первый запуск
python main.py --headless --seed 42 --ticks 1000 --out out_py_1.json

# Второй запуск
python main.py --headless --seed 42 --ticks 1000 --out out_py_2.json
```

### Шаг 2: Сравнение результатов

#### Вариант A: Использование Python-скрипта

Создайте скрипт `compare_runs.py`:

```python
import json
import numpy as np

def load_result(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def compare(r1, r2):
    # Сравниваем основные метрики
    for key in ['seed', 'ticks', 'agent_count', 'births', 'deaths', 'food_count']:
        if r1[key] != r2[key]:
            print(f"РАЗЛИЧИЕ: {key}: {r1[key]} vs {r2[key]}")
            return False
    
    # Сравниваем avg_generation
    if not np.isclose(r1['avg_generation'], r2['avg_generation'], rtol=1e-9):
        print(f"РАЗЛИЧИЕ: avg_generation: {r1['avg_generation']} vs {r2['avg_generation']}")
        return False
    
    # Сравниваем агентов
    agents1 = sorted(r1['agents'], key=lambda a: a['id'])
    agents2 = sorted(r2['agents'], key=lambda a: a['id'])
    
    if len(agents1) != len(agents2):
        print(f"РАЗЛИЧИЕ: количество агентов: {len(agents1)} vs {len(agents2)}")
        return False
    
    for i, (a1, a2) in enumerate(zip(agents1, agents2)):
        for key in ['id', 'generation', 'energy', 'depression', 'breakdown']:
            if isinstance(a1[key], float):
                if not np.isclose(a1[key], a2[key], rtol=1e-9):
                    print(f"РАЗЛИЧИЕ: агент[{i}].{key}: {a1[key]} vs {a2[key]}")
                    return False
            elif a1[key] != a2[key]:
                print(f"РАЗЛИЧИЕ: агент[{i}].{key}: {a1[key]} vs {a2[key]}")
                return False
        
        # Позиция
        if not np.isclose(a1['x'], a2['x'], rtol=1e-9):
            print(f"РАЗЛИЧИЕ: агент[{i}].x: {a1['x']} vs {a2['x']}")
            return False
        if not np.isclose(a1['y'], a2['y'], rtol=1e-9):
            print(f"РАЗЛИЧИЕ: агент[{i}].y: {a1['y']} vs {a2['y']}")
            return False
        
        # Гормоны
        for h in ['D', 'S', 'O', 'C', 'T']:
            if not np.isclose(a1['hormones'][h], a2['hormones'][h], rtol=1e-9):
                print(f"РАЗЛИЧИЕ: агент[{i}].hormones.{h}: {a1['hormones'][h]} vs {a2['hormones'][h]}")
                return False
    
    return True

if __name__ == '__main__':
    r1 = load_result('out_py_1.json')
    r2 = load_result('out_py_2.json')
    
    if compare(r1, r2):
        print("✓ Результаты идентичны — детерминизм подтверждён")
    else:
        print("✗ Результаты различаются — нарушение детерминизма!")
```

Запустите:

```bash
python compare_runs.py
```

#### Вариант B: Использование diff (для быстрой проверки)

```bash
# Нормализуем JSON (убираем форматирование) для сравнения
python -c "import json; print(json.dumps(json.load(open('out_py_1.json')), sort_keys=True))" > norm1.json
python -c "import json; print(json.dumps(json.load(open('out_py_2.json')), sort_keys=True))" > norm2.json

# Сравниваем
diff norm1.json norm2.json && echo "✓ Файлы идентичны" || echo "✗ Файлы различаются"
```

#### Вариант C: Использование jq (если установлен)

```bash
jq --sort-keys '.' out_py_1.json > norm1.json
jq --sort-keys '.' out_py_2.json > norm2.json
diff norm1.json norm2.json && echo "✓ Детерминизм подтверждён"
```

### Шаг 3: Проверка отсутствия NaN

NaN может возникнуть при численных ошибках. Для проверки:

```python
import json
import numpy as np

def check_nan(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    
    has_nan = False
    for agent in data.get('agents', []):
        if np.isnan(agent.get('x', 0)):
            print(f"NaN в агент[{agent['id']}].x")
            has_nan = True
        if np.isnan(agent.get('y', 0)):
            print(f"NaN в агент[{agent['id']}].y")
            has_nan = True
        if np.isnan(agent.get('energy', 0)):
            print(f"NaN в агент[{agent['id']}].energy")
            has_nan = True
        for h in ['D', 'S', 'O', 'C', 'T']:
            if np.isnan(agent['hormones'].get(h, 0)):
                print(f"NaN в агент[{agent['id']}].hormones.{h}")
                has_nan = True
        if np.isnan(agent.get('depression', 0)):
            print(f"NaN в агент[{agent['id']}].depression")
            has_nan = True
        if np.isnan(agent.get('breakdown', 0)):
            print(f"NaN в агент[{agent['id']}].breakdown")
            has_nan = True
    
    if not has_nan:
        print("✓ NaN не обнаружен")
    return not has_nan

check_nan('out_py_1.json')
```

## Пример ожидаемого вывода

При успешной проверке детерминизма:

```
$ python main.py --headless --seed 42 --ticks 1000 --out out_py_1.json
=== Headless Simulation Results ===
Ticks completed: 1000
Average tick time: 17.732 ms
Final agent count: 25
Average generation: 0.04
Total births: 1
Total deaths: 0
Total simulation time: 18.31 s
Results written to: out_py_1.json

$ python main.py --headless --seed 42 --ticks 1000 --out out_py_2.json
=== Headless Simulation Results ===
Ticks completed: 1000
Average tick time: 17.689 ms
Final agent count: 25
Average generation: 0.04
Total births: 1
Total deaths: 0
Total simulation time: 18.27 s
Results written to: out_py_2.json

$ python compare_runs.py
✓ Результаты идентичны — детерминизм подтверждён
```

**Обратите внимание:** `Average tick time` и `Total simulation time` могут отличаться между запусками (зависят от загрузки CPU), но это не влияет на детерминизм самой симуляции.

## Источники недетерминированности (чего избегать)

При модификации кода избегайте:

1. **Глобального `random`** — используйте `alife.rng.RNG`.
2. **`np.random` без явного Generator** — используйте `rng = np.random.default_rng(seed)` и передавайте `rng` явно.
3. **Параллелизма без синхронизации** — порядок выполнения потоков недетерминирован.
4. **Зависимости от системного времени** — не используйте `time.time()` для логики симуляции.
5. **Хеш-таблиц с неупорядоченным обходом** — в Python 3.7+ `dict` упорядочен, но `set` — нет.

## Тесты на детерминизм

В репозитории присутствуют следующие тесты:

| Файл | Описание |
|------|----------|
| `tests/test_determinism.py` | Интеграционный тест headless-симуляции |
| `tests/test_genome_determinism.py` | Детерминизм создания, кроссовера и мутации геномов |
| `tests/test_agent_determinism.py` | Детерминизм поведения агентов |
| `tests/test_world_determinism.py` | Детерминизм мира (спавн еды, обновление агентов) |
| `tests/test_rng.py` | Тесты генератора случайных чисел |

Запуск всех тестов:

```bash
cd python
python -m pytest tests/ -v -k determinism
```

## Troubleshooting

### Результаты различаются

1. Убедитесь, что используется одинаковый `--seed`.
2. Проверьте, что не изменены параметры симуляции (`--agents`, `--food`, `--hidden-neurons`).
3. Убедитесь, что версия кода идентична (нет незакоммиченных изменений).

### Обнаружен NaN

1. Проверьте входные данные (энергия, гормоны) на корректность.
2. Убедитесь, что нет деления на ноль в формулах.
3. Проверьте, что веса мозга инициализированы корректно.

### Разное количество агентов

Это указывает на нарушение детерминизма в логике размножения или смерти. Проверьте:
- Порядок обновления агентов (должен быть по ID).
- Условия размножения и смерти.
- Использование RNG в соответствующих местах.
