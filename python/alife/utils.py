# utils.py
# Вспомогательные функции
import math
from .config import WORLD_W, WORLD_H, clamp, normalize_angle


def wall_front_sensor(pos, angle):
    # Сенсор расстояния до стены впереди агента.
    dx = math.cos(angle)
    dy = math.sin(angle)
    dists = []
    if dx > 1e-6:
        dists.append((WORLD_W - pos[0]) / dx)
    if dx < -1e-6:
        dists.append((0.0 - pos[0]) / dx)
    if dy > 1e-6:
        dists.append((WORLD_H - pos[1]) / dy)
    if dy < -1e-6:
        dists.append((0.0 - pos[1]) / dy)
    d = min(dists) if dists else 1000.0
    return clamp(1.0 - d / 120.0, 0.0, 1.0)
