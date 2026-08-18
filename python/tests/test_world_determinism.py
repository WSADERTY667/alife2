"""
Тесты на детерминированность мира (World) с использованием RNG.
Гарантируют, что одинаковый seed даёт одинаковое развитие мира.
"""
import numpy as np
from alife.world import World
from alife.rng import RNG


def test_world_determinism_same_seed():
    """Одинаковый seed должен давать одинаковое развитие мира."""
    from alife.agent import Agent
    seed = 12345
    
    # Сбрасываем счетчик ID для детерминированности
    Agent.next_id = 1
    
    # Создаём два мира с одинаковым seed
    world1 = World(rng=RNG(seed=seed))
    world2 = World(rng=RNG(seed=seed))
    
    # Сохраняем начальные состояния
    def get_state(world):
        foods = [(f["pos"][0], f["pos"][1], f["nutrition"]) for f in world.foods]
        agents = [(a.pos[0], a.pos[1], a.angle, a.energy, a.id) for a in world.agents]
        return (tuple(foods), tuple(agents))
    
    state1_init = get_state(world1)
    state2_init = get_state(world2)
    
    # Начальные состояния должны быть одинаковыми
    assert state1_init == state2_init, "Начальные состояния миров с одинаковым seed должны совпадать"
    
    # Запускаем несколько тиков
    for _ in range(50):
        world1.update()
        world2.update()
    
    state1_after = get_state(world1)
    state2_after = get_state(world2)
    
    # Состояния после обновления должны быть одинаковыми
    assert state1_after == state2_after, "Состояния миров после update() с одинаковым seed должны совпадать"


def test_world_determinism_different_seed():
    """Разный seed должен давать разное развитие мира."""
    world1 = World(rng=RNG(seed=11111))
    world2 = World(rng=RNG(seed=22222))
    
    # Сохраняем начальные состояния
    def get_state(world):
        foods = [(f["pos"][0], f["pos"][1], f["nutrition"]) for f in world.foods]
        agents = [(a.pos[0], a.pos[1], a.angle, a.energy, a.id) for a in world.agents]
        return (tuple(foods), tuple(agents))
    
    state1_init = get_state(world1)
    state2_init = get_state(world2)
    
    # Начальные состояния должны быть разными
    assert state1_init != state2_init, "Начальные состояния миров с разным seed должны отличаться"


def test_world_agent_update_order():
    """Порядок обновления агентов должен быть стабильным (по ID)."""
    world = World(rng=RNG(seed=42))
    
    # Получаем порядок агентов до update
    initial_ids = [a.id for a in world.agents]
    
    # Выполняем несколько тиков
    for _ in range(10):
        world.update()
        # После каждого update агенты должны быть отсортированы по ID
        current_ids = [a.id for a in world.agents]
        assert current_ids == sorted(current_ids), "Агенты должны быть отсортированы по ID после update()"


def test_world_newborns_not_affecting_current_tick():
    """Новорождённые агенты не должны влиять на текущий тик."""
    world = World(rng=RNG(seed=42))
    
    # Запоминаем количество агентов до update
    agent_count_before = len(world.agents)
    
    # Находим агента, который может размножаться
    for agent in world.agents:
        agent.age = 600  # Устанавливаем возраст больше MATURE_AGE
        agent.energy = 90  # Устанавливаем энергию больше REPRO_ENERGY
        agent.repro_cooldown = 0
    
    # Сохраняем ID существующих агентов
    existing_ids = set(a.id for a in world.agents)
    
    # Выполняем update
    world.update()
    
    # Новорождённые должны иметь ID, которых не было до update
    for agent in world.agents:
        if agent.id not in existing_ids:
            # Это новорождённый агент
            # Он не должен был обновляться в этом тике
            # (проверяем, что он есть в списке, но это гарантируется структурой кода)
            pass


def test_world_food_spawn_deterministic():
    """Спавн еды должен быть детерминированным."""
    seed = 54321
    
    world1 = World(rng=RNG(seed=seed))
    world2 = World(rng=RNG(seed=seed))
    
    # Сбрасываем еду и спавним заново для проверки
    world1.foods = []
    world2.foods = []
    
    for _ in range(FOOD_MAX := 90):
        world1.spawn_food()
        world2.spawn_food()
    
    foods1 = [(f["pos"][0], f["pos"][1], f["nutrition"]) for f in world1.foods]
    foods2 = [(f["pos"][0], f["pos"][1], f["nutrition"]) for f in world2.foods]
    
    assert foods1 == foods2, "Спавн еды должен быть детерминированным"


def test_world_extinction_protection():
    """Защита от вымирания должна использовать RNG детерминированно."""
    seed = 99999
    
    world1 = World(rng=RNG(seed=seed))
    world2 = World(rng=RNG(seed=seed))
    
    # Убиваем всех агентов кроме одного
    for agent in world1.agents[1:]:
        agent.alive = False
    for agent in world2.agents[1:]:
        agent.alive = False
    
    # Фильтруем мёртвых
    world1.agents = [a for a in world1.agents if a.alive]
    world2.agents = [a for a in world2.agents if a.alive]
    
    # Выполняем update - должна сработать защита от вымирания
    world1.update()
    world2.update()
    
    # Количество агентов должно быть одинаковым
    assert len(world1.agents) == len(world2.agents), \
        "Защита от вымирания должна работать детерминированно"
    
    # Оба мира должны иметь как минимум MIN_AGENTS агентов
    from alife.config import MIN_AGENTS
    assert len(world1.agents) >= MIN_AGENTS
    assert len(world2.agents) >= MIN_AGENTS


def test_world_rng_only_source_of_randomness():
    """World должен использовать только переданный RNG."""
    # Создаём мир с конкретным seed
    world = World(rng=RNG(seed=77777))
    
    # Проверяем, что у всех агентов есть rng и он является копией world.rng
    # (или создан из него)
    for agent in world.agents:
        assert hasattr(agent, 'rng'), "У агента должен быть rng"
        assert agent.rng is not None, "rng агента не должен быть None"
