#!/usr/bin/env python3
"""
Тесты для инструмента сравнения Python и C++ симуляций.
"""

import json
import os
import sys
import tempfile
import unittest

# Добавляем путь к инструменту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tools.compare_python_cpp import (
    load_json,
    compare_values,
    compare_positions,
    compare_scalar_values,
    compare_agent_properties,
)


class TestCompareValues(unittest.TestCase):
    """Тесты для функции compare_values."""

    def test_equal_values(self):
        """Равные значения должны проходить проверку."""
        ok, err = compare_values(1.0, 1.0, 1e-3, "test")
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_within_tolerance(self):
        """Значения в пределах допуска должны проходить проверку."""
        ok, err = compare_values(1.0, 1.0005, 1e-3, "test")
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_outside_tolerance(self):
        """Значения вне допуска не должны проходить проверку."""
        ok, err = compare_values(1.0, 1.1, 1e-3, "test")
        self.assertFalse(ok)
        self.assertIsNotNone(err)

    def test_none_values(self):
        """Два None должны считаться равными."""
        ok, err = compare_values(None, None, 1e-3, "test")
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_integer_values(self):
        """Целочисленные значения должны сравниваться корректно."""
        ok, err = compare_values(5, 5, 1e-3, "test")
        self.assertTrue(ok)
        self.assertIsNone(err)


class TestComparePositions(unittest.TestCase):
    """Тесты для функции compare_positions."""

    def test_identical_positions(self):
        """Идентичные позиции должны проходить проверку."""
        py_agents = [{"id": 1, "x": 100.0, "y": 200.0}]
        cpp_agents = [{"id": 1, "pos": [100.0, 200.0]}]
        errors = compare_positions(py_agents, cpp_agents, 1e-3)
        self.assertEqual(len(errors), 0)

    def test_different_ids(self):
        """Разные ID агентов должны вызывать ошибку."""
        py_agents = [{"id": 1, "x": 100.0, "y": 200.0}]
        cpp_agents = [{"id": 2, "pos": [100.0, 200.0]}]
        errors = compare_positions(py_agents, cpp_agents, 1e-3)
        self.assertTrue(any("Агенты только в" in e for e in errors))

    def test_position_within_tolerance(self):
        """Позиции в пределах допуска должны проходить проверку."""
        py_agents = [{"id": 1, "x": 100.0, "y": 200.0}]
        cpp_agents = [{"id": 1, "pos": [100.0001, 200.0001]}]
        errors = compare_positions(py_agents, cpp_agents, 1e-3)
        self.assertEqual(len(errors), 0)

    def test_position_outside_tolerance(self):
        """Позиции вне допуска должны вызывать ошибку."""
        py_agents = [{"id": 1, "x": 100.0, "y": 200.0}]
        cpp_agents = [{"id": 1, "pos": [101.0, 201.0]}]
        errors = compare_positions(py_agents, cpp_agents, 1e-3)
        self.assertTrue(len(errors) > 0)


class TestCompareScalarValues(unittest.TestCase):
    """Тесты для функции compare_scalar_values."""

    def test_identical_data(self):
        """Идентичные данные должны проходить проверку."""
        py_data = {
            "agent_count": 10,
            "births": 5,
            "deaths": 2,
            "avg_generation": 1.5,
            "food_count": 50,
        }
        cpp_data = {
            "agents": [{"id": i, "generation": 1.5} for i in range(10)],
            "births": 5,
            "deaths": 2,
            "foods": [{"eaten": False} for _ in range(50)],
        }
        errors = compare_scalar_values(py_data, cpp_data, 1e-3)
        self.assertEqual(len(errors), 0)

    def test_different_agent_count(self):
        """Разное число агентов должно вызывать ошибку."""
        py_data = {"agent_count": 10}
        cpp_data = {"agents": [{"id": i} for i in range(5)]}
        errors = compare_scalar_values(py_data, cpp_data, 1e-3)
        self.assertTrue(any("agent_count" in e for e in errors))

    def test_different_births(self):
        """Разное число рождений должно вызывать ошибку."""
        py_data = {"agent_count": 5, "births": 10}
        cpp_data = {"agents": [{"id": i} for i in range(5)], "births": 5}
        errors = compare_scalar_values(py_data, cpp_data, 1e-3)
        self.assertTrue(any("births" in e for e in errors))


class TestCompareAgentProperties(unittest.TestCase):
    """Тесты для функции compare_agent_properties."""

    def test_identical_energy(self):
        """Идентичная энергия должна проходить проверку."""
        py_agents = [{"id": 1, "energy": 50.0}]
        cpp_agents = [{"id": 1, "energy": 50.0}]
        errors = compare_agent_properties(py_agents, cpp_agents, 1e-3)
        self.assertEqual(len(errors), 0)

    def test_missing_hormones_in_cpp(self):
        """Отсутствие гормонов в C++ не должно вызывать ошибку."""
        py_agents = [{"id": 1, "energy": 50.0, "hormones": {"D": 0.5}}]
        cpp_agents = [{"id": 1, "energy": 50.0}]
        errors = compare_agent_properties(py_agents, cpp_agents, 1e-3)
        self.assertEqual(len(errors), 0)

    def test_different_energy(self):
        """Разная энергия должна вызывать ошибку."""
        py_agents = [{"id": 1, "energy": 50.0}]
        cpp_agents = [{"id": 1, "energy": 40.0}]
        errors = compare_agent_properties(py_agents, cpp_agents, 1e-3)
        self.assertTrue(any("energy" in e for e in errors))


class TestLoadJson(unittest.TestCase):
    """Тесты для функции load_json."""

    def test_load_valid_json(self):
        """Загрузка валичного JSON файла."""
        data = {"test": 123}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name
        try:
            loaded = load_json(temp_path)
            self.assertEqual(loaded, data)
        finally:
            os.unlink(temp_path)

    def test_load_invalid_json(self):
        """Загрузка неваличного JSON файла должна вызывать ошибку."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid json}")
            temp_path = f.name
        try:
            with self.assertRaises(json.JSONDecodeError):
                load_json(temp_path)
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
