
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
        paths = graph.shortest_paths(start, end)
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
    main(file_path)
