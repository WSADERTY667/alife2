#!/usr/bin/env python3
# main.py - точка входа в симуляцию ALife MVP
import pygame
import numpy as np
from alife.config import SCREEN_W, SCREEN_H, WORLD_H, FPS
from alife.world import World
from alife.render import draw, get_agent_by_id


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
