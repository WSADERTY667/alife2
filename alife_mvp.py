# alife_mvp.py
# MVP-прототип 2D artificial life game в духе Creatures.
# Архитектура: SNN + R-STDP + genome + hormones + social dynamics.

import pygame
import random
import math
import numpy as np


# =====================================================================
# 1. CONFIG
# =====================================================================

WORLD_W = 1000
WORLD_H = 640
PANEL_H = 190
SCREEN_W = WORLD_W
SCREEN_H = WORLD_H + PANEL_H
FPS = 60

# Количество скрытых нейронов в мозге одного существа.
# Для 10_000_000 этот прототип не предназначен.
# Если поставить слишком много, будет тормозить или упасть память.
N_HIDDEN = 160

INPUT_SIZE = 12
OUTPUT_SIZE = 6
TOTAL_NEURONS = INPUT_SIZE + N_HIDDEN + OUTPUT_SIZE

# Пластичность оставляем только для небольших сетей,
# иначе dense outer products станут слишком тяжёлыми.
LEARNING = TOTAL_NEURONS <= 1200

AGENT_COUNT = 24
MIN_AGENTS = 6
FOOD_MAX = 90
FOOD_RESPAWN = 0.22

MAX_ENERGY = 100.0
START_ENERGY = 70.0
REPRO_ENERGY = 78.0
REPRO_COST = 28.0
REPRO_BASE = 0.035
REPRODUCE_COOLDOWN = 900
MATURE_AGE = 500
MAX_AGE = 26000

SENSE_RANGE = 230.0
SOCIAL_RANGE = 85.0
MATE_RANGE = 55.0
EAT_RANGE = 18.0
ATTACK_RANGE = 24.0

TURN_RATE = 0.38
MAX_SPEED = 2.2
AGENT_RADIUS = 6

EAT_THRESHOLD = 0.35
ATTACK_THRESHOLD = 0.45

ATTACK_DAMAGE = 12.0
ATTACK_COST = 3.0

SYNAPTIC_SCALE = 0.085
REFLEX_ASSIST = True
LAMARCKIAN = True

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
    if v < lo:
        return float(lo)
    if v > hi:
        return float(hi)
    return float(v)


def normalize_angle(a):
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def wall_front_sensor(pos, angle):
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


# =====================================================================
# 2. GENOME
# =====================================================================

GENOME_KEYS = [
    "mutation_rate",
    "conn_prob",
    "weight_scale",
    "weight_max",
    "membrane_decay",
    "threshold",
    "stdp_rate",
    "plasticity_gain",

    "dopamine_base",
    "dopamine_reactivity",

    "serotonin_base",
    "serotonin_decay",

    "oxytocin_base",
    "oxytocin_gain",

    "cortisol_base",
    "cortisol_reactivity",
    "cortisol_decay",

    "testosterone_base",
    "testosterone_reactivity",

    "aggression_gain",
    "social_gain",
    "lamarckian_weight",
    "metabolism",
]

BOUNDS = {
    "mutation_rate": (0.001, 0.30),
    "conn_prob": (0.02, 0.25),
    "weight_scale": (0.05, 1.5),
    "weight_max": (0.5, 3.0),
    "membrane_decay": (0.70, 0.98),
    "threshold": (0.5, 1.8),
    "stdp_rate": (0.0005, 0.05),
    "plasticity_gain": (0.1, 2.5),

    "dopamine_base": (0.2, 1.0),
    "dopamine_reactivity": (0.1, 2.0),

    "serotonin_base": (0.2, 1.0),
    "serotonin_decay": (0.01, 0.20),

    "oxytocin_base": (0.1, 0.8),
    "oxytocin_gain": (0.1, 2.0),

    "cortisol_base": (0.05, 0.6),
    "cortisol_reactivity": (0.1, 2.0),
    "cortisol_decay": (0.01, 0.30),

    "testosterone_base": (0.1, 1.0),
    "testosterone_reactivity": (0.1, 2.0),

    "aggression_gain": (0.0, 2.0),
    "social_gain": (0.0, 2.0),
    "lamarckian_weight": (0.0, 0.9),
    "metabolism": (0.01, 0.10),
}

MUT_SCALE = {
    k: max(1e-5, (BOUNDS[k][1] - BOUNDS[k][0]) * 0.08)
    for k in GENOME_KEYS
}

