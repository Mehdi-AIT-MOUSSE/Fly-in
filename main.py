
from src.models import ParseError, GraphError, SimulationError
from src.parsing import Parse
from src.graph import Graph
from src.similation import Simulation


def main(path: str) -> None:
    try:
        p = Parse(path)
        zones = p.get_zones()
        connections = p.get_connection()
    except ParseError as error:
        print(error)
        exit()

    graph = Graph(zones, connections)

    start = next(z for z in zones.values() if z.is_start)
    end = next(z for z in zones.values() if z.is_end)

    try:
        paths = graph.shortest_paths(start, end, K=2)
        for i, (dist, path) in enumerate(paths):
            print(f"Path {i + 1}: {' -> '.join(path)} (Distance: {dist})")

        print('\n', '#' * 50, '\n')
    except GraphError as error:
        print(error)

    try:
        simulation = Simulation(graph, paths, nb_drones=start.max_drones)
        simulation.creat_drones(start_zone=start)
        simulation.run()

    except SimulationError as error:
        print(error)
    except GraphError as error:
        print(error)


if __name__ == "__main__":
    file_path = "maps/easy/02_simple_fork.txt"
    # file_path = "maps/challenger/01_the_impossible_dream.txt"
    # file_path = "maps/medium/02_circular_loop.txt"
    main(file_path)


# Maps
# # easy
# file_path = "maps/easy/01_linear_path.txt"
# file_path = "maps/easy/02_simple_fork.txt"
# file_path = "maps/easy/03_basic_capacity.txt"

# # medium
# file_path = "maps/medium/01_dead_end_trap.txt"
# file_path = "maps/medium/02_circular_loop.txt"
# file_path = "maps/medium/03_priority_puzzle.txt"

# # hard
# file_path = "maps/hard/01_maze_nightmare.txt"
# file_path = "maps/hard/02_capacity_hell.txt"
# file_path = "maps/hard/03_ultimate_challenge.txt"
