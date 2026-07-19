"""Graph structure and shortest-path search."""

from .models import Zone, Connection, GraphError
import heapq


class Graph:
    """Zone graph with adjacency list and pathfinding."""

    def __init__(
        self,
        zones: dict[str, Zone],
        connections: list[Connection],
    ) -> None:
        """Build adjacency lists from zones and connections."""
        self.zones: dict[str, Zone] = zones
        self.connections: list[Connection] = connections

        self.adj: dict[str, list[tuple[Zone, Connection]]] = {
            name: [] for name in zones
        }

        for con in connections:
            self.adj[con.zone1.name].append((con.zone2, con))
            self.adj[con.zone2.name].append((con.zone1, con))

    def shortest_paths(
        self,
        start: Zone,
        end: Zone,
        K: int = 4,
    ) -> list[tuple[float, list[str]]]:
        """Return up to K shortest paths from start to end."""
        path = [start.name]
        priority_queue: list[tuple[float, str, list[str]]] = [
            (0, start.name, path),
        ]

        paths: list[tuple[float, list[str]]] = []

        while priority_queue:
            current_dist, current_name, current_path = heapq.heappop(
                                                            priority_queue)

            if current_name == end.name:
                paths.append((current_dist, current_path))
                if len(paths) == K:
                    break

                continue

            for neighbor, connection in self.adj[current_name]:
                neighbor_name = neighbor.name

                if neighbor.is_blocked() or neighbor_name in current_path:
                    continue

                distance = current_dist + neighbor.cost

                heapq.heappush(
                    priority_queue,
                    (distance, neighbor_name, current_path + [neighbor_name])
                    )

        if not paths:
            raise GraphError(f"No path found from {start.name} to {end.name}")

        return paths

    def get_zone(self, zone_name: str) -> Zone:
        """Return the zone with the given name."""
        if zone_name not in self.zones:
            raise GraphError(
                f"Zone '{zone_name}' does not exist in the graph.")
        return self.zones[zone_name]

    def get_connection(self, zone1_name: str, zone2_name: str) -> Connection:
        """Return the connection between two named zones."""
        for con in self.adj[zone1_name]:
            zone, connection = con
            if zone.name == zone2_name:
                return connection
        raise GraphError(
            f"No connection found between '{zone1_name}' and '{zone2_name}'.")

    def __repr__(self) -> str:
        """Return a readable adjacency-list representation."""
        lines = ["Graph adjacency list:"]

        for zone_name, neighbors in self.adj.items():
            adj = ", ".join(
                f"{neighbor.name} ({connection})"
                for neighbor, connection in neighbors
            )
            lines.append(f"{zone_name}: [{adj}]")

        return "\n".join(lines)
