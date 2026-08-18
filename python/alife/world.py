# world.py
# Класс мира симуляции
import json
import numpy as np
from pathlib import Path
from .config import WORLD_W, WORLD_H, FOOD_MAX, FOOD_RESPAWN, AGENT_COUNT, MIN_AGENTS, INPUT_SIZE, OUTPUT_SIZE
from .genome import Genome, genome_similarity
from .agent import Agent
from .hormones import Hormones
from .brain import Brain
from .rng import RNG


class World:
    SCHEMA_VERSION = 2  # Updated schema version for new genome features
    
    def __init__(self, rng=None):
        self.rng = rng if rng is not None else RNG(seed=42)
        self.agents = []
        self.foods = []
        self.tick = 0
        self.newborns = []
        # Статистика поколений
        self.generation_stats = {
            "max_generation": 0,
            "generation_counts": {},  # generation -> count of agents
            "lineage_stats": {},  # tribal_tag -> {generations, population, avg_fitness}
        }
        for _ in range(FOOD_MAX):
            self.spawn_food()
        for _ in range(AGENT_COUNT):
            self.spawn_random_agent()

    def spawn_food(self):
        pos = np.array(
            [self.rng.uniform(10.0, WORLD_W - 10.0), self.rng.uniform(10.0, WORLD_H - 10.0)],
            dtype=np.float32,
        )
        self.foods.append({
            "pos": pos,
            "nutrition": self.rng.uniform(18.0, 30.0),
            "eaten": False,
        })

    def spawn_random_agent(self):
        genome = Genome()
        genome.mutate()
        pos = np.array(
            [self.rng.uniform(30.0, WORLD_W - 30.0), self.rng.uniform(30.0, WORLD_H - 30.0)],
            dtype=np.float32,
        )
        self.agents.append(Agent(pos, genome, 0, None, rng=self.rng.copy()))

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

    def update_generation_stats(self):
        """Обновляет статистику поколений."""
        gen_counts = {}
        lineage_data = {}
        
        for agent in self.agents:
            gen = agent.generation
            gen_counts[gen] = gen_counts.get(gen, 0) + 1
            
            # Собираем данные по племенным тегам
            for tag in agent.genome.tribal_tags:
                if tag not in lineage_data:
                    lineage_data[tag] = {
                        "count": 0,
                        "total_energy": 0.0,
                        "generations": set(),
                    }
                lineage_data[tag]["count"] += 1
                lineage_data[tag]["total_energy"] += agent.energy
                lineage_data[tag]["generations"].add(gen)
        
        # Обновляем статистику
        self.generation_stats["max_generation"] = max(gen_counts.keys()) if gen_counts else 0
        self.generation_stats["generation_counts"] = gen_counts
        
        # Преобразуем множества в списки для JSON-сериализуемости
        self.generation_stats["lineage_stats"] = {
            tag: {
                "count": data["count"],
                "avg_energy": data["total_energy"] / data["count"] if data["count"] > 0 else 0.0,
                "generation_span": [min(data["generations"]), max(data["generations"])] if data["generations"] else [0, 0],
            }
            for tag, data in lineage_data.items()
        }

    def update(self):
        self.tick += 1
        self.newborns = []
        if len(self.foods) < FOOD_MAX and self.rng.next_float() < FOOD_RESPAWN:
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
        
        # Обновляем статистику поколений каждые 100 тиков
        if self.tick % 100 == 0:
            self.update_generation_stats()

    def get_generation_report(self):
        """Возвращает текстовый отчет о статистике поколений."""
        report = []
        report.append(f"=== Generation Statistics (tick {self.tick}) ===")
        report.append(f"Max generation: {self.generation_stats['max_generation']}")
        report.append("Generation distribution:")
        for gen in sorted(self.generation_stats['generation_counts'].keys()):
            count = self.generation_stats['generation_counts'][gen]
            report.append(f"  Gen {gen}: {count} agents")
        
        if self.generation_stats['lineage_stats']:
            report.append("Lineage stats:")
            for tag, data in list(self.generation_stats['lineage_stats'].items())[:5]:
                report.append(f"  Tag '{tag}': {data['count']} agents, avg energy={data['avg_energy']:.1f}, gens={data['generation_span']}")
        
        return "\n".join(report)

    def save(self, path="save_world"):
        """Сохранить мир в JSON + NPZ файлы."""
        path = Path(path)
        json_path = path.with_suffix(".json") if not path.suffix else path
        npz_path = json_path.with_suffix(".npz")
        
        # Данные для JSON
        world_data = {
            "schema_version": self.SCHEMA_VERSION,
            "tick": self.tick,
            "foods": [
                {
                    "pos": f["pos"].tolist(),
                    "nutrition": float(f["nutrition"]),
                    "eaten": f["eaten"],
                }
                for f in self.foods
            ],
            "agents": [],
            "generation_stats": self.generation_stats,
        }
        
        # Данные для NPZ (веса мозгов)
        brain_weights = {}
        
        for i, agent in enumerate(self.agents):
            agent_data = {
                "id": agent.id,
                "generation": agent.generation,
                "age": float(agent.age),
                "energy": float(agent.energy),
                "pos": agent.pos.tolist(),
                "angle": float(agent.angle),
                "repro_cooldown": float(agent.repro_cooldown),
                "last_pain": float(agent.last_pain),
                "pending_reward": float(agent.pending_reward),
                "pending_punishment": float(agent.pending_punishment),
                "alive": agent.alive,
                "genome_genes": agent.genome.genes.copy(),
                "genome_tag": agent.genome.tag,
                "genome_tribal_tags": agent.genome.tribal_tags,
                "genome_n_hidden": agent.genome.n_hidden,
                "hormones": {
                    "D": float(agent.hormones.D),
                    "S": float(agent.hormones.S),
                    "O": float(agent.hormones.O),
                    "C": float(agent.hormones.C),
                    "T": float(agent.hormones.T),
                    "allostatic": float(agent.hormones.allostatic),
                    "depression": float(agent.hormones.depression),
                    "breakdown": float(agent.hormones.breakdown),
                    "D_decay": float(agent.hormones.D_decay),
                    "S_decay": float(agent.hormones.S_decay),
                    "O_decay": float(agent.hormones.O_decay),
                    "C_decay": float(agent.hormones.C_decay),
                    "T_decay": float(agent.hormones.T_decay),
                    "S_sensitivity": float(agent.hormones.S_sensitivity),
                    "O_sensitivity": float(agent.hormones.O_sensitivity),
                    "C_sensitivity": float(agent.hormones.C_sensitivity),
                    "T_sensitivity": float(agent.hormones.T_sensitivity),
                },
                "brain_idx": i,
            }
            world_data["agents"].append(agent_data)
            
            # Сохраняем веса мозга
            brain_weights[f"agent_{i}_W"] = agent.brain.W
            
            # Дополнительные данные мозга для восстановления состояния
            brain_weights[f"agent_{i}_mask"] = agent.brain.mask.astype(np.int8)
            brain_weights[f"agent_{i}_v"] = agent.brain.v
            brain_weights[f"agent_{i}_spikes"] = agent.brain.spikes
            brain_weights[f"agent_{i}_out_rate"] = agent.brain.out_rate
            brain_weights[f"agent_{i}_E"] = agent.brain.E if agent.brain.E is not None else np.zeros(1)
            brain_weights[f"agent_{i}_n_hidden"] = agent.brain.n_hidden
        
        with open(json_path, "w") as f:
            json.dump(world_data, f, indent=2)
        
        np.savez_compressed(npz_path, **brain_weights)
        
        print(f"World saved: {json_path}, {npz_path}")
        return json_path, npz_path

    def load(self, path="save_world"):
        """Загрузить мир из JSON + NPZ файлов."""
        path = Path(path)
        json_path = path.with_suffix(".json") if not path.suffix else path
        npz_path = json_path.with_suffix(".npz")
        
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")
        if not npz_path.exists():
            raise FileNotFoundError(f"NPZ file not found: {npz_path}")
        
        with open(json_path, "r") as f:
            world_data = json.load(f)
        
        brain_data = np.load(npz_path)
        
        # Проверка версии схемы
        schema_version = world_data.get("schema_version", 1)
        if schema_version != self.SCHEMA_VERSION and schema_version < 2:
            # Для старых версий схемы используем совместимость
            pass
        
        # Восстановление тика
        self.tick = world_data["tick"]
        
        # Восстановление статистики поколений (если есть)
        if "generation_stats" in world_data:
            self.generation_stats = world_data["generation_stats"]
        
        # Восстановление еды
        self.foods = []
        for f_data in world_data["foods"]:
            self.foods.append({
                "pos": np.array(f_data["pos"], dtype=np.float32),
                "nutrition": float(f_data["nutrition"]),
                "eaten": f_data["eaten"],
            })
        
        # Сброс агентов
        self.agents = []
        self.newborns = []
        
        # Восстановление агентов
        Agent.next_id = 0  # Сброс счетчика ID
        for agent_data in world_data["agents"]:
            # Восстанавливаем геном с новыми полями
            genome = Genome(
                genes=agent_data["genome_genes"].copy(),
                tag=agent_data["genome_tag"],
                tribal_tags=agent_data.get("genome_tribal_tags", []),
                n_hidden=agent_data.get("genome_n_hidden", None),
            )
            
            # Создаем агента
            pos = np.array(agent_data["pos"], dtype=np.float32)
            agent = Agent.__new__(Agent)
            agent.id = agent_data["id"]
            if agent.id >= Agent.next_id:
                Agent.next_id = agent.id + 1
            agent.pos = pos
            agent.angle = float(agent_data["angle"])
            agent.genome = genome
            agent.energy = float(agent_data["energy"])
            agent.age = float(agent_data["age"])
            agent.generation = agent_data["generation"]
            agent.alive = agent_data["alive"]
            agent.repro_cooldown = float(agent_data["repro_cooldown"])
            agent.last_pain = float(agent_data["last_pain"])
            agent.pending_reward = float(agent_data["pending_reward"])
            agent.pending_punishment = float(agent_data["pending_punishment"])
            agent.nearest_food = None
            agent.nearest_agent = None
            
            # Восстанавливаем мозг с правильным n_hidden
            brain_idx = agent_data["brain_idx"]
            agent.brain = Brain.__new__(Brain)
            agent.brain.W = brain_data[f"agent_{brain_idx}_W"]
            agent.brain.mask = brain_data[f"agent_{brain_idx}_mask"].astype(bool)
            agent.brain.v = brain_data[f"agent_{brain_idx}_v"]
            agent.brain.spikes = brain_data[f"agent_{brain_idx}_spikes"]
            agent.brain.out_rate = brain_data[f"agent_{brain_idx}_out_rate"]
            E_data = brain_data[f"agent_{brain_idx}_E"]
            agent.brain.E = E_data if E_data.size > 1 else None
            agent.brain.n_hidden = int(brain_data[f"agent_{brain_idx}_n_hidden"])
            agent.brain.n_in = INPUT_SIZE
            agent.brain.n_out = OUTPUT_SIZE
            agent.brain.n = agent.brain.n_in + agent.brain.n_hidden + agent.brain.n_out
            agent.brain.hidden_slice = slice(agent.brain.n_in, agent.brain.n)
            
            # Восстанавливаем параметры мозга из генома
            agent.brain.decay_base = genome["membrane_decay"]
            agent.brain.threshold_base = genome["threshold"]
            agent.brain.stdp_rate = genome["stdp_rate"]
            agent.brain.max_w = genome["weight_max"]
            
            # Восстанавливаем гормоны с новыми полями
            h_data = agent_data["hormones"]
            agent.hormones = Hormones.__new__(Hormones)
            agent.hormones.D = float(h_data["D"])
            agent.hormones.S = float(h_data["S"])
            agent.hormones.O = float(h_data["O"])
            agent.hormones.C = float(h_data["C"])
            agent.hormones.T = float(h_data["T"])
            agent.hormones.allostatic = float(h_data.get("allostatic", 0.0))
            agent.hormones.depression = float(h_data.get("depression", 0.0))
            agent.hormones.breakdown = float(h_data.get("breakdown", 0.0))
            agent.hormones.D_decay = float(h_data.get("D_decay", 0.05))
            agent.hormones.S_decay = float(h_data.get("S_decay", 0.05))
            agent.hormones.O_decay = float(h_data.get("O_decay", 0.05))
            agent.hormones.C_decay = float(h_data.get("C_decay", 0.05))
            agent.hormones.T_decay = float(h_data.get("T_decay", 0.05))
            agent.hormones.S_sensitivity = float(h_data.get("S_sensitivity", 1.0))
            agent.hormones.O_sensitivity = float(h_data.get("O_sensitivity", 1.0))
            agent.hormones.C_sensitivity = float(h_data.get("C_sensitivity", 1.0))
            agent.hormones.T_sensitivity = float(h_data.get("T_sensitivity", 1.0))
            
            self.agents.append(agent)
        
        print(f"World loaded: {json_path}, {npz_path}")
        print(f"Loaded tick: {self.tick}, agents: {len(self.agents)}, foods: {len(self.foods)}")
        return True
