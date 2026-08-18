# hormones.py
# Гормональная система агента с расширенной моделью эмоций
from .config import clamp


class Hormones:
    def __init__(self, genome):
        # Базовые уровни гормонов
        self.D = genome["dopamine_base"]
        self.S = genome["serotonin_base"]
        self.O = genome["oxytocin_base"]
        self.C = genome["cortisol_base"]
        self.T = genome["testosterone_base"]
        
        # Аллостатическая нагрузка - накопленный ущерб от хронического стресса
        self.allostatic = 0.0
        # Депрессия - состояние низкого настроения и мотивации
        self.depression = 0.0
        # Слом - критическое состояние после чрезмерного стресса
        self.breakdown = 0.0
        # Паранойя - недоверие к окружению, растёт от наказания и стресса
        self.paranoia = 0.0
        # Доверие - склонность к социальному взаимодействию
        self.trust = 0.5
        # Отложенное наказание - след от прошлых негативных событий
        self.delayed_punishment = 0.0
        self.punishment_history = []
        
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
        self.D_sensitivity = genome.get("dopamine_sensitivity", 1.0)
        
        # Индивидуальный профиль реактивности - насколько сильно агент реагирует на стимулы
        self.stress_resilience = genome.get("stress_resilience", 0.5)
        self.social_temperament = genome.get("social_temperament", 0.5)

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

        # Сохраняем историю наказания для отложенной реакции
        if punishment > 0.1:
            self.punishment_history.append((punishment, dt))
        # Обрабатываем отложенное наказание - эффект проявляется постепенно
        delayed_effect = 0.0
        if self.punishment_history:
            for i, (punish, age) in enumerate(self.punishment_history):
                self.punishment_history[i] = (punish, age + dt)
            # Старые события затухают, но влияют на текущее состояние
            active_punishments = [(p, a) for p, a in self.punishment_history if a < 50.0]
            if active_punishments:
                delayed_effect = sum(p * max(0.1, 1.0 - a/50.0) for p, a in active_punishments) / len(active_punishments)
            self.punishment_history = active_punishments
        self.delayed_punishment = clamp(delayed_effect, 0.0, 1.0)

        # Дофамин с учетом наследуемого распада и чувствительности
        D_decay_rate = self.D_decay if hasattr(self, 'D_decay') else genome.get("dopamine_decay", 0.05)
        D_sens = self.D_sensitivity if hasattr(self, 'D_sensitivity') else 1.0
        self.D += (
            genome["dopamine_reactivity"] * (reward - punishment) * 0.25 * D_sens
            + D_decay_rate * (genome["dopamine_base"] - self.D)
        )
        self.D = clamp(self.D, 0.0, 2.0)

        # Кортизол с учетом наследуемой чувствительности и распада
        C_decay_rate = self.C_decay if hasattr(self, 'C_decay') else genome.get("cortisol_decay", 0.05)
        C_sens = self.C_sensitivity if hasattr(self, 'C_sensitivity') else 1.0
        # Стресс зависит от индивидуальной устойчивости
        resilience_factor = 1.0 - self.stress_resilience * 0.4
        stress = (punishment * 1.0 + conflict * 0.6 + hunger * 0.35 + injury * 0.9 + fear * 0.8) * resilience_factor
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
            - self.delayed_punishment * 0.02
        )
        self.S = clamp(self.S, 0.0, 2.0)

        # Окситоцин с учетом наследуемой чувствительности и распада
        O_decay_rate = self.O_decay if hasattr(self, 'O_decay') else genome.get("oxytocin_decay", 0.05)
        O_sens = self.O_sensitivity if hasattr(self, 'O_sensitivity') else 1.0
        social_temper = self.social_temperament if hasattr(self, 'social_temperament') else 0.5
        self.O += (
            genome["oxytocin_gain"] * (social * 0.06 + kin * 0.08) * O_sens * (0.7 + social_temper * 0.6)
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

        # Аллостатическая нагрузка - накопленный ущерб от хронического стресса
        if self.C > 0.85:
            allostatic_increase = (self.C - 0.85) * 0.03 * (1.0 - self.stress_resilience * 0.3)
            self.allostatic += allostatic_increase
        else:
            self.allostatic = max(0.0, self.allostatic - 0.004)
        
        # Слом происходит при критической аллостатической нагрузке
        if self.allostatic > 1.8:
            self.breakdown = min(1.0, self.breakdown + 0.01)
        else:
            self.breakdown = max(0.0, self.breakdown - 0.006)

        # Депрессия - развивается при низком серотонине и дофамине
        low_S_threshold = 0.30 * (2.0 - self.S_sensitivity)
        low_D_threshold = 0.35 * (2.0 - self.D_sensitivity)
        if self.S < low_S_threshold and self.D < low_D_threshold:
            depression_rate = 0.004 * (1.0 + self.delayed_punishment)
            self.depression = min(1.0, self.depression + depression_rate)
        else:
            recovery_rate = 0.002 * (1.0 + self.O * 0.3)
            self.depression = max(0.0, self.depression - recovery_rate)

        # Паранойя - растёт от наказания, стресса и одиночества
        paranoia_triggers = punishment * 0.4 + self.C * 0.2 + fear * 0.3
        if paranoia_triggers > 0.3:
            self.paranoia = min(1.0, self.paranoia + 0.003 * paranoia_triggers)
        else:
            # Снижается от окситоцина и социальных контактов
            paranoia_reduction = (self.O * 0.3 + social * 0.2) * (1.0 - self.paranoia)
            self.paranoia = max(0.0, self.paranoia - paranoia_reduction * 0.005)

        # Доверие - зависит от окситоцина, серотонина и позитивного социального опыта
        trust_boost = (self.O * 0.4 + self.S * 0.2 + reward * 0.1) * (1.0 - self.trust)
        trust_decline = (punishment * 0.3 + self.paranoia * 0.4) * self.trust
        self.trust = clamp(self.trust + (trust_boost - trust_decline) * 0.01, 0.0, 1.0)

    def effects(self, genome, hunger=0.0):
        dopamine_error = self.D - genome["dopamine_base"]
        
        # Учет чувствительности к гормонам в эффектах
        C_eff = self.C * (self.C_sensitivity if hasattr(self, 'C_sensitivity') else 1.0)
        T_eff = self.T * (self.T_sensitivity if hasattr(self, 'T_sensitivity') else 1.0)
        S_eff = self.S * (self.S_sensitivity if hasattr(self, 'S_sensitivity') else 1.0)
        O_eff = self.O * (self.O_sensitivity if hasattr(self, 'O_sensitivity') else 1.0)
        D_eff = self.D * (self.D_sensitivity if hasattr(self, 'D_sensitivity') else 1.0)
        
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
        
        # Агрессия зависит от тестостерона, кортизола, паранойи и низкого доверия
        paranoia_factor = 1.0 + self.paranoia * 0.5
        distrust_factor = 1.0 + (1.0 - self.trust) * 0.3
        aggression = genome["aggression_gain"] * (
            T_eff * 0.55 + C_eff * 0.35 - S_eff * 0.25 + hunger * 0.20
        ) * paranoia_factor * distrust_factor
        
        # Социальность зависит от окситоцина, доверия и снижена паранойей
        trust_factor = self.trust * 0.7 + 0.3
        paranoia_social_penalty = 1.0 - self.paranoia * 0.6
        sociality = genome["social_gain"] * (
            O_eff * 0.85 + S_eff * 0.10 - C_eff * 0.20
        ) * trust_factor * paranoia_social_penalty
        
        dopamine_signal = clamp(dopamine_error * 1.5, -1.0, 1.0)
        return {
            "arousal": clamp(arousal, -1.0, 2.0),
            "plasticity": clamp(plasticity, 0.0, 3.0),
            "aggression": clamp(aggression, 0.0, 3.0),
            "sociality": clamp(sociality, 0.0, 3.0),
            "dopamine_signal": dopamine_signal,
            "depression": self.depression,
            "breakdown": self.breakdown,
            "paranoia": self.paranoia,
            "trust": self.trust,
            "allostatic": self.allostatic,
        }

    def get_mood(self):
        """Определяет текущее настроение на основе гормонального профиля."""
        # Сначала проверяем критические состояния
        if self.breakdown > 0.5:
            return "ярость"
        
        if self.depression > 0.5:
            return "грусть"
        
        # Паранойя влияет на восприятие
        if self.paranoia > 0.7:
            return "подозрительность"
        
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
        
        # Высокое доверие + окситоцин = спокойствие
        if self.trust > 0.6 and self.O > 0.5:
            return "спокойствие"
        
        return "нормальное"
    
    def is_broken(self):
        """Проверяет, сломано ли существо от хронического стресса."""
        return self.breakdown > 0.5
    
    def is_depressed(self):
        """Проверяет, находится ли существо в депрессии."""
        return self.depression > 0.5
    
    def is_paranoid(self):
        """Проверяет, параноидально ли настроено существо."""
        return self.paranoia > 0.5
    
    def is_trusting(self):
        """Проверяет, доверяет ли существо окружению."""
        return self.trust >= 0.5
