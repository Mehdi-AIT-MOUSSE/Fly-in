from .models import Zone, Connection, Drone, SimulationError
from .graph import Graph


class Simulation:
    def __init__(self, graph: Graph, paths: list[(float, str)],
                 nb_drones: int):
        self.graph = graph
        self.nb_drones = nb_drones
        self.paths = paths
        self.drones: list[Drone] = []

    def creat_drones(self, start_zone: Zone):
        for i in range(self.nb_drones):
            path = self.paths[i % len(self.paths)][1]
            drone = Drone(id=i + 1, current_zone=start_zone, path=path)
            self.add_drone(drone)

    def check_simulation_finished(self):
        return all(drone.finished for drone in self.drones)

    def add_drone(self, drone: Drone):
        if drone.current_zone.is_blocked():
            raise SimulationError(
                f"Cannot add drone to blocked zone: {drone.current_zone.name}")
        self.drones.append(drone)

    def move_drone(self, drone, next_zone, connection):
            drone.current_zone = next_zone
            drone.x = next_zone.x
            drone.y = next_zone.y
            drone.paths_index += 1


    def run(self):
        turn = 1
        while not self.check_simulation_finished():
            turn_log = []
            
            for conn in self.graph.connections :
                conn.current_drones = 0

            for drone in self.drones:
                current_zone = drone.current_zone
                if current_zone.is_end:
                    continue

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



            if turn_log:
                print(" ".join(turn_log))

            turn += 1

        print(f"\nSimulation completed in {turn - 1} turns.")

    def __repr__(self):
        return f"Simulation(drones={self.drones})"