KIN_KEYS = [
    "conn_prob",
    "threshold",
    "dopamine_base",
    "serotonin_base",
    "oxytocin_gain",
    "cortisol_decay",
    "aggression_gain",
    "social_gain",
]


class Genome:
    def __init__(self, genes=None, tag=None):
        if genes is None:
            genes = {
                k: random.uniform(BOUNDS[k][0], BOUNDS[k][1])
                for k in GENOME_KEYS
            }
        self.genes = genes
        if tag is None:
            self.tag = random.randint(0, len(TAG_COLORS) - 1)
        else:
            self.tag = tag

    def __getitem__(self, key):
        return self.genes[key]

    def mutate(self):
        mr = clamp(self.genes.get("mutation_rate", 0.08), 0.0, 0.5)

        for k in GENOME_KEYS:
            if random.random() < mr:
                self.genes[k] = clamp(
                    self.genes[k] + random.gauss(0.0, MUT_SCALE[k]),
                    BOUNDS[k][0],
                    BOUNDS[k][1],
                )

        if random.random() < mr * 0.35:
            self.tag = random.randint(0, len(TAG_COLORS) - 1)

    @staticmethod
    def crossover(a, b):
        genes = {}

        for k in GENOME_KEYS:
            r = random.random()
            if r < 0.45:
                v = a[k]
            elif r < 0.90:
                v = b[k]
            else:
                v = (a[k] + b[k]) * 0.5

            genes[k] = v

        tag = a.tag if random.random() < 0.5 else b.tag
        return Genome(genes, tag)


def genome_similarity(g1, g2):
    total = 0.0
    for k in KIN_KEYS:
        lo, hi = BOUNDS[k]
        rng = max(1e-6, hi - lo)
        total += abs(g1[k] - g2[k]) / rng

    gene_sim = 1.0 - clamp(total / len(KIN_KEYS), 0.0, 1.0)
    tag_sim = 1.0 if g1.tag == g2.tag else 0.0
    return clamp(0.7 * gene_sim + 0.3 * tag_sim, 0.0, 1.0)


# =====================================================================
# 3. HORMONES
# =====================================================================

