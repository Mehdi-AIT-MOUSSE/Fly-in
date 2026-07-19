"""Turn-based drone fleet simulation."""

from .models import Zone, Connection, Drone, SimulationError
from .graph import Graph


class Simulation:
    """Simulates drone movement through a graph over discrete turns."""

    def __init__(
        self,
        graph: Graph,
        paths: list[tuple[float, list[str]]],
        nb_drones: int,
    ) -> None:
        """Initialize simulation state for the given graph and paths."""
        self.graph = graph
        self.nb_drones = nb_drones
        self.paths = paths
        self.drones: list[Drone] = []

    def creat_drones(self, start_zone: Zone) -> None:
        """Create drones at the start zone, one path per drone."""
        for i in range(self.nb_drones):
            path = self.paths[i % len(self.paths)][1]
            drone = Drone(id=i + 1, current_zone=start_zone, path=path)
            self.add_drone(drone)

    def check_simulation_finished(self) -> bool:
        """Return True when every drone has reached the end."""
        return all(drone.finished for drone in self.drones)

    def add_drone(self, drone: Drone) -> None:
        """Add a drone if its starting zone is not blocked."""
        if drone.current_zone.is_blocked():
            raise SimulationError(
                f"Cannot add drone to blocked zone: {drone.current_zone.name}")
        self.drones.append(drone)

    def move_drone(
        self,
        drone: Drone,
        next_zone: Zone,
        connection: Connection,
    ) -> None:
        """Move a drone into the next zone along its path."""
        drone.current_zone = next_zone
        drone.x = next_zone.x
        drone.y = next_zone.y
        drone.paths_index += 1

    def step_turn(self) -> tuple[list[str], bool]:
        """Advance the simulation by one turn."""
        if self.check_simulation_finished():
            return [], True

        turn_log: list[str] = []

        for conn in self.graph.connections:
            conn.current_drones = 0

        for drone in self.drones:
            current_zone = drone.current_zone
            if current_zone.is_end:
                continue

            assert drone.path is not None
            next_zone = self.graph.get_zone(drone.path[drone.paths_index])
            connection: Connection = self.graph.get_connection(
                                        current_zone.name, next_zone.name)
            if drone.in_the_restricted_con:
                drone.restricted_index += 1
                if drone.restricted_index < 2:
                    turn_log.append(f"D{drone.id}-{connection.name}")
                    continue

                drone.in_the_restricted_con = False
                drone.restricted_index = 0

                self.move_drone(drone, next_zone, connection)

                if drone.current_zone.is_end:
                    drone.finished = True
                turn_log.append(f"D{drone.id}-{next_zone.name}")
                continue

            if (next_zone.zone_has_capacity()
                    and connection.con_has_capacity()):
                current_zone.zone_decrement_drones()
                next_zone.zone_increment_drones()
                connection.con_increment_drones()

                if next_zone.type == 'restricted':
                    drone.in_the_restricted_con = True
                    drone.restricted_index = 1
                    turn_log.append(f"D{drone.id}-{connection.name}")
                    continue

                self.move_drone(drone, next_zone, connection)

                if drone.current_zone.is_end:
                    drone.finished = True
                turn_log.append(f"D{drone.id}-{next_zone.name}")

        return turn_log, self.check_simulation_finished()

    def run(self) -> None:
        """Console-mode run, kept for backwards compatibility."""
        turn = 1
        while not self.check_simulation_finished():
            turn_log, _finished = self.step_turn()
            print(f"Turn {turn}: ", end="")
            if turn_log:
                print(" ".join(turn_log))

            turn += 1

        print(f"\nSimulation completed in {turn - 1} turns.")

    def __repr__(self) -> str:
        """Return a readable representation of the simulation."""
        return f"Simulation(drones={self.drones})"
