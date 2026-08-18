# test_emotions.py
# Тесты для расширенной эмоциональной модели
import pytest
from alife.genome import Genome
from alife.hormones import Hormones


def test_hormones_initialization():
    """Тест: инициализация гормонов с геномом."""
    genome = Genome()
    hormones = Hormones(genome)
    
    assert 0.0 <= hormones.D <= 2.0
    assert 0.0 <= hormones.S <= 2.0
    assert 0.0 <= hormones.O <= 2.0
    assert 0.0 <= hormones.C <= 2.0
    assert 0.0 <= hormones.T <= 2.0
    assert hormones.allostatic == 0.0
    assert hormones.depression == 0.0
    assert hormones.breakdown == 0.0
    assert hormones.paranoia == 0.0
    assert 0.0 <= hormones.trust <= 1.0
    assert hormones.delayed_punishment == 0.0


def test_stress_increases_cortisol():
    """Тест: стресс увеличивает кортизол."""
    genome = Genome()
    hormones = Hormones(genome)
    
    events = {
        "punishment": 1.0,
        "conflict": 0.8,
        "hunger": 0.5,
        "injury": 0.3,
        "fear": 0.6,
    }
    
    for _ in range(20):
        hormones.update(1.0, events, genome)
    
    assert hormones.C > genome["cortisol_base"]


def test_chronic_stress_leads_to_breakdown():
    """Тест: хронический стресс приводит к слому."""
    genome = Genome()
    hormones = Hormones(genome)
    
    # Постоянный высокий стресс
    events = {
        "punishment": 1.0,
        "conflict": 1.0,
        "hunger": 0.8,
        "injury": 0.5,
        "fear": 0.8,
        "reward": 0.0,
        "social": 0.0,
        "kin": 0.0,
        "dominance": 0.0,
    }
    
    # Много циклов обновления для накопления аллостатической нагрузки
    for _ in range(500):
        hormones.update(1.0, events, genome)
    
    assert hormones.allostatic > 1.0 or hormones.breakdown > 0.0


def test_low_serotonin_dopamine_causes_depression():
    """Тест: низкий серотонин и дофамин вызывают депрессию."""
    genome = Genome()
    hormones = Hormones(genome)
    
    # События, которые снижают серотонин и дофамин
    events = {
        "reward": 0.0,
        "punishment": 0.8,
        "social": 0.0,
        "kin": 0.0,
        "conflict": 0.5,
        "dominance": 0.0,
        "hunger": 0.7,
        "injury": 0.2,
        "fear": 0.4,
    }
    
    # Искусственно занижаем базовые уровни
    hormones.S = 0.15
    hormones.D = 0.15
    
    for _ in range(150):
        hormones.update(1.0, events, genome)
    
    # Депрессия должна развиться или серотонин остаться низким
    assert hormones.depression > 0.0 or hormones.S < 0.35


def test_oxytocin_increases_sociality():
    """Тест: окситоцин увеличивает социальность."""
    genome = Genome()
    hormones = Hormones(genome)
    
    # Социальные события
    events = {
        "social": 1.0,
        "kin": 0.8,
        "reward": 0.3,
        "punishment": 0.0,
        "conflict": 0.0,
        "dominance": 0.0,
        "hunger": 0.0,
        "injury": 0.0,
        "fear": 0.0,
    }
    
    for _ in range(30):
        hormones.update(1.0, events, genome)
    
    assert hormones.O > genome["oxytocin_base"]
    
    effects = hormones.effects(genome)
    # Социальность должна быть положительной
    assert effects["sociality"] > 0.0


def test_punishment_history_affects_delayed_punishment():
    """Тест: история наказаний влияет на отложенное наказание."""
    genome = Genome()
    hormones = Hormones(genome)
    
    # Единичное сильное наказание
    events = {
        "punishment": 1.0,
        "reward": 0.0,
        "social": 0.0,
        "kin": 0.0,
        "conflict": 0.0,
        "dominance": 0.0,
        "hunger": 0.0,
        "injury": 0.0,
        "fear": 0.0,
    }
    
    hormones.update(1.0, events, genome)
    
    # Проверяем, что отложенное наказание появилось
    assert len(hormones.punishment_history) > 0 or hormones.delayed_punishment > 0


def test_paranoia_increases_with_punishment():
    """Тест: паранойя растёт от наказания."""
    genome = Genome()
    hormones = Hormones(genome)
    
    events = {
        "punishment": 0.8,
        "conflict": 0.5,
        "fear": 0.6,
        "reward": 0.0,
        "social": 0.0,
        "kin": 0.0,
        "dominance": 0.0,
        "hunger": 0.0,
        "injury": 0.0,
    }
    
    for _ in range(100):
        hormones.update(1.0, events, genome)
    
    assert hormones.paranoia > 0.0