class Hormones:
    def __init__(self, genome):
        self.D = genome["dopamine_base"]
        self.S = genome["serotonin_base"]
        self.O = genome["oxytocin_base"]
        self.C = genome["cortisol_base"]
        self.T = genome["testosterone_base"]

        self.allostatic = 0.0
        self.depression = 0.0
        self.breakdown = 0.0

    def update(self, dt, events, genome):
        reward = events.get("reward", 0.0)
        punishment = events.get("punishment", 0.0)
        social = events.get("social", 0.0)
        kin = events.get("kin", 0.0)
        conflict = events.get("conflict", 0.0)
        dominance = events.get("dominance", 0.0)
        hunger = events.get("hunger", 0.0)
        injury = events.get("injury", 0.0)
        fear = events.get("fear", 0.0)

        # Dopamine: reward prediction / motivation signal.
        self.D += (
            genome["dopamine_reactivity"] * (reward - punishment) * 0.25
            + 0.02 * (genome["dopamine_base"] - self.D)
        )
        self.D = clamp(self.D, 0.0, 2.0)

        # Cortisol: stress.
        stress = (
            punishment * 1.0
            + conflict * 0.6
            + hunger * 0.35
            + injury * 0.9
            + fear * 0.8
        )
        self.C += (
            genome["cortisol_reactivity"] * stress * 0.12
            - genome["cortisol_decay"] * (self.C - genome["cortisol_base"])
        )
        self.C = clamp(self.C, 0.0, 2.0)

        # Serotonin: mood stability, suppressed by high cortisol.
        self.S += (
            genome["serotonin_decay"] * (genome["serotonin_base"] - self.S)
            + reward * 0.03
            - max(0.0, self.C - 0.8) * 0.05
        )
        self.S = clamp(self.S, 0.0, 2.0)

        # Oxytocin: social bonding, kin trust.
        self.O += (
            genome["oxytocin_gain"] * (social * 0.06 + kin * 0.08)
            - 0.05 * (self.O - genome["oxytocin_base"])
        )
        self.O = clamp(self.O, 0.0, 2.0)

        # Testosterone: aggression/dominance.
        self.T += (
            genome["testosterone_reactivity"] * (conflict * 0.08 + dominance * 0.05)
            - 0.04 * (self.T - genome["testosterone_base"])
        )
        self.T = clamp(self.T, 0.0, 2.0)

        # Allostatic load: chronic stress accumulation.
        if self.C > 0.85:
            self.allostatic += (self.C - 0.85) * 0.03
        else:
            self.allostatic = max(0.0, self.allostatic - 0.004)

        if self.allostatic > 1.8:
            self.breakdown = 1.0
        else:
            self.breakdown = max(0.0, self.breakdown - 0.006)

        # Depression-like state.
        if self.S < 0.30 and self.D < 0.35:
            self.depression = min(1.0, self.depression + 0.004)
        else:
            self.depression = max(0.0, self.depression - 0.002)

    def effects(self, genome, hunger=0.0):
        dopamine_error = self.D - genome["dopamine_base"]

        arousal = clamp(
            0.15
            + self.C * 0.55
            + self.T * 0.25
            - self.S * 0.15
            + hunger * 0.20,
            -0.5,
            1.5,
        )

        plasticity = genome["plasticity_gain"] * (
            0.15 + max(0.0, dopamine_error) * 1.8
        ) * (1.0 - min(0.75, self.C * 0.35))

        if self.depression > 0.5:
            plasticity *= 0.45
        if self.breakdown > 0.5:
            plasticity *= 0.20

        aggression = genome["aggression_gain"] * (
            self.T * 0.55
            + self.C * 0.35
            - self.S * 0.25
            + hunger * 0.20
        )

        sociality = genome["social_gain"] * (
            self.O * 0.85
            + self.S * 0.10
            - self.C * 0.20
        )

        dopamine_signal = clamp(dopamine_error * 1.5, -1.0, 1.0)

        return {
            "arousal": clamp(arousal, -1.0, 2.0),
            "plasticity": clamp(plasticity, 0.0, 3.0),
            "aggression": clamp(aggression, 0.0, 3.0),
            "sociality": clamp(sociality, 0.0, 3.0),
            "dopamine_signal": dopamine_signal,
            "depression": self.depression,
            "breakdown": self.breakdown,
        }

    def get_mood(self):
        """Определяет текущее настроение на основе гормонального профиля."""
        # Сначала проверяем критические состояния
        if self.breakdown > 0.5:
            return "ярость"
        
        if self.depression > 0.5:
            return "грусть"
        
        # Очень низкие все гормоны или диссоциация = отрешённость (проверяем до скуки)
        if self.D < 0.3 and self.S < 0.3 and self.O < 0.3:
            return "отрешённость"
        
        # Высокий кортизол + отстранённость = отрешённость
        if self.C > 0.8 and self.S < 0.4:
            return "отрешённость"
        
        # Высокий дофамин + высокий серотонин = радость
        if self.D > 0.7 and self.S > 0.6:
            return "радость"
        
        # Низкий дофамин + низкий кортизол + низкий тестостерон = скука
        if self.D < 0.4 and self.C < 0.4 and self.T < 0.4:
            return "скука"
        
        # Высокий кортизол + высокий тестостерон + низкий серотонин = ярость
        if self.C > 0.7 and self.T > 0.6 and self.S < 0.5:
            return "ярость"
        
        return "нормальное"


# =====================================================================
# 4. SPIKING NEURAL NETWORK BRAIN
# =====================================================================

