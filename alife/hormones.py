# hormones.py
# Гормональная система агента
from .config import clamp


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

        # Дофамин
        self.D += (
            genome["dopamine_reactivity"] * (reward - punishment) * 0.25
            + 0.02 * (genome["dopamine_base"] - self.D)
        )
        self.D = clamp(self.D, 0.0, 2.0)

        # Кортизол
        stress = punishment * 1.0 + conflict * 0.6 + hunger * 0.35 + injury * 0.9 + fear * 0.8
        self.C += (
            genome["cortisol_reactivity"] * stress * 0.12
            - genome["cortisol_decay"] * (self.C - genome["cortisol_base"])
        )
        self.C = clamp(self.C, 0.0, 2.0)

        # Серотонин
        self.S += (
            genome["serotonin_decay"] * (genome["serotonin_base"] - self.S)
            + reward * 0.03
            - max(0.0, self.C - 0.8) * 0.05
        )
        self.S = clamp(self.S, 0.0, 2.0)

        # Окситоцин
        self.O += (
            genome["oxytocin_gain"] * (social * 0.06 + kin * 0.08)
            - 0.05 * (self.O - genome["oxytocin_base"])
        )
        self.O = clamp(self.O, 0.0, 2.0)

        # Тестостерон
        self.T += (
            genome["testosterone_reactivity"] * (conflict * 0.08 + dominance * 0.05)
            - 0.04 * (self.T - genome["testosterone_base"])
        )
        self.T = clamp(self.T, 0.0, 2.0)

        # Аллостатическая нагрузка
        if self.C > 0.85:
            self.allostatic += (self.C - 0.85) * 0.03
        else:
            self.allostatic = max(0.0, self.allostatic - 0.004)
        if self.allostatic > 1.8:
            self.breakdown = 1.0
        else:
            self.breakdown = max(0.0, self.breakdown - 0.006)

        # Депрессия
        if self.S < 0.30 and self.D < 0.35:
            self.depression = min(1.0, self.depression + 0.004)
        else:
            self.depression = max(0.0, self.depression - 0.002)

    def effects(self, genome, hunger=0.0):
        dopamine_error = self.D - genome["dopamine_base"]
        arousal = clamp(
            0.15 + self.C * 0.55 + self.T * 0.25 - self.S * 0.15 + hunger * 0.20,
            -0.5, 1.5,
        )
        plasticity = genome["plasticity_gain"] * (
            0.15 + max(0.0, dopamine_error) * 1.8
        ) * (1.0 - min(0.75, self.C * 0.35))
        if self.depression > 0.5:
            plasticity *= 0.45
        if self.breakdown > 0.5:
            plasticity *= 0.20
        aggression = genome["aggression_gain"] * (
            self.T * 0.55 + self.C * 0.35 - self.S * 0.25 + hunger * 0.20
        )
        sociality = genome["social_gain"] * (
            self.O * 0.85 + self.S * 0.10 - self.C * 0.20
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