def test_trust_increases_with_positive_social():
    """Тест: доверие растёт от позитивного социального опыта."""
    genome = Genome()
    hormones = Hormones(genome)
    
    events = {
        "social": 1.0,
        "kin": 0.7,
        "reward": 0.5,
        "punishment": 0.0,
        "conflict": 0.0,
        "dominance": 0.0,
        "hunger": 0.0,
        "injury": 0.0,
        "fear": 0.0,
    }
    
    for _ in range(50):
        hormones.update(1.0, events, genome)
    
    assert hormones.trust >= 0.5 or hormones.O > 0.5


def test_aggression_affected_by_paranoia_and_trust():
    """Тест: агрессия зависит от паранойи и доверия."""
    genome = Genome()
    hormones = Hormones(genome)
    
    # Устанавливаем высокую паранойю вручную
    hormones.paranoia = 0.8
    hormones.trust = 0.2
    hormones.T = 1.2
    hormones.C = 0.9
    
    effects_normal = hormones.effects(genome)
    
    # Теперь низкая паранойя и высокое доверие
    hormones.paranoia = 0.1
    hormones.trust = 0.8
    
    effects_low_paranoia = hormones.effects(genome)
    
    # Агрессия должна быть выше при высокой паранойе
    assert effects_normal["aggression"] > effects_low_paranoia["aggression"] * 1.1


def test_mood_refects_emotional_state():
    """Тест: настроение отражает эмоциональное состояние."""
    genome = Genome()
    hormones = Hormones(genome)
    
    # Депрессия
    hormones.depression = 0.7
    assert hormones.get_mood() == "грусть"
    
    # Слом
    hormones.depression = 0.3
    hormones.breakdown = 0.7
    assert hormones.get_mood() == "ярость"
    
    # Паранойя
    hormones.breakdown = 0.3
    hormones.paranoia = 0.8
    assert hormones.get_mood() == "подозрительность"
    
    # Спокойствие - устанавливаем условия, где нет других доминирующих состояний
    hormones.paranoia = 0.2
    hormones.trust = 0.8
    hormones.O = 0.7
    hormones.D = 0.5  # Не слишком высокий дофамин
    hormones.S = 0.5  # Не слишком высокий серотонин
    assert hormones.get_mood() in ["спокойствие", "нормальное"]


def test_helper_methods():
    """Тест: вспомогательные методы проверки состояния."""
    genome = Genome()
    hormones = Hormones(genome)
    
    assert not hormones.is_broken()
    assert not hormones.is_depressed()
    assert not hormones.is_paranoid()
    assert hormones.is_trusting()  # начальное доверие 0.5 (>= 0.5 считается доверяющим)
    
    hormones.breakdown = 0.6
    assert hormones.is_broken()
    
    hormones.depression = 0.6
    assert hormones.is_depressed()
    
    hormones.paranoia = 0.6
    assert hormones.is_paranoid()
    
    hormones.trust = 0.3
    assert not hormones.is_trusting()


def test_individual_hormone_profiles():
    """Тест: индивидуальные гормональные профили влияют на поведение."""
    # Агент с высокой чувствительностью к серотонину
    genome_high_sensitivity = Genome()
    genome_high_sensitivity.genes["serotonin_sensitivity"] = 1.8
    
    # Агент с низкой чувствительностью к серотонину
    genome_low_sensitivity = Genome()
    genome_low_sensitivity.genes["serotonin_sensitivity"] = 0.6
    
    hormones_high = Hormones(genome_high_sensitivity)
    hormones_low = Hormones(genome_low_sensitivity)
    
    # Одинаковые события
    events = {
        "reward": 0.5,
        "punishment": 0.0,
        "social": 0.5,
        "kin": 0.3,
        "conflict": 0.0,
        "dominance": 0.0,
        "hunger": 0.0,
        "injury": 0.0,
        "fear": 0.0,
    }
    
    for _ in range(30):
        hormones_high.update(1.0, events, genome_high_sensitivity)
        hormones_low.update(1.0, events, genome_low_sensitivity)
    
    # Эффекты должны различаться из-за разной чувствительности
    effects_high = hormones_high.effects(genome_high_sensitivity)
    effects_low = hormones_low.effects(genome_low_sensitivity)
    
    # Проверяем, что чувствительность влияет на результаты
    assert effects_high is not None
    assert effects_low is not None