class Brain:
    def __init__(self, genome, n_hidden, parent_weights=None):
        self.n_hidden = n_hidden
        self.n_in = INPUT_SIZE
        self.n_out = OUTPUT_SIZE
        self.n = self.n_in + self.n_hidden + self.n_out
        self.hidden_slice = slice(self.n_in, self.n)

        self.v = np.zeros(self.n, dtype=np.float32)
        self.spikes = np.zeros(self.n, dtype=np.float32)
        self.out_rate = np.zeros(self.n_out, dtype=np.float32)

        rng = np.random.default_rng()

        # Sparse-ish random connectivity, but still dense matrix in MVP.
        self.mask = rng.random((self.n, self.n)) < genome["conn_prob"]
        np.fill_diagonal(self.mask, False)

        # Гарантируем, что входы и выходы не останутся полностью изолированными.
        in_mask = rng.random((self.n_in, self.n)) < max(genome["conn_prob"], 0.12)
        self.mask[:self.n_in, :] |= in_mask

        out_mask = rng.random((self.n, self.n_out)) < max(genome["conn_prob"], 0.15)
        self.mask[:, -self.n_out:] |= out_mask

        np.fill_diagonal(self.mask, False)

        self.W = (
            rng.normal(0.0, genome["weight_scale"], (self.n, self.n)).astype(np.float32)
            * self.mask
        )

        # Lamarckian inheritance: partially copy learned parent weights.
        if parent_weights is not None and parent_weights.shape == self.W.shape:
            lam = clamp(genome["lamarckian_weight"], 0.0, 1.0)
            self.W = ((1.0 - lam) * self.W + lam * parent_weights).astype(np.float32)
            self.W *= self.mask

        self.decay_base = genome["membrane_decay"]
        self.threshold_base = genome["threshold"]
        self.stdp_rate = genome["stdp_rate"]
        self.max_w = genome["weight_max"]

        if LEARNING:
            self.E = np.zeros((self.n, self.n), dtype=np.float32)
        else:
            self.E = None

    def step(self, sensors, mod):
        sensors = np.asarray(sensors, dtype=np.float32)
        pre = self.spikes

        # Synaptic current from previous spikes.
        current = pre @ self.W

        arousal = mod.get("arousal", 0.0)
        decay = clamp(self.decay_base + arousal * 0.02, 0.50, 0.99)
        threshold = clamp(self.threshold_base - arousal * 0.05, 0.30, 2.0)

        # Membrane update.
        self.v = self.v * decay + current * SYNAPTIC_SCALE

        # High stress adds neural noise.
        if arousal > 0.8:
            noise_size = self.n - INPUT_SIZE
            noise = np.random.normal(
                0.0,
                (arousal - 0.8) * 0.02,
                noise_size,
            ).astype(np.float32)
            self.v[INPUT_SIZE:] += noise

        new_spikes = np.zeros(self.n, dtype=np.float32)

        hidden_v = self.v[self.hidden_slice]
        fired = hidden_v >= threshold
        new_spikes[self.hidden_slice] = fired.astype(np.float32)
        hidden_v[fired] = 0.0

        # Input layer is rate-coded from sensors.
        new_spikes[:INPUT_SIZE] = np.clip(sensors, 0.0, 1.0)

        # Output motor rates.
        self.out_rate = 0.75 * self.out_rate + 0.25 * new_spikes[-self.n_out:]

        # Reward-modulated STDP.
        if LEARNING and self.E is not None:
            learn_rate = clamp(
                mod.get("plasticity", 0.0) * mod.get("dopamine", 0.0),
                -2.0,
                2.0,
            )

            if abs(learn_rate) > 1e-6:
                post = new_spikes
                delta = (
                    np.outer(pre, post) - np.outer(post, pre)
                ).astype(np.float32)

                self.E = self.E * 0.95 + delta * self.stdp_rate
                self.W += learn_rate * self.E * self.mask
                self.W = np.clip(self.W, -self.max_w, self.max_w)
                self.W *= self.mask

        self.spikes = new_spikes
        return self.out_rate


# =====================================================================
# 5. AGENT
# =====================================================================

