#!/usr/bin/env python3
# main.py - точка входа в симуляцию ALife MVP
import argparse
import time
import numpy as np


def run_headless(ticks, agents, food, hidden_neurons):
    """Запуск симуляции в headless-режиме."""
    from alife.config import WORLD_W, WORLD_H
    from alife.world import World
    import random
    
    # Настройка начальных параметров
    original_agent_count = None
    original_food_max = None
    
    if agents is not None or food is not None or hidden_neurons is not None:
        from alife import config
        if agents is not None:
            original_agent_count = config.AGENT_COUNT
            config.AGENT_COUNT = agents
        if food is not None:
            original_food_max = config.FOOD_MAX
            config.FOOD_MAX = food
        if hidden_neurons is not None:
            original_hidden = config.N_HIDDEN
            config.N_HIDDEN = hidden_neurons
            # Пересчитать TOTAL_NEURONS
            config.TOTAL_NEURONS = config.INPUT_SIZE + config.N_HIDDEN + config.OUTPUT_SIZE
    
    world = World()
    
    # Восстановить оригинальные значения если они были изменены
    if original_agent_count is not None:
        config.AGENT_COUNT = original_agent_count
    if original_food_max is not None:
        config.FOOD_MAX = original_food_max
    if hidden_neurons is not None:
        config.N_HIDDEN = original_hidden
        config.TOTAL_NEURONS = config.INPUT_SIZE + config.N_HIDDEN + config.OUTPUT_SIZE
    
    # Статистика
    start_time = time.time()
    tick_times = []
    total_births = 0
    total_deaths = 0
    initial_agents = len(world.agents)
    
    for t in range(ticks):
        tick_start = time.time()
        prev_count = len(world.agents)
        world.update()
        curr_count = len(world.agents)
        
        # Подсчет рождений и смертей
        births = len(world.newborns)
        deaths = prev_count - (curr_count - births)
        if deaths < 0:
            deaths = 0
        total_births += births
        total_deaths += deaths
        
        tick_end = time.time()
        tick_times.append(tick_end - tick_start)
        
        # Проверка на NaN в мозгах всех агентов
        for a in world.agents:
            if np.any(np.isnan(a.brain.W)):
                raise RuntimeError(f"NaN detected in brain weights at tick {t}, agent {a.id}")
            if np.any(np.isnan(a.brain.v)):
                raise RuntimeError(f"NaN detected in brain voltages at tick {t}, agent {a.id}")
    
    end_time = time.time()
    
    # Вычисление статистики
    avg_tick_time = sum(tick_times) / len(tick_times) if tick_times else 0.0
    final_agents = len(world.agents)
    avg_generation = sum(a.generation for a in world.agents) / final_agents if final_agents > 0 else 0.0
    
    print(f"=== Headless Simulation Results ===")
    print(f"Ticks completed: {ticks}")
    print(f"Average tick time: {avg_tick_time*1000:.3f} ms")
    print(f"Final agent count: {final_agents}")
    print(f"Average generation: {avg_generation:.2f}")
    print(f"Total births: {total_births}")
    print(f"Total deaths: {total_deaths}")
    print(f"Total simulation time: {end_time - start_time:.2f} s")


def main():
    parser = argparse.ArgumentParser(description="ALife MVP Simulation")
    parser.add_argument("--headless", action="store_true", help="Run without Pygame display")
    parser.add_argument("--ticks", type=int, default=1000, help="Number of ticks for headless mode")
    parser.add_argument("--agents", type=int, default=None, help="Initial number of agents")
    parser.add_argument("--food", type=int, default=None, help="Initial/max number of food items")
    parser.add_argument("--hidden-neurons", type=int, default=None, help="Number of hidden neurons")
    args = parser.parse_args()
    
    if args.headless:
        run_headless(args.ticks, args.agents, args.food, args.hidden_neurons)
        return
    
    # Visual mode (original behavior)
    import pygame
    from alife.config import SCREEN_W, SCREEN_H, WORLD_H, FPS
    from alife.world import World
    from alife.render import draw, get_agent_by_id
    
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
    print("Space: pause | S: save | L: load | F: food | A: agent | R: reset | +/-: speed")
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
                elif event.key == pygame.K_s:
                    world.save()
                elif event.key == pygame.K_l:
                    world.load()
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
