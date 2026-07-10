class ParseError(Exception):
    pass


class GraphError(Exception):
    pass


class SimulationError(Exception):
    pass


class Zone:
    def __init__(self, name, x, y, metadata, is_start, is_end, nb_drones=0):
        self.name = name
        self.x = x
        self.y = y
        self.type = metadata['zone']
        self.color = metadata['color']
        self.max_drones = metadata['max_drones']
        self.is_start = is_start
        self.is_end = is_end

        self.current_drones = 0
        if self.is_start:
            self.current_drones = nb_drones

        self.cost = 1
        if self.type == "restricted":
            self.cost = 2
        elif self.type == "priority":
            self.cost = 0.9

    def is_blocked(self):
        return self.type == 'blocked'

    def zone_has_capacity(self):
        return self.current_drones < self.max_drones

    def zone_increment_drones(self):
        if self.zone_has_capacity():
            self.current_drones += 1

    def zone_decrement_drones(self):
        if self.current_drones > 0:
            self.current_drones -= 1

    def __repr__(self):
        tag = " [START]" if self.is_start else " [END]" if self.is_end else ""
        return (f"Zone(name={self.name!r}, x={self.x}, y={self.y}, "
                f"type={self.type!r}, color={self.color!r}, "
                f"max_drones={self.max_drones}{tag})")


class Connection:
    def __init__(self, zone1, zone2, max_link_capacity=1):
        self.zone1: Zone = zone1
        self.zone2: Zone = zone2
        self.current_drones = 0
        self.max_link_capacity: int = max_link_capacity
        self.name = f"{zone1.name}-{zone2.name}"

    def con_has_capacity(self):
        return self.current_drones < self.max_link_capacity

    def con_increment_drones(self):
        if self.con_has_capacity():
            self.current_drones += 1

    def con_decrement_drones(self):
        if self.current_drones > 0:
            self.current_drones -= 1

    def __repr__(self):
        return (f"Connection({self.zone1.name!r} <-> {self.zone2.name!r}, "
                f"max_link_capacity={self.max_link_capacity})")


class Drone:
    def __init__(self, id, current_zone: Zone, path=None):
        self.id = id
        self.current_zone = current_zone
        self.finished = False
        self.x = current_zone.x
        self.y = current_zone.y

        self.path = path
        self.paths_index = 1

        self.in_the_restricted_con = False
        self.restricted_index = 0

    def __repr__(self):
        return f"Drone(id={self.id}, current_zone={self.current_zone.name})"