class Agent:
    next_id = 1

    def __init__(self, pos, genome, generation=0, parent_weights=None):
        self.id = Agent.next_id
        Agent.next_id += 1

        self.pos = np.array(pos, dtype=np.float32)
        self.angle = random.uniform(-math.pi, math.pi)

        self.genome = genome
        self.brain = Brain(genome, N_HIDDEN, parent_weights)
        self.hormones = Hormones(genome)

        self.energy = START_ENERGY
        self.age = 0.0
        self.generation = generation
        self.alive = True

        self.repro_cooldown = REPRODUCE_COOLDOWN * random.uniform(0.3, 0.8)

        self.last_pain = 0.0
        self.pending_reward = 0.0
        self.pending_punishment = 0.0

        self.nearest_food = None
        self.nearest_agent = None

    def can_reproduce(self):
        return (
            self.alive
            and self.age > MATURE_AGE
            and self.energy > REPRO_ENERGY
            and self.repro_cooldown <= 0.0
            and self.hormones.depression < 0.85
        )

    def make_sensors(self):
        sensors = np.zeros(INPUT_SIZE, dtype=np.float32)
        hunger = 1.0 - clamp(self.energy / MAX_ENERGY, 0.0, 1.0)

        sensors[0] = hunger

        if self.nearest_food is not None:
            dist, abs_angle, food = self.nearest_food
            if dist < SENSE_RANGE and not food["eaten"]:
                rel = normalize_angle(abs_angle - self.angle)
                prox = 1.0 - dist / SENSE_RANGE

                sensors[1] = prox

                if rel < 0.0:
                    sensors[2] = min(1.0, -rel / math.pi)
                else:
                    sensors[3] = min(1.0, rel / math.pi)

        if self.nearest_agent is not None:
            dist, abs_angle, other, kin_sim = self.nearest_agent
            if dist < SENSE_RANGE and other.alive:
                rel = normalize_angle(abs_angle - self.angle)
                prox = 1.0 - dist / SENSE_RANGE

                sensors[4] = prox

                if rel < 0.0:
                    sensors[5] = min(1.0, -rel / math.pi)
                else:
                    sensors[6] = min(1.0, rel / math.pi)

                sensors[7] = kin_sim * prox

                if dist < SOCIAL_RANGE:
                    sensors[11] = 1.0

        sensors[8] = wall_front_sensor(self.pos, self.angle)
        sensors[9] = clamp(self.last_pain, 0.0, 1.0)
        sensors[10] = clamp(self.hormones.C / 2.0, 0.0, 1.0)

        return sensors

    def bounce(self):
        r = AGENT_RADIUS

        if self.pos[0] < r:
            self.pos[0] = r
            self.angle = math.pi - self.angle
        elif self.pos[0] > WORLD_W - r:
            self.pos[0] = WORLD_W - r
            self.angle = math.pi - self.angle

        if self.pos[1] < r:
            self.pos[1] = r
            self.angle = -self.angle
        elif self.pos[1] > WORLD_H - r:
            self.pos[1] = WORLD_H - r
            self.angle = -self.angle

        self.angle = normalize_angle(self.angle)

    def make_child(self, mate):
        child_genome = Genome.crossover(self.genome, mate.genome)
        child_genome.mutate()

        parent_weights = None
        if LAMARCKIAN and self.brain.W.shape == mate.brain.W.shape:
            parent_weights = ((self.brain.W + mate.brain.W) * 0.5).astype(np.float32)

        pos = (self.pos + mate.pos) * 0.5
        pos += np.array(
            [random.uniform(-12.0, 12.0), random.uniform(-12.0, 12.0)],
            dtype=np.float32,
        )
        pos[0] = clamp(pos[0], AGENT_RADIUS, WORLD_W - AGENT_RADIUS)
        pos[1] = clamp(pos[1], AGENT_RADIUS, WORLD_H - AGENT_RADIUS)

        generation = max(self.generation, mate.generation) + 1
        return Agent(pos, child_genome, generation, parent_weights)

    def update(self, world, dt=1.0):
        self.age += dt
        self.repro_cooldown -= dt
        self.energy -= self.genome["metabolism"] * dt
        self.last_pain *= 0.92

        hunger = 1.0 - clamp(self.energy / MAX_ENERGY, 0.0, 1.0)
        sensors = self.make_sensors()

        eff = self.hormones.effects(self.genome, hunger)
        neuromod = {
            "plasticity": eff["plasticity"],
            "dopamine": eff["dopamine_signal"],
            "arousal": eff["arousal"],
        }

        out = self.brain.step(sensors, neuromod)

        left, right, forward, backward, eat, attack = [
            clamp(float(x), 0.0, 1.0) for x in out
        ]

        reflex_turn = 0.0
        reflex_forward = 0.0
        reflex_eat = 0.0

        # Innate reflex assist, чтобы мир не был полностью парализован
        # на этапе случайной инициализации мозга.
        if REFLEX_ASSIST:
            if sensors[8] > 0.70:
                reflex_turn += 0.22 * (1.0 if random.random() < 0.5 else -1.0)

            food_prox = sensors[1]
            if hunger > 0.35 and food_prox > 0.05:
                reflex_turn += 0.22 * (sensors[3] - sensors[2])
                reflex_forward += 0.15 * food_prox
                if food_prox > 0.8:
                    reflex_eat += 0.5

            if hunger > 0.6:
                reflex_forward += 0.05

        turn = (left - right) * TURN_RATE * dt + reflex_turn * dt

        if eff["breakdown"] > 0.5:
            turn += random.uniform(-0.5, 0.5) * dt
            forward = clamp(forward + random.uniform(-0.2, 0.5), 0.0, 1.0)
            attack = clamp(attack + random.uniform(0.0, 0.4), 0.0, 1.0)

        if eff["depression"] > 0.5:
            forward *= 0.45
            eat *= 0.55
            attack *= 0.5
            reflex_forward *= 0.3

        move_power = forward - backward + reflex_forward
        move_power *= 0.4 + 0.6 * clamp(self.energy / MAX_ENERGY, 0.0, 1.0)

        if eff["depression"] > 0.5:
            move_power *= 0.55

        self.angle += turn
        self.pos[0] += math.cos(self.angle) * move_power * MAX_SPEED * dt
        self.pos[1] += math.sin(self.angle) * move_power * MAX_SPEED * dt
        self.bounce()

        events = {
            "reward": self.pending_reward,
            "punishment": self.pending_punishment,
            "social": 0.0,
            "kin": 0.0,
            "conflict": 0.0,
            "dominance": 0.0,
            "hunger": hunger,
            "injury": self.last_pain,
            "fear": 0.0,
        }

        self.pending_reward = 0.0
        self.pending_punishment = 0.0

        # Social contact.
        na = self.nearest_agent
        if na is not None:
            dist, abs_angle, other, kin_sim = na
            if dist < SOCIAL_RANGE and other.alive:
                events["social"] = 1.0
                events["kin"] = kin_sim

                if eff["sociality"] > 0.6:
                    events["reward"] += 0.015 + 0.04 * kin_sim * eff["sociality"]

                if other.hormones.breakdown > 0.5:
                    events["fear"] += 0.4
                    events["punishment"] += 0.02

        # Eating.
        nf = self.nearest_food
        if nf is not None:
            dist, abs_angle, food = nf
            if not food["eaten"] and dist < EAT_RANGE:
                eat_drive = eat + reflex_eat
                if eat_drive > EAT_THRESHOLD:
                    food["eaten"] = True
                    self.energy = min(MAX_ENERGY, self.energy + food["nutrition"])
                    events["reward"] += 1.0

        # Attack / conflict.
        if na is not None:
            dist, abs_angle, other, kin_sim = na
            if dist < ATTACK_RANGE and other.alive:
                attack_drive = attack * eff["aggression"]

                if REFLEX_ASSIST and hunger > 0.8:
                    attack_drive += 0.05

                if eff["breakdown"] > 0.5:
                    attack_drive += random.uniform(0.0, 0.3)

                # Oxytocin/sociality/kinship suppress attack.
                attack_drive *= 1.0 - clamp(0.65 * kin_sim * eff["sociality"], 0.0, 0.9)

                if attack_drive > ATTACK_THRESHOLD:
                    other.energy -= ATTACK_DAMAGE
                    other.last_pain = 1.0
                    other.pending_punishment += 0.8
                    other.hormones.C = clamp(other.hormones.C + 0.12, 0.0, 2.0)

                    self.energy -= ATTACK_COST

                    events["conflict"] = 1.0

                    if other.energy < self.energy:
                        events["dominance"] = 1.0
                        if self.genome["aggression_gain"] > 0.8:
                            events["reward"] += 0.12
                    else:
                        events["punishment"] += 0.05

        # Extra energy drain during breakdown.
        if eff["breakdown"] > 0.5:
            self.energy -= 0.05 * dt

        self.hormones.update(dt, events, self.genome)

        if self.energy <= 0.0 or self.age > MAX_AGE:
            self.alive = False
            return

        # Reproduction.
        if self.can_reproduce() and na is not None:
            dist, abs_angle, mate, kin_sim = na
            if dist < MATE_RANGE and mate.can_reproduce():
                compat = 0.35 + 0.65 * kin_sim
                mate_social = clamp(mate.hormones.O, 0.0, 1.0)

                chance = (
                    REPRO_BASE
                    * eff["sociality"]
                    * compat
                    * (0.3 + mate_social)
                )

                if random.random() < chance:
                    child = self.make_child(mate)
                    world.newborns.append(child)

                    self.energy -= REPRO_COST
                    mate.energy -= REPRO_COST

                    self.repro_cooldown = REPRODUCE_COOLDOWN
                    mate.repro_cooldown = REPRODUCE_COOLDOWN


