"""
Детерминированный RNG на основе алгоритма SplitMix64.
Обеспечивает воспроизводимую последовательность чисел при одинаковом seed.
"""

from typing import Any, List, Optional, Sequence, TypeVar

T = TypeVar('T')


class RNG:
    """
    Детерминированный генератор псевдослучайных чисел на основе SplitMix64.
    
    SplitMix64 — простой и быстрый алгоритм, обеспечивающий хорошее качество
    случайности и полную детерминированность при одинаковом начальном seed.
    """
    
    MASK64 = (1 << 64) - 1
    MASK32 = (1 << 32) - 1
    
    def __init__(self, seed: int = 0):
        """
        Инициализировать RNG с заданным seed.
        
        Args:
            seed: Начальное значение (целое число). Может быть отрицательным.
        """
        self._state = seed & self.MASK64
    
    def _next_state(self) -> int:
        """
        Обновить внутреннее состояние и вернуть следующее 64-битное значение.
        Реализация SplitMix64.
        """
        self._state = (self._state + 0x9E3779B97F4A7C15) & self.MASK64
        z = self._state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & self.MASK64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & self.MASK64
        return z ^ (z >> 31)
    
    def next_int(self) -> int:
        """
        Вернуть следующее случайное целое число в диапазоне [0, 2^32).
        
        Returns:
            Случайное 32-битное неотрицательное целое число.
        """
        return self._next_state() & self.MASK32
    
    def next_float(self) -> float:
        """
        Вернуть следующее случайное число с плавающей точкой в диапазоне [0.0, 1.0).
        
        Returns:
            Случайное float значение от 0.0 (включительно) до 1.0 (исключительно).
        """
        return self.next_int() / (self.MASK32 + 1)
    
    def randint(self, a: int, b: int) -> int:
        """
        Вернуть случайное целое число в диапазоне [a, b] (оба конца включены).
        
        Args:
            a: Нижняя граница (включительно).
            b: Верхняя граница (включительно).
            
        Returns:
            Случайное целое число от a до b включительно.
            
        Raises:
            ValueError: Если a > b.
        """
        if a > b:
            raise ValueError(f"Нижняя граница ({a}) не может быть больше верхней ({b})")
        
        if a == b:
            return a
        
        range_size = b - a + 1
        return a + (self.next_int() % range_size)
    
    def choice(self, seq: Sequence[T]) -> T:
        """
        Вернуть случайный элемент из непустой последовательности.
        
        Args:
            seq: Непустая последовательность (список, кортеж, строка и т.д.).
            
        Returns:
            Случайный элемент из последовательности.
            
        Raises:
            IndexError: Если последовательность пуста.
        """
        if len(seq) == 0:
            raise IndexError("choice из пустой последовательности")
        return seq[self.randint(0, len(seq) - 1)]
    
    def gauss(self, mu: float = 0.0, sigma: float = 1.0) -> float:
        """
        Вернуть случайное число с нормальным (Гауссовым) распределением.
        
        Использует метод Бокса-Мюллера для преобразования двух равномерных
        случайных величин в нормально распределённую.
        
        Args:
            mu: Математическое ожидание (среднее значение).
            sigma: Стандартное отклонение (должно быть > 0).
            
        Returns:
            Случайное число с нормальным распределением N(mu, sigma^2).
        """
        import math
        
        if sigma <= 0:
            raise ValueError("sigma должно быть положительным")
        
        # Метод Бокса-Мюллера
        u1 = self.next_float()
        u2 = self.next_float()
        
        # Избегаем log(0)
        while u1 == 0.0:
            u1 = self.next_float()
        
        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return mu + sigma * z0
    
    def shuffle(self, lst: List[Any]) -> None:
        """
        Перемешать список на месте (алгоритм Фишера-Йетса).
        
        Args:
            lst: Список для перемешивания (изменяется на месте).
        """
        n = len(lst)
        for i in range(n - 1, 0, -1):
            j = self.randint(0, i)
            lst[i], lst[j] = lst[j], lst[i]
    
    def copy(self) -> 'RNG':
        """
        Создать копию RNG с тем же состоянием.
        
        Returns:
            Новый экземпляр RNG с идентичным внутренним состоянием.
        """
        new_rng = RNG.__new__(RNG)
        new_rng._state = self._state
        return new_rng
    
    def set_state(self, state: int) -> None:
        """
        Установить внутреннее состояние вручную.
        
        Args:
            state: Новое значение состояния (будет приведено к 64 битам).
        """
        self._state = state & self.MASK64
    
    def get_state(self) -> int:
        """
        Получить текущее внутреннее состояние.
        
        Returns:
            Текущее 64-битное состояние генератора.
        """
        return self._state
