# agent.py
# Класс агента
import math
import random
import numpy as np
from .config import (
    START_ENERGY, MATURE_AGE, REPRODUCE_COOLDOWN, MAX_ENERGY, REPRO_ENERGY,
    SENSE_RANGE, SOCIAL_RANGE, EAT_RANGE, ATTACK_RANGE,
    TURN_RATE, MAX_SPEED, AGENT_RADIUS,
    EAT_THRESHOLD, ATTACK_THRESHOLD, ATTACK_DAMAGE, ATTACK_COST,
    REPRO_BASE, REPRO_COST, REFLEX_ASSIST, LAMARCKIAN, N_HIDDEN,
    clamp,
)
from .utils import normalize_angle, wall_front_sensor
from .genome import Genome, genome_similarity
from .hormones import Hormones
from .brain import Brain


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
        sensors = np.zeros(12, dtype=np.float32)
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
        elif self.pos[0] > 1000 - r:
            self.pos[0] = 1000 - r
            self.angle = math.pi - self.angle
        if self.pos[1] < r:
            self.pos[1] = r
            self.angle = -self.angle
        elif self.pos[1] > 640 - r:
            self.pos[1] = 640 - r
            self.angle = -self.angle
        self.angle = normalize_angle(self.angle)

    def make_child(self, mate):
        child_genome = Genome.crossover(self.genome, mate.genome)
        child_genome.mutate()
        parent_weights = None
        if LAMARCKIAN and self.brain.W.shape == mate.brain.W.shape:
            parent_weights = ((self.brain.W + mate.brain.W) * 0.5).astype(np.float32)
        pos = (self.pos + mate.pos) * 0.5
        pos += np.array([random.uniform(-12.0, 12.0), random.uniform(-12.0, 12.0)], dtype=np.float32)
        pos[0] = clamp(pos[0], AGENT_RADIUS, 1000 - AGENT_RADIUS)
        pos[1] = clamp(pos[1], AGENT_RADIUS, 640 - AGENT_RADIUS)
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
        left, right, forward, backward, eat, attack = [clamp(float(x), 0.0, 1.0) for x in out]

        reflex_turn = 0.0
        reflex_forward = 0.0
        reflex_eat = 0.0

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

        nf = self.nearest_food
        if nf is not None:
            dist, abs_angle, food = nf
            if not food["eaten"] and dist < EAT_RANGE:
                eat_drive = eat + reflex_eat
                if eat_drive > EAT_THRESHOLD:
                    food["eaten"] = True
                    self.energy = min(MAX_ENERGY, self.energy + food["nutrition"])
                    events["reward"] += 1.0

        if na is not None:
            dist, abs_angle, other, kin_sim = na
            if dist < ATTACK_RANGE and other.alive:
                attack_drive = attack * eff["aggression"]
                if REFLEX_ASSIST and hunger > 0.8:
                    attack_drive += 0.05
                if eff["breakdown"] > 0.5:
                    attack_drive += random.uniform(0.0, 0.3)
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

        if eff["breakdown"] > 0.5:
            self.energy -= 0.05 * dt

        self.hormones.update(dt, events, self.genome)

        if self.energy <= 0.0 or self.age > 26000:
            self.alive = False
            return

        if self.can_reproduce() and na is not None:
            dist, abs_angle, mate, kin_sim = na
            if dist < 55 and mate.can_reproduce():
                compat = 0.35 + 0.65 * kin_sim
                mate_social = clamp(mate.hormones.O, 0.0, 1.0)
                chance = REPRO_BASE * eff["sociality"] * compat * (0.3 + mate_social)
                if random.random() < chance:
                    child = self.make_child(mate)
                    world.newborns.append(child)
                    self.energy -= REPRO_COST
                    mate.energy -= REPRO_COST
                    self.repro_cooldown = REPRODUCE_COOLDOWN
                    mate.repro_cooldown = REPRODUCE_COOLDOWN