# =====================================================================
# 6. WORLD
# =====================================================================

class World:
    def __init__(self):
        self.agents = []
        self.foods = []
        self.tick = 0
        self.newborns = []

        for _ in range(FOOD_MAX):
            self.spawn_food()

        for _ in range(AGENT_COUNT):
            self.spawn_random_agent()

    def spawn_food(self):
        pos = np.array(
            [
                random.uniform(10.0, WORLD_W - 10.0),
                random.uniform(10.0, WORLD_H - 10.0),
            ],
            dtype=np.float32,
        )
        self.foods.append(
            {
                "pos": pos,
                "nutrition": random.uniform(18.0, 30.0),
                "eaten": False,
            }
        )

    def spawn_random_agent(self):
        genome = Genome()
        genome.mutate()
        pos = np.array(
            [
                random.uniform(30.0, WORLD_W - 30.0),
                random.uniform(30.0, WORLD_H - 30.0),
            ],
            dtype=np.float32,
        )
        self.agents.append(Agent(pos, genome, 0, None))

    def find_nearest_food(self, pos):
        best = None
        best_d = 1e18

        for f in self.foods:
            if f["eaten"]:
                continue

            d = float(np.linalg.norm(f["pos"] - pos))
            if d < best_d:
                best_d = d
                best = f

        if best is None:
            return None

        angle = math.atan2(best["pos"][1] - pos[1], best["pos"][0] - pos[0])
        return best_d, angle, best

    def find_nearest_agent(self, agent):
        best = None
        best_d = 1e18

        for b in self.agents:
            if b is agent or not b.alive:
                continue

            d = float(np.linalg.norm(b.pos - agent.pos))
            if d < best_d:
                best_d = d
                best = b

        if best is None:
            return None

        angle = math.atan2(best.pos[1] - agent.pos[1], best.pos[0] - agent.pos[0])
        kin_sim = genome_similarity(agent.genome, best.genome)
        return best_d, angle, best, kin_sim

    def update(self):
        self.tick += 1
        self.newborns = []

        if len(self.foods) < FOOD_MAX and random.random() < FOOD_RESPAWN:
            self.spawn_food()

        for a in self.agents:
            a.nearest_food = self.find_nearest_food(a.pos)
            a.nearest_agent = self.find_nearest_agent(a)

        for a in self.agents:
            if a.alive:
                a.update(self, 1.0)

        self.foods = [f for f in self.foods if not f["eaten"]]

        self.agents.extend(self.newborns)
        self.agents = [a for a in self.agents if a.alive]

        if len(self.agents) < MIN_AGENTS:
            for _ in range(MIN_AGENTS - len(self.agents)):
                self.spawn_random_agent()


