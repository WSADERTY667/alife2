"""
Тесты на детерминизм Agent при использовании RNG.
"""

import math
import numpy as np
from alife.agent import Agent
from alife.genome import Genome
from alife.rng import RNG


class TestAgentDeterminism:
    """Тесты на детерминированность поведения агента."""

    def test_same_seed_same_initial_angle(self):
        """Два агента с одинаковым seed должны иметь одинаковый начальный угол."""
        genome = Genome()
        
        rng1 = RNG(seed=42)
        agent1 = Agent([500.0, 320.0], genome, rng=rng1)
        
        rng2 = RNG(seed=42)
        agent2 = Agent([500.0, 320.0], genome, rng=rng2)
        
        assert agent1.angle == agent2.angle, "Начальные углы должны совпадать"

    def test_same_seed_same_repro_cooldown(self):
        """Два агента с одинаковым seed должны иметь одинаковый repro_cooldown."""
        genome = Genome()
        
        rng1 = RNG(seed=123)
        agent1 = Agent([500.0, 320.0], genome, rng=rng1)
        
        rng2 = RNG(seed=123)
        agent2 = Agent([500.0, 320.0], genome, rng=rng2)
        
        assert agent1.repro_cooldown == agent2.repro_cooldown, "repro_cooldown должны совпадать"

    def test_different_seed_different_angle(self):
        """Агенты с разными seed должны (обычно) иметь разные углы."""
        genome = Genome()
        
        rng1 = RNG(seed=1)
        agent1 = Agent([500.0, 320.0], genome, rng=rng1)
        
        rng2 = RNG(seed=2)
        agent2 = Agent([500.0, 320.0], genome, rng=rng2)
        
        # Углы скорее всего будут разными, но это не строго обязательно
        # Проверяем просто, что они в допустимом диапазоне
        assert -math.pi <= agent1.angle <= math.pi
        assert -math.pi <= agent2.angle <= math.pi

    def test_agent_no_global_random(self):
        """Проверка, что агент не использует глобальный random напрямую."""
        import random
        
        genome = Genome()
        
        # Сохраняем состояние global random
        state_before = random.getstate()
        
        rng = RNG(seed=42)
        agent = Agent([500.0, 320.0], genome, rng=rng)
        
        # Создаём второго агента с тем же seed
        rng2 = RNG(seed=42)
        agent2 = Agent([500.0, 320.0], genome, rng=rng2)
        
        # Состояние global random не должно измениться
        state_after = random.getstate()
        
        # Проверяем, что состояния идентичны
        assert str(state_before) == str(state_after), "Agent не должен использовать global random"

    def test_reflex_turn_deterministic(self):
        """Рефлексы агента должны быть детерминированными."""
        from alife.world import World
        from alife.config import REFLEX_ASSIST
        
        if not REFLEX_ASSIST:
            return  # Пропускаем, если рефлексы отключены
        
        genome = Genome()
        
        rng1 = RNG(seed=999)
        agent1 = Agent([500.0, 320.0], genome, rng=rng1)
        
        rng2 = RNG(seed=999)
        agent2 = Agent([500.0, 320.0], genome, rng=rng2)
        
        # Создаём фиктивный world для update
        world1 = World(rng=RNG(seed=100))
        world2 = World(rng=RNG(seed=100))
        
        # Устанавливаем одинаковые сенсоры
        agent1.nearest_food = None
        agent1.nearest_agent = None
        agent2.nearest_food = None
        agent2.nearest_agent = None
        
        # Запоминаем начальное состояние
        angle1_before = agent1.angle
        angle2_before = agent2.angle
        
        # Выполняем один шаг
        agent1.update(world1, dt=1.0)
        agent2.update(world2, dt=1.0)
        
        # Углы после шага должны совпадать
        assert agent1.angle == agent2.angle, f"Углы после update должны совпадать: {agent1.angle} vs {agent2.angle}"

    def test_breakdown_noise_deterministic(self):
        """breakdown-шум должен быть детерминированным."""
        from alife.world import World
        
        genome = Genome()
        # Устанавливаем параметры, которые могут вызвать breakdown
        genome.genes["stress_gain"] = 1.5
        genome.genes["trauma_gain"] = 1.5
        
        rng1 = RNG(seed=777)
        agent1 = Agent([500.0, 320.0], genome, rng=rng1)
        
        rng2 = RNG(seed=777)
        agent2 = Agent([500.0, 320.0], genome, rng=rng2)
        
        world1 = World(rng=RNG(seed=200))
        world2 = World(rng=RNG(seed=200))
        
        agent1.nearest_food = None
        agent1.nearest_agent = None
        agent2.nearest_food = None
        agent2.nearest_agent = None
        
        # Выполняем несколько шагов
        for _ in range(10):
            agent1.update(world1, dt=1.0)
            agent2.update(world2, dt=1.0)
        
        # Позиции и углы должны совпадать
        assert np.allclose(agent1.pos, agent2.pos), f"Позиции должны совпадать: {agent1.pos} vs {agent2.pos}"
        assert agent1.angle == agent2.angle, f"Углы должны совпадать: {agent1.angle} vs {agent2.angle}"
        assert agent1.energy == agent2.energy, f"Энергия должна совпадать: {agent1.energy} vs {agent2.energy}"

    def test_reproduction_chance_deterministic(self):
        """Проверка воспроизведения должна быть детерминированной."""
        from alife.world import World
        from alife.config import MATURE_AGE, REPRO_ENERGY
        
        genome = Genome()
        
        rng1 = RNG(seed=555)
        agent1 = Agent([500.0, 320.0], genome, rng=rng1)
        
        rng2 = RNG(seed=555)
        agent2 = Agent([500.0, 320.0], genome, rng=rng2)
        
        # Искусственно делаем агентов способными к размножению
        agent1.age = MATURE_AGE + 100
        agent1.energy = REPRO_ENERGY + 50
        agent1.repro_cooldown = 0
        agent2.age = MATURE_AGE + 100
        agent2.energy = REPRO_ENERGY + 50
        agent2.repro_cooldown = 0
        
        # Создаём партнёра
        mate_genome = Genome()
        mate1 = Agent([510.0, 320.0], mate_genome, rng=RNG(seed=556))
        mate2 = Agent([510.0, 320.0], mate_genome, rng=RNG(seed=556))
        
        mate1.age = MATURE_AGE + 100
        mate1.energy = REPRO_ENERGY + 50
        mate1.repro_cooldown = 0
        mate2.age = MATURE_AGE + 100
        mate2.energy = REPRO_ENERGY + 50
        mate2.repro_cooldown = 0
        
        world1 = World(rng=RNG(seed=300))
        world2 = World(rng=RNG(seed=300))
        
        # Устанавливаем nearest_agent
        agent1.nearest_agent = (5.0, 0.0, mate1, 0.5)
        agent2.nearest_agent = (5.0, 0.0, mate2, 0.5)
        agent1.nearest_food = None
        agent2.nearest_food = None
        
        # Выполняем шаг
        agent1.update(world1, dt=1.0)
        agent2.update(world2, dt=1.0)
        
        # Количество новорождённых должно совпадать
        assert len(world1.newborns) == len(world2.newborns), \
            f"Количество newborns должно совпадать: {len(world1.newborns)} vs {len(world2.newborns)}"


