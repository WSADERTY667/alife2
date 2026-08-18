"""
Тесты для детерминированного RNG (SplitMix64).
"""

import pytest
from alife.rng import RNG


class TestRNGDeterminism:
    """Тесты на детерминированность RNG."""
    
    def test_same_seed_same_sequence(self):
        """Два RNG с одинаковым seed дают одинаковую последовательность."""
        rng1 = RNG(seed=42)
        rng2 = RNG(seed=42)
        
        for _ in range(100):
            assert rng1.next_int() == rng2.next_int()
    
    def test_same_seed_same_floats(self):
        """Два RNG с одинаковым seed дают одинаковые float значения."""
        rng1 = RNG(seed=12345)
        rng2 = RNG(seed=12345)
        
        for _ in range(50):
            assert rng1.next_float() == rng2.next_float()
    
    def test_different_seed_different_sequence(self):
        """RNG с разными seed дают разные последовательности."""
        rng1 = RNG(seed=1)
        rng2 = RNG(seed=2)
        
        # Вероятность совпадения всех 10 значений крайне мала
        matches = sum(1 for _ in range(10) if rng1.next_int() == rng2.next_int())
        assert matches < 10  # Не все должны совпадать
    
    def test_zero_seed(self):
        """Seed=0 должен работать корректно."""
        rng1 = RNG(seed=0)
        rng2 = RNG(seed=0)
        
        for _ in range(10):
            assert rng1.next_int() == rng2.next_int()
    
    def test_negative_seed(self):
        """Отрицательный seed должен работать корректно."""
        rng1 = RNG(seed=-42)
        rng2 = RNG(seed=-42)
        
        for _ in range(10):
            assert rng1.next_int() == rng2.next_int()
    
    def test_large_seed(self):
        """Большой seed должен работать корректно."""
        rng1 = RNG(seed=2**63 + 12345)
        rng2 = RNG(seed=2**63 + 12345)
        
        for _ in range(10):
            assert rng1.next_int() == rng2.next_int()


class TestNextInt:
    """Тесты для метода next_int()."""
    
    def test_next_int_range(self):
        """next_int() возвращает значения в диапазоне [0, 2^32)."""
        rng = RNG(seed=42)
        
        for _ in range(1000):
            value = rng.next_int()
            assert 0 <= value < (1 << 32)
    
    def test_next_int_is_integer(self):
        """next_int() возвращает целое число."""
        rng = RNG(seed=42)
        assert isinstance(rng.next_int(), int)


class TestNextFloat:
    """Тесты для метода next_float()."""
    
    def test_next_float_range(self):
        """next_float() возвращает значения в диапазоне [0.0, 1.0)."""
        rng = RNG(seed=42)
        
        for _ in range(1000):
            value = rng.next_float()
            assert 0.0 <= value < 1.0
    
    def test_next_float_is_float(self):
        """next_float() возвращает float."""
        rng = RNG(seed=42)
        assert isinstance(rng.next_float(), float)


class TestRandint:
    """Тесты для метода randint()."""
    
    def test_randint_range(self):
        """randint(a, b) возвращает значения в диапазоне [a, b]."""
        rng = RNG(seed=42)
        
        for _ in range(1000):
            value = rng.randint(10, 20)
            assert 10 <= value <= 20
    
    def test_randint_single_value(self):
        """randint(a, a) всегда возвращает a."""
        rng = RNG(seed=42)
        
        for _ in range(10):
            assert rng.randint(42, 42) == 42
    
    def test_randint_negative_range(self):
        """randint() работает с отрицательными диапазонами."""
        rng = RNG(seed=42)
        
        for _ in range(100):
            value = rng.randint(-10, -5)
            assert -10 <= value <= -5
    
    def test_randint_mixed_range(self):
        """randint() работает со смешанными диапазонами."""
        rng = RNG(seed=42)
        
        for _ in range(100):
            value = rng.randint(-5, 5)
            assert -5 <= value <= 5
    
    def test_randint_invalid_range(self):
        """randint(a, b) с a > b выбрасывает ValueError."""
        rng = RNG(seed=42)
        
        with pytest.raises(ValueError):
            rng.randint(10, 5)


class TestChoice:
    """Тесты для метода choice()."""
    
    def test_choice_from_list(self):
        """choice() возвращает элемент из списка."""
        rng = RNG(seed=42)
        items = [1, 2, 3, 4, 5]
        
        for _ in range(100):
            value = rng.choice(items)
            assert value in items
    
    def test_choice_from_tuple(self):
        """choice() работает с кортежами."""
        rng = RNG(seed=42)
        items = (10, 20, 30)
        
        for _ in range(50):
            value = rng.choice(items)
            assert value in items
    
    def test_choice_from_string(self):
        """choice() работает со строками."""
        rng = RNG(seed=42)
        s = "hello"
        
        for _ in range(50):
            value = rng.choice(s)
            assert value in s
    
    def test_choice_empty_sequence(self):
        """choice() с пустой последовательностью выбрасывает IndexError."""
        rng = RNG(seed=42)
        
        with pytest.raises(IndexError):
            rng.choice([])
    
    def test_choice_deterministic(self):
        """choice() детерминирован при одинаковом seed."""
        rng1 = RNG(seed=999)
        rng2 = RNG(seed=999)
        items = ['a', 'b', 'c', 'd', 'e']
        
        for _ in range(50):
            assert rng1.choice(items) == rng2.choice(items)


