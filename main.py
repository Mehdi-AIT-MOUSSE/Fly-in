from src.models import ParseError, GraphError, SimulationError
from src.parsing import Parse
from src.graph import Graph
from src.similation import Simulation
from src.display import DroneSimWindow
import arcade
import sys


class Main:
    '''Main class to run the drone simulation with a chosen map.'''
    path: str

    def __init__(self, path: str | None = None) -> None:
        """Initialize the main simulation with a map path."""
        if path:
            self.path = path
        else:
            self.path = self.menu()

    def menu(self) -> str:
        '''Display a menu for the user to choose a map file.'''
        maps = [
            "maps/easy/01_linear_path.txt",
            "maps/easy/02_simple_fork.txt",
            "maps/easy/03_basic_capacity.txt",
            "maps/medium/01_dead_end_trap.txt",
            "maps/medium/02_circular_loop.txt",
            "maps/medium/03_priority_puzzle.txt",
            "maps/hard/01_maze_nightmare.txt",
            "maps/hard/02_capacity_hell.txt",
            "maps/hard/03_ultimate_challenge.txt",
            "maps/challenger/01_the_impossible_dream.txt"
        ]

        for i, path in enumerate(maps, start=1):
            print(f"{i}. {path}")

        try:
            choice = int(input("Choose a map: "))
            if not (1 <= choice <= len(maps)):
                raise ValueError
        except ValueError:
            choice = 1

        return maps[choice - 1]

    def run(self) -> None:
        """Run the simulation with the selected map."""
        try:
            p = Parse(self.path)
            nb_drones = p.nb_drones
            zones = p.get_zones()
            connections = p.get_connection()
        except ParseError as error:
            print(f"\033[31m{error}\033[0m")
            exit()
        graph = Graph(zones, connections)

        start = next(z for z in zones.values() if z.is_start)
        end = next(z for z in zones.values() if z.is_end)

        try:
            paths = graph.shortest_paths(start, end, K=2)
        except GraphError as error:
            print(f"\033[31m{error}\033[0m")
            exit()
        try:
            simulation = Simulation(graph, paths, nb_drones)
            simulation.creat_drones(start_zone=start)

            DroneSimWindow(
                graph,
                start,
                end,
                paths,
                nb_drones,
            )
            arcade.run()
        except SimulationError as error:
            print(f"\033[31m{error}\033[0m")
            exit()


if __name__ == "__main__":
    try:
        # file_path = "maps/easy/02_simple_fork.txt"

        file_path = sys.argv[1] if len(sys.argv) > 1 else None
        main = Main(file_path)
        main.run()

    except (Exception, KeyboardInterrupt):
        exit()
