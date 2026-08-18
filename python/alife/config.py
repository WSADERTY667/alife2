# config.py
# Конфигурация и константы для ALife MVP
import math

# === Размеры мира ===
WORLD_W = 1000
WORLD_H = 640
PANEL_H = 190
SCREEN_W = WORLD_W
SCREEN_H = WORLD_H + PANEL_H
FPS = 60

# === Нейросеть ===
N_HIDDEN = 160
INPUT_SIZE = 12
OUTPUT_SIZE = 6
TOTAL_NEURONS = INPUT_SIZE + N_HIDDEN + OUTPUT_SIZE
LEARNING = TOTAL_NEURONS <= 1200
SYNAPTIC_SCALE = 0.085

# === Популяция ===
AGENT_COUNT = 24
MIN_AGENTS = 6
FOOD_MAX = 90
FOOD_RESPAWN = 0.22

# === Энергия и размножение ===
MAX_ENERGY = 100.0
START_ENERGY = 70.0
REPRO_ENERGY = 78.0
REPRO_COST = 28.0
REPRO_BASE = 0.035
REPRODUCE_COOLDOWN = 900
MATURE_AGE = 500
MAX_AGE = 26000

# === Сенсоры и движение ===
SENSE_RANGE = 230.0
SOCIAL_RANGE = 85.0
MATE_RANGE = 55.0
EAT_RANGE = 18.0
ATTACK_RANGE = 24.0
TURN_RATE = 0.38
MAX_SPEED = 2.2
AGENT_RADIUS = 6

# === Поведение ===
EAT_THRESHOLD = 0.35
ATTACK_THRESHOLD = 0.45
ATTACK_DAMAGE = 12.0
ATTACK_COST = 3.0
REFLEX_ASSIST = True
LAMARCKIAN = True

# === Цвета племен ===
TAG_COLORS = [
    (80, 170, 255),
    (255, 120, 90),
    (120, 255, 140),
    (255, 230, 90),
    (200, 120, 255),
    (120, 255, 230),
    (255, 150, 220),
    (180, 200, 255),
]


def clamp(v, lo=0.0, hi=1.0):
    # Ограничить значение диапазоном [lo, hi].
    if v < lo:
        return float(lo)
    if v > hi:
        return float(hi)
    return float(v)


def normalize_angle(a):
    # Нормализовать угол к диапазону [-pi, pi].
    return (a + math.pi) % (2.0 * math.pi) - math.pi
