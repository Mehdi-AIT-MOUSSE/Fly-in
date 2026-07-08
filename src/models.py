class ParseError(Exception):
    pass


class GraphError(Exception):
    pass


class Zone:
    def __init__(self, name, x, y, metadata, is_start, is_end):
        self.name = name
        self.x = x
        self.y = y
        self.type = metadata['zone']
        self.color = metadata['color']
        self.max_drones = metadata['max_drones']
        self.is_start = is_start
        self.is_end = is_end

        self.cost = 1
        if self.type == "restricted":
            self.cost = 2
        elif self.type == "restricted":
            self.cost = 0.9

    def is_blocked(self):
        return self.type == 'blocked'

    def __repr__(self):
        tag = " [START]" if self.is_start else " [END]" if self.is_end else ""
        return (f"Zone(name={self.name!r}, x={self.x}, y={self.y}, "
                f"type={self.type!r}, color={self.color!r}, "
                f"max_drones={self.max_drones}{tag})")


class Connection:
    def __init__(self, zone1, zone2, max_link_capacity=1):
        self.zone1: Zone = zone1
        self.zone2: Zone = zone2
        self.max_link_capacity: int = max_link_capacity

    def __repr__(self):
        return (f"Connection({self.zone1.name!r} <-> {self.zone2.name!r}, "
                f"max_link_capacity={self.max_link_capacity})")