# =====================================================================
# 7. RENDERING
# =====================================================================

def draw_text(screen, font, x, y, text, color=(220, 220, 220)):
    screen.blit(font.render(text, True, color), (x, y))


def draw_panel(screen, world, font, selected):
    panel_rect = pygame.Rect(0, WORLD_H, SCREEN_W, PANEL_H)
    pygame.draw.rect(screen, (16, 18, 24), panel_rect)
    pygame.draw.line(screen, (50, 55, 70), (0, WORLD_H), (SCREEN_W, WORLD_H), 2)

    avg_gen = 0.0
    if world.agents:
        avg_gen = sum(a.generation for a in world.agents) / len(world.agents)

    y = WORLD_H + 8
    draw_text(
        screen,
        font,
        10,
        y,
        f"Tick: {world.tick}  Agents: {len(world.agents)}  Food: {len(world.foods)}  Avg gen: {avg_gen:.1f}",
    )
    y += 18
    draw_text(
        screen,
        font,
        10,
        y,
        "Keys: Space pause, F food, A agent, R reset, +/- speed, Click select, T reward, P punish",
        (170, 180, 200),
    )
    y += 24

    if selected is None:
        draw_text(screen, font, 10, y, "No agent selected.", (150, 150, 160))
        return

    h = selected.hormones
    color = TAG_COLORS[selected.genome.tag % len(TAG_COLORS)]

    draw_text(
        screen,
        font,
        10,
        y,
        f"Agent {selected.id}  gen {selected.generation}  age {int(selected.age)}  energy {selected.energy:.0f}",
        color,
    )
    y += 18

    draw_text(
        screen,
        font,
        10,
        y,
        f"D {h.D:.2f}  S {h.S:.2f}  O {h.O:.2f}  C {h.C:.2f}  T {h.T:.2f}",
    )
    y += 18

    mood = h.get_mood()

    draw_text(
        screen,
        font,
        10,
        y,
        f"настроение: {mood}  аллостаз: {h.allostatic:.2f}  депрессия: {h.depression:.2f}",
    )
    y += 18

    draw_text(
        screen,
        font,
        10,
        y,
        f"tribe tag: {selected.genome.tag}  aggression: {h.effects(selected.genome)['aggression']:.2f}  sociality: {h.effects(selected.genome)['sociality']:.2f}",
        (170, 190, 220),
    )


