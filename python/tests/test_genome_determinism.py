"""
Тест на детерминированность Genome при использовании RNG.
Проверяет, что одинаковый seed даёт одинаковые результаты.
"""
import pytest
from alife.genome import Genome
from alife.rng import RNG


class TestGenomeDeterminism:
    """Тесты на повторяемость операций Genome с одинаковым seed."""

    def test_genome_creation_same_seed(self):
        """Одинаковый seed при создании Genome даёт одинаковые гены и tag."""
        rng1 = RNG(42)
        g1 = Genome(rng=rng1)

        rng2 = RNG(42)
        g2 = Genome(rng=rng2)

        # Проверяем все гены
        for k in g1.genes.keys():
            assert g1.genes[k] == pytest.approx(g2.genes[k], rel=1e-10), \
                f"Ген {k} различается: {g1.genes[k]} != {g2.genes[k]}"

        # Проверяем tag
        assert g1.tag == g2.tag, f"Tag различается: {g1.tag} != {g2.tag}"

        # Проверяем n_hidden (по умолчанию одинаковое)
        assert g1.n_hidden == g2.n_hidden

    def test_crossover_same_seed_same_parents(self):
        """Одинаковый seed и одинаковые родители дают одинаковый child genome."""
        # Создаём родителей с фиксированными seed
        parent_a1 = Genome(rng=RNG(10))
        parent_b1 = Genome(rng=RNG(20))

        # Кроссовер с seed 123
        child1 = Genome.crossover(parent_a1, parent_b1, rng=RNG(123))

        # Повторяем с теми же seed
        parent_a2 = Genome(rng=RNG(10))
        parent_b2 = Genome(rng=RNG(20))
        child2 = Genome.crossover(parent_a2, parent_b2, rng=RNG(123))

        # Проверяем все гены ребёнка
        for k in child1.genes.keys():
            assert child1.genes[k] == pytest.approx(child2.genes[k], rel=1e-10), \
                f"Ген ребёнка {k} различается: {child1.genes[k]} != {child2.genes[k]}"

        # Проверяем tag
        assert child1.tag == child2.tag, f"Tag ребёнка различается: {child1.tag} != {child2.tag}"

        # Проверяем n_hidden
        assert child1.n_hidden == child2.n_hidden, \
            f"n_hidden ребёнка различается: {child1.n_hidden} != {child2.n_hidden}"

    def test_mutation_same_seed_same_parent(self):
        """Одинаковый seed мутации на одинаковом родителе даёт одинаковый результат."""
        # Создаём идентичные геномы
        g1 = Genome(rng=RNG(99))
        g1.tag = 3
        g1.n_hidden = 200

        g2 = Genome(rng=RNG(99))
        g2.tag = 3
        g2.n_hidden = 200

        # Мутируем с одинаковым seed
        g1.mutate(rng=RNG(456))
        g2.mutate(rng=RNG(456))

        # Проверяем все гены после мутации
        for k in g1.genes.keys():
            assert g1.genes[k] == pytest.approx(g2.genes[k], rel=1e-10), \
                f"Мутированный ген {k} различается: {g1.genes[k]} != {g2.genes[k]}"

        # Проверяем tag после мутации
        assert g1.tag == g2.tag, f"Tag после мутации различается: {g1.tag} != {g2.tag}"

        # Проверяем n_hidden после мутации
        assert g1.n_hidden == g2.n_hidden, \
            f"n_hidden после мутации различается: {g1.n_hidden} != {g2.n_hidden}"

    def test_full_lifecycle_determinism(self):
        """Полный цикл: создание -> кроссовер -> мутация с одинаковыми seed."""
        # Первый прогон
        pa1 = Genome(rng=RNG(1))
        pb1 = Genome(rng=RNG(2))
        child1 = Genome.crossover(pa1, pb1, rng=RNG(3))
        child1.mutate(rng=RNG(4))

        # Второй прогон с теми же seed
        pa2 = Genome(rng=RNG(1))
        pb2 = Genome(rng=RNG(2))
        child2 = Genome.crossover(pa2, pb2, rng=RNG(3))
        child2.mutate(rng=RNG(4))

        # Проверяем идентичность финального генома
        for k in child1.genes.keys():
            assert child1.genes[k] == pytest.approx(child2.genes[k], rel=1e-10), \
                f"Финальный ген {k} различается: {child1.genes[k]} != {child2.genes[k]}"

        assert child1.tag == child2.tag
        assert child1.n_hidden == child2.n_hidden
        assert child1.tribal_tags == child2.tribal_tags

    def test_different_seed_different_result(self):
        """Разные seed должны давать разные результаты (с высокой вероятностью)."""
        g1 = Genome(rng=RNG(100))
        g2 = Genome(rng=RNG(101))

        # Хотя бы некоторые гены должны отличаться
        different_count = sum(
            1 for k in g1.genes.keys()
            if abs(g1.genes[k] - g2.genes[k]) > 1e-6
        )
        # Ожидаем, что большинство генов будут разными
        assert different_count > len(g1.genes) // 2, \
            f"Слишком мало различных генов: {different_count} из {len(g1.genes)}"
