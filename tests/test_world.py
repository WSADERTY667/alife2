from alife.world import World


def test_world_updates_without_crash():
    world = World()
    for _ in range(100):
        world.update()
    assert len(world.agents) > 0