def draw(screen, world, font, selected):
    screen.fill((8, 10, 14))

    for f in world.foods:
        if not f["eaten"]:
            pygame.draw.circle(
                screen,
                (70, 220, 120),
                (int(f["pos"][0]), int(f["pos"][1])),
                3,
            )

    for a in world.agents:
        base_color = TAG_COLORS[a.genome.tag % len(TAG_COLORS)]

        if a.hormones.breakdown > 0.5:
            body_color = (255, 70, 70)
        elif a.hormones.depression > 0.5:
            body_color = (90, 95, 120)
        else:
            body_color = base_color

        r = int(AGENT_RADIUS + 4.0 * clamp(a.energy / MAX_ENERGY, 0.0, 1.0))
        pos = (int(a.pos[0]), int(a.pos[1]))

        pygame.draw.circle(screen, body_color, pos, r)
        pygame.draw.circle(screen, (210, 220, 255), pos, r, 1)

        end_x = int(a.pos[0] + math.cos(a.angle) * (r + 6))
        end_y = int(a.pos[1] + math.sin(a.angle) * (r + 6))
        pygame.draw.line(screen, (220, 220, 220), pos, (end_x, end_y), 1)

        if selected is not None and selected.id == a.id:
            pygame.draw.circle(screen, (255, 255, 120), pos, r + 4, 2)

    draw_panel(screen, world, font, selected)


# =====================================================================
# 8. MAIN LOOP
# =====================================================================

def get_agent_by_id(world, agent_id):
    if agent_id is None:
        return None
    for a in world.agents:
        if a.id == agent_id:
            return a
    return None


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("ALife MVP: SNN + Genome + Hormones")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas,monospace", 14)

    world = World()
    selected_id = None

    paused = False
    sim_speed = 1
    running = True

    print("ALife MVP started.")
    print("Space: pause | F: food | A: agent | R: reset | +/-: speed")
    print("Click agent, then T = reward, P = punish.")

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    paused = not paused

                elif event.key == pygame.K_f:
                    for _ in range(10):
                        world.spawn_food()

                elif event.key == pygame.K_a:
                    world.spawn_random_agent()

                elif event.key == pygame.K_r:
                    world = World()
                    selected_id = None

                elif event.key in (pygame.K_EQUALS, pygame.K_KP_PLUS):
                    sim_speed = min(8, sim_speed + 1)

                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    sim_speed = max(1, sim_speed - 1)

                elif event.key in (pygame.K_t, pygame.K_p):
                    sel = get_agent_by_id(world, selected_id)
                    if sel is not None:
                        if event.key == pygame.K_t:
                            sel.pending_reward += 1.0
                        elif event.key == pygame.K_p:
                            sel.pending_punishment += 1.0
                            sel.last_pain = max(sel.last_pain, 0.5)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if my < WORLD_H:
                    mouse_pos = np.array([mx, my], dtype=np.float32)
                    best = None
                    best_d = 18.0

                    for a in world.agents:
                        d = float(np.linalg.norm(a.pos - mouse_pos))
                        if d < best_d:
                            best_d = d
                            best = a

                    selected_id = best.id if best is not None else None

        if not paused:
            for _ in range(sim_speed):
                world.update()

        selected = get_agent_by_id(world, selected_id)

        draw(screen, world, font, selected)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
