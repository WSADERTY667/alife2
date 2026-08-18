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
        
        # Полу-распады гормонов - наследуемые параметры распада
        self.D_decay = genome.get("dopamine_decay", 0.05)
        self.S_decay = genome.get("serotonin_decay", 0.05)
        self.O_decay = genome.get("oxytocin_decay", 0.05)
        self.C_decay = genome.get("cortisol_decay", 0.05)
        self.T_decay = genome.get("testosterone_decay", 0.05)
        
        # Чувствительность к гормонам - наследуемые множители эффекта
        self.S_sensitivity = genome.get("serotonin_sensitivity", 1.0)
        self.O_sensitivity = genome.get("oxytocin_sensitivity", 1.0)
        self.C_sensitivity = genome.get("cortisol_sensitivity", 1.0)
        self.T_sensitivity = genome.get("testosterone_sensitivity", 1.0)

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

        # Дофамин с учетом наследуемого распада
        D_decay_rate = self.D_decay if hasattr(self, 'D_decay') else genome.get("dopamine_decay", 0.05)
        self.D += (
            genome["dopamine_reactivity"] * (reward - punishment) * 0.25
            + D_decay_rate * (genome["dopamine_base"] - self.D)
        )
        self.D = clamp(self.D, 0.0, 2.0)

        # Кортизол с учетом наследуемой чувствительности и распада
        C_decay_rate = self.C_decay if hasattr(self, 'C_decay') else genome.get("cortisol_decay", 0.05)
        C_sens = self.C_sensitivity if hasattr(self, 'C_sensitivity') else 1.0
        stress = punishment * 1.0 + conflict * 0.6 + hunger * 0.35 + injury * 0.9 + fear * 0.8
        self.C += (
            genome["cortisol_reactivity"] * stress * 0.12 * C_sens
            - C_decay_rate * (self.C - genome["cortisol_base"])
        )
        self.C = clamp(self.C, 0.0, 2.0)

        # Серотонин с учетом наследуемой чувствительности и распада
        S_decay_rate = self.S_decay if hasattr(self, 'S_decay') else genome.get("serotonin_decay", 0.05)
        S_sens = self.S_sensitivity if hasattr(self, 'S_sensitivity') else 1.0
        self.S += (
            S_decay_rate * (genome["serotonin_base"] - self.S) * S_sens
            + reward * 0.03
            - max(0.0, self.C - 0.8) * 0.05
        )
        self.S = clamp(self.S, 0.0, 2.0)

        # Окситоцин с учетом наследуемой чувствительности и распада
        O_decay_rate = self.O_decay if hasattr(self, 'O_decay') else genome.get("oxytocin_decay", 0.05)
        O_sens = self.O_sensitivity if hasattr(self, 'O_sensitivity') else 1.0
        self.O += (
            genome["oxytocin_gain"] * (social * 0.06 + kin * 0.08) * O_sens
            - O_decay_rate * (self.O - genome["oxytocin_base"])
        )
        self.O = clamp(self.O, 0.0, 2.0)

        # Тестостерон с учетом наследуемой чувствительности и распада
        T_decay_rate = self.T_decay if hasattr(self, 'T_decay') else genome.get("testosterone_decay", 0.05)
        T_sens = self.T_sensitivity if hasattr(self, 'T_sensitivity') else 1.0
        self.T += (
            genome["testosterone_reactivity"] * (conflict * 0.08 + dominance * 0.05) * T_sens
            - T_decay_rate * (self.T - genome["testosterone_base"])
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
        
        # Учет чувствительности к гормонам в эффектах
        C_eff = self.C * (self.C_sensitivity if hasattr(self, 'C_sensitivity') else 1.0)
        T_eff = self.T * (self.T_sensitivity if hasattr(self, 'T_sensitivity') else 1.0)
        S_eff = self.S * (self.S_sensitivity if hasattr(self, 'S_sensitivity') else 1.0)
        O_eff = self.O * (self.O_sensitivity if hasattr(self, 'O_sensitivity') else 1.0)
        
        arousal = clamp(
            0.15 + C_eff * 0.55 + T_eff * 0.25 - S_eff * 0.15 + hunger * 0.20,
            -0.5, 1.5,
        )
        plasticity = genome["plasticity_gain"] * (
            0.15 + max(0.0, dopamine_error) * 1.8
        ) * (1.0 - min(0.75, C_eff * 0.35))
        if self.depression > 0.5:
            plasticity *= 0.45
        if self.breakdown > 0.5:
            plasticity *= 0.20
        aggression = genome["aggression_gain"] * (
            T_eff * 0.55 + C_eff * 0.35 - S_eff * 0.25 + hunger * 0.20
        )
        sociality = genome["social_gain"] * (
            O_eff * 0.85 + S_eff * 0.10 - C_eff * 0.20
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
