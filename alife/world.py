# world.py
# Класс мира симуляции
import random
import numpy as np
from .config import WORLD_W, WORLD_H, FOOD_MAX, FOOD_RESPAWN, AGENT_COUNT, MIN_AGENTS
from .genome import Genome, genome_similarity
from .agent import Agent


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
            [random.uniform(10.0, WORLD_W - 10.0), random.uniform(10.0, WORLD_H - 10.0)],
            dtype=np.float32,
        )
        self.foods.append({
            "pos": pos,
            "nutrition": random.uniform(18.0, 30.0),
            "eaten": False,
        })

    def spawn_random_agent(self):
        genome = Genome()
        genome.mutate()
        pos = np.array(
            [random.uniform(30.0, WORLD_W - 30.0), random.uniform(30.0, WORLD_H - 30.0)],
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
        angle = np.arctan2(best["pos"][1] - pos[1], best["pos"][0] - pos[0])
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
        angle = np.arctan2(best.pos[1] - agent.pos[1], best.pos[0] - agent.pos[0])
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