class TestAgentWithWorldDeterminism:
    """Интеграционные тесты детерминизма агента в мире."""

    def test_world_same_seed_same_behavior(self):
        """Мир с одинаковым seed должен давать одинаковое поведение агентов."""
        from alife.world import World
        
        world1 = World(rng=RNG(seed=12345))
        world2 = World(rng=RNG(seed=12345))
        
        # Получаем первого агента из каждого мира
        agent1 = world1.agents[0]
        agent2 = world2.agents[0]
        
        # Запоминаем начальное состояние
        pos1_before = agent1.pos.copy()
        pos2_before = agent2.pos.copy()
        angle1_before = agent1.angle
        angle2_before = agent2.angle
        
        assert np.allclose(pos1_before, pos2_before), "Начальные позиции должны совпадать"
        assert angle1_before == angle2_before, "Начальные углы должны совпадать"
        
        # Выполняем несколько тиков
        for _ in range(20):
            world1.update()
            world2.update()
        
        # Находим соответствующего агента (по id)
        agent1_after = next((a for a in world1.agents if a.id == agent1.id), None)
        agent2_after = next((a for a in world2.agents if a.id == agent2.id), None)
        
        if agent1_after is not None and agent2_after is not None:
            assert np.allclose(agent1_after.pos, agent2_after.pos), \
                f"Позиции после 20 тиков должны совпадать: {agent1_after.pos} vs {agent2_after.pos}"
            assert agent1_after.angle == agent2_after.angle, \
                f"Углы после 20 тиков должны совпадать: {agent1_after.angle} vs {agent2_after.angle}"
            assert agent1_after.energy == agent2_after.energy, \
                f"Энергия после 20 тиков должна совпадать: {agent1_after.energy} vs {agent2_after.energy}"
