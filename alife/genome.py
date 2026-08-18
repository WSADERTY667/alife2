# genome.py
# Геном агента и генетические операции
import random
from .config import TAG_COLORS, clamp

GENOME_KEYS = [
    "mutation_rate", "conn_prob", "weight_scale", "weight_max",
    "membrane_decay", "threshold", "stdp_rate", "plasticity_gain",
    "dopamine_base", "dopamine_reactivity", "dopamine_decay",
    "serotonin_base", "serotonin_decay", "serotonin_sensitivity",
    "oxytocin_base", "oxytocin_gain", "oxytocin_decay", "oxytocin_sensitivity",
    "cortisol_base", "cortisol_reactivity", "cortisol_decay", "cortisol_sensitivity",
    "testosterone_base", "testosterone_reactivity", "testosterone_decay", "testosterone_sensitivity",
    "aggression_gain", "social_gain",
    "lamarckian_weight", "metabolism",
    "brain_arch_mutability",  # вероятность мутации архитектуры мозга
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
    "dopamine_decay": (0.01, 0.20),
    "serotonin_base": (0.2, 1.0),
    "serotonin_decay": (0.01, 0.20),
    "serotonin_sensitivity": (0.5, 2.0),
    "oxytocin_base": (0.1, 0.8),
    "oxytocin_gain": (0.1, 2.0),
    "oxytocin_decay": (0.01, 0.20),
    "oxytocin_sensitivity": (0.5, 2.0),
    "cortisol_base": (0.05, 0.6),
    "cortisol_reactivity": (0.1, 2.0),
    "cortisol_decay": (0.01, 0.30),
    "cortisol_sensitivity": (0.5, 2.0),
    "testosterone_base": (0.1, 1.0),
    "testosterone_reactivity": (0.1, 2.0),
    "testosterone_decay": (0.01, 0.30),
    "testosterone_sensitivity": (0.5, 2.0),
    "aggression_gain": (0.0, 2.0),
    "social_gain": (0.0, 2.0),
    "lamarckian_weight": (0.0, 0.9),
    "metabolism": (0.01, 0.10),
    "brain_arch_mutability": (0.0, 0.15),
}

MUT_SCALE = {
    k: max(1e-5, (BOUNDS[k][1] - BOUNDS[k][0]) * 0.08)
    for k in GENOME_KEYS
}

KIN_KEYS = [
    "conn_prob", "threshold",
    "dopamine_base", "serotonin_base",
    "oxytocin_gain", "cortisol_decay",
    "aggression_gain", "social_gain",
    "cortisol_sensitivity", "oxytocin_sensitivity",
]


class Genome:
    def __init__(self, genes=None, tag=None, tribal_tags=None, n_hidden=None):
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
        
        # Племенные теги - наследуемые маркеры линии
        if tribal_tags is None:
            self.tribal_tags = []
        else:
            self.tribal_tags = list(tribal_tags)
        
        # Архитектура мозга - наследуемое количество скрытых нейронов
        if n_hidden is None:
            from .config import N_HIDDEN
            self.n_hidden = N_HIDDEN
        else:
            self.n_hidden = n_hidden

    def __getitem__(self, key):
        return self.genes[key]

    def get(self, key, default=None):
        return self.genes.get(key, default)

    def mutate(self):
        mr = clamp(self.genes.get("mutation_rate", 0.08), 0.0, 0.5)
        for k in GENOME_KEYS:
            if random.random() < mr:
                self.genes[k] = clamp(
                    self.genes[k] + random.gauss(0.0, MUT_SCALE[k]),
                    BOUNDS[k][0], BOUNDS[k][1],
                )
        if random.random() < mr * 0.35:
            self.tag = random.randint(0, len(TAG_COLORS) - 1)
        
        # Мутация архитектуры мозга (изменение количества скрытых нейронов)
        arch_mut = clamp(self.genes.get("brain_arch_mutability", 0.05), 0.0, 0.5)
        if random.random() < arch_mut:
            delta = random.choice([-8, -4, 4, 8])
            self.n_hidden = max(40, min(400, self.n_hidden + delta))
        
        # Мутация племенных тегов - редкое добавление нового тега
        if random.random() < mr * 0.05:
            new_tag = f"mut_{random.randint(1000, 9999)}"
            if new_tag not in self.tribal_tags:
                self.tribal_tags.append(new_tag)
                if len(self.tribal_tags) > 5:
                    self.tribal_tags.pop(0)

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
        
        # Наследование племенных тегов - комбинация от обоих родителей
        tribal_tags = list(set(a.tribal_tags + b.tribal_tags))[:5]
        
        # Наследование архитектуры мозга - среднее с небольшой вариацией
        n_hidden = int((a.n_hidden + b.n_hidden) / 2)
        n_hidden = max(40, min(400, n_hidden + random.choice([-4, 0, 0, 0, 4])))
        
        return Genome(genes, tag, tribal_tags, n_hidden)


def genome_similarity(g1, g2):
    total = 0.0
    for k in KIN_KEYS:
        lo, hi = BOUNDS[k]
        rng = max(1e-6, hi - lo)
        total += abs(g1[k] - g2[k]) / rng
    gene_sim = 1.0 - clamp(total / len(KIN_KEYS), 0.0, 1.0)
    tag_sim = 1.0 if g1.tag == g2.tag else 0.0
    
    # Учет племенных тегов в схожести
    if g1.tribal_tags and g2.tribal_tags:
        shared_tags = set(g1.tribal_tags) & set(g2.tribal_tags)
        tag_overlap = len(shared_tags) / max(len(g1.tribal_tags), len(g2.tribal_tags), 1)
    else:
        tag_overlap = 0.0
    
    # Схожесть архитектуры мозга
    n_hidden_diff = abs(g1.n_hidden - g2.n_hidden)
    arch_sim = 1.0 - clamp(n_hidden_diff / 200.0, 0.0, 1.0)
    
    # Комбинированная схожесть: гены + визуальный тег + племенные теги + архитектура
    return clamp(0.5 * gene_sim + 0.15 * tag_sim + 0.2 * tag_overlap + 0.15 * arch_sim, 0.0, 1.0)
