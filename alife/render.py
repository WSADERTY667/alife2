# render.py
# Рендеринг через Pygame
import math
import pygame
import numpy as np
from .config import (
    WORLD_W, WORLD_H, SCREEN_W, PANEL_H, TAG_COLORS, AGENT_RADIUS, MAX_ENERGY, clamp,
)


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
        screen, font, 10, y,
        f"Tick: {world.tick}  Agents: {len(world.agents)}  Food: {len(world.foods)}  Avg gen: {avg_gen:.1f}",
    )
    y += 18
    draw_text(
        screen, font, 10, y,
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
        screen, font, 10, y,
        f"Agent {selected.id}  gen {selected.generation}  age {int(selected.age)}  energy {selected.energy:.0f}",
        color,
    )
    y += 18
    draw_text(screen, font, 10, y, f"D {h.D:.2f}  S {h.S:.2f}  O {h.O:.2f}  C {h.C:.2f}  T {h.T:.2f}")
    y += 18
    mood = h.get_mood()
    draw_text(screen, font, 10, y, f"настроение: {mood}  аллостаз: {h.allostatic:.2f}  депрессия: {h.depression:.2f}")
    y += 18
    eff = h.effects(selected.genome)
    draw_text(
        screen, font, 10, y,
        f"tribe tag: {selected.genome.tag}  aggression: {eff['aggression']:.2f}  sociality: {eff['sociality']:.2f}",
        (170, 190, 220),
    )


def draw(screen, world, font, selected):
    screen.fill((8, 10, 14))
    for f in world.foods:
        if not f["eaten"]:
            pygame.draw.circle(screen, (70, 220, 120), (int(f["pos"][0]), int(f["pos"][1])), 3)
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


def get_agent_by_id(world, agent_id):
    if agent_id is None:
        return None
    for a in world.agents:
        if a.id == agent_id:
            return a
    return None