class TestGauss:
    """Тесты для метода gauss()."""
    
    def test_gauss_returns_float(self):
        """gauss() возвращает float."""
        rng = RNG(seed=42)
        assert isinstance(rng.gauss(), float)
    
    def test_gauss_mean_approximation(self):
        """Среднее значение gauss(mu, sigma) приближается к mu."""
        rng = RNG(seed=42)
        mu = 5.0
        sigma = 1.0
        
        values = [rng.gauss(mu, sigma) for _ in range(1000)]
        mean = sum(values) / len(values)
        
        # Среднее должно быть близко к mu (с допуском для случайности)
        assert abs(mean - mu) < 0.5
    
    def test_gauss_invalid_sigma(self):
        """gauss() с sigma <= 0 выбрасывает ValueError."""
        rng = RNG(seed=42)
        
        with pytest.raises(ValueError):
            rng.gauss(sigma=0)
        
        with pytest.raises(ValueError):
            rng.gauss(sigma=-1)
    
    def test_gauss_deterministic(self):
        """gauss() детерминирован при одинаковом seed."""
        rng1 = RNG(seed=777)
        rng2 = RNG(seed=777)
        
        for _ in range(50):
            assert rng1.gauss() == rng2.gauss()


class TestShuffle:
    """Тесты для метода shuffle()."""
    
    def test_shuffle_preserves_elements(self):
        """shuffle() сохраняет все элементы списка."""
        rng = RNG(seed=42)
        original = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        shuffled = original.copy()
        rng.shuffle(shuffled)
        
        assert sorted(shuffled) == sorted(original)
    
    def test_shuffle_changes_order(self):
        """shuffle() обычно меняет порядок элементов."""
        rng = RNG(seed=42)
        original = list(range(100))
        shuffled = original.copy()
        rng.shuffle(shuffled)
        
        # С вероятностью ~100% порядок изменится для 100 элементов
        assert shuffled != original or len(original) <= 1
    
    def test_shuffle_deterministic(self):
        """shuffle() детерминирован при одинаковом seed."""
        original = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        rng1 = RNG(seed=555)
        rng2 = RNG(seed=555)
        
        lst1 = original.copy()
        lst2 = original.copy()
        
        rng1.shuffle(lst1)
        rng2.shuffle(lst2)
        
        assert lst1 == lst2
    
    def test_shuffle_empty_list(self):
        """shuffle() работает с пустым списком."""
        rng = RNG(seed=42)
        lst = []
        rng.shuffle(lst)
        assert lst == []
    
    def test_shuffle_single_element(self):
        """shuffle() работает со списком из одного элемента."""
        rng = RNG(seed=42)
        lst = [42]
        rng.shuffle(lst)
        assert lst == [42]


class TestCopy:
    """Тесты для метода copy()."""
    
    def test_copy_same_state(self):
        """copy() создаёт RNG с тем же состоянием."""
        rng1 = RNG(seed=42)
        # Прогоним несколько значений
        for _ in range(10):
            rng1.next_int()
        
        rng2 = rng1.copy()
        
        # Копия должна давать те же значения
        for _ in range(100):
            assert rng1.next_int() == rng2.next_int()
    
    def test_copy_independent(self):
        """Копия независима от оригинала после создания."""
        rng1 = RNG(seed=42)
        rng2 = rng1.copy()

        # Продвигаем только оригинал на несколько шагов
        for _ in range(5):
            rng1.next_int()
        
        # Копия должна оставаться в исходном состоянии
        # и давать значения, которые rng1 давал бы, если бы его не продвигали
        rng3 = RNG(seed=42)  # Третий RNG с тем же начальным seed
        
        # Теперь rng2 (копия) должен давать те же значения, что rng3
        for _ in range(10):
            assert rng2.next_int() == rng3.next_int()
        
        # А rng1 уже даёт другие значения (он был продвинут)
        # Проверяем, что последовательности разные
        rng1_vals = [rng1.next_int() for _ in range(10)]
        rng2_vals = [rng2.next_int() for _ in range(10)]
        assert rng1_vals != rng2_vals

class TestGetSetState:
    """Тесты для get_state() и set_state()."""
    
    def test_get_set_state(self):
        """set_state(get_state()) восстанавливает состояние."""
        rng1 = RNG(seed=42)
        for _ in range(10):
            rng1.next_int()
        
        state = rng1.get_state()
        
        rng2 = RNG(seed=0)
        rng2.set_state(state)
        
        for _ in range(100):
            assert rng1.next_int() == rng2.next_int()
