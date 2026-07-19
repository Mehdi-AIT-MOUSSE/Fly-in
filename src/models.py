"""Core data models for zones, connections, drones, and errors."""

from typing import cast


class ParseError(Exception):
    """Raised when map file parsing fails."""

    pass


class GraphError(Exception):
    """Raised when graph path or lookup operations fail."""

    pass


class SimulationError(Exception):
    """Raised when simulation rules are violated."""

    pass


class Zone:
    """A map zone where drones can stop or pass through."""

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        metadata: dict[str, str | int],
        is_start: bool,
        is_end: bool,
        nb_drones: int = 0,
    ) -> None:
        """Initialize a zone from parsed metadata."""
        self.name = name
        self.x = x
        self.y = y
        self.type = cast(str, metadata['zone'])
        self.color = cast(str, metadata['color'])
        self.max_drones = cast(int, metadata['max_drones'])
        self.is_start = is_start
        self.is_end = is_end

        self.current_drones = 0
        if self.is_start:
            self.current_drones = nb_drones

        self.cost: float = 1
        if self.type == "restricted":
            self.cost = 2
        elif self.type == "priority":
            self.cost = 0.9

    def is_blocked(self) -> bool:
        """Return True if this zone blocks drone movement."""
        return self.type == 'blocked'

    def zone_has_capacity(self) -> bool:
        """Return True if the zone can accept another drone."""
        return self.current_drones < self.max_drones

    def zone_increment_drones(self) -> None:
        """Increase the drone count when one enters the zone."""
        if self.zone_has_capacity():
            self.current_drones += 1

    def zone_decrement_drones(self) -> None:
        """Decrease the drone count when one leaves the zone."""
        if self.current_drones > 0:
            self.current_drones -= 1

    def __repr__(self) -> str:
        """Return a readable representation of the zone."""
        tag = " [START]" if self.is_start else " [END]" if self.is_end else ""
        return (f"Zone(name={self.name!r}, x={self.x}, y={self.y}, "
                f"type={self.type!r}, color={self.color!r}, "
                f"max_drones={self.max_drones}{tag})")


class Connection:
    """A bidirectional link between two zones."""

    def __init__(
        self,
        zone1: Zone,
        zone2: Zone,
        max_link_capacity: int = 1,
    ) -> None:
        """Initialize a connection between two zones."""
        self.zone1: Zone = zone1
        self.zone2: Zone = zone2
        self.current_drones = 0
        self.max_link_capacity: int = max_link_capacity
        self.name = f"{zone1.name}-{zone2.name}"

    def con_has_capacity(self) -> bool:
        """Return True if the connection can carry another drone."""
        return self.current_drones < self.max_link_capacity

    def con_increment_drones(self) -> None:
        """Increase the drone count on this connection."""
        if self.con_has_capacity():
            self.current_drones += 1

    def con_decrement_drones(self) -> None:
        """Decrease the drone count on this connection."""
        if self.current_drones > 0:
            self.current_drones -= 1

    def __repr__(self) -> str:
        """Return a readable representation of the connection."""
        return (f"Connection({self.zone1.name!r} <-> {self.zone2.name!r}, "
                f"max_link_capacity={self.max_link_capacity})")


class Drone:
    """A drone moving along a predefined path through the graph."""

    def __init__(
        self,
        id: int,
        current_zone: Zone,
        path: list[str] | None = None,
    ) -> None:
        """Initialize a drone at its starting zone."""
        self.id = id
        self.current_zone = current_zone
        self.finished = False
        self.x = current_zone.x
        self.y = current_zone.y

        self.path = path
        self.paths_index = 1

        self.in_the_restricted_con = False
        self.restricted_index = 0

    def __repr__(self) -> str:
        """Return a readable representation of the drone."""
        return f"Drone(id={self.id}, current_zone={self.current_zone.name})"
