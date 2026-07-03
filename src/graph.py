from .models import Zone, Connection


class Graph:
    def __init__(self, zones: dict[str, Zone], connections: list[Connection]):
        self.zones: dict[str, Zone] = zones
        self.connections: list[Connection] = connections

        self.adj: dict[str, list[tuple[Zone, Connection]]] = {
            name: [] for name in zones
        }

        for con in connections:
            self.adj[con.zone1.name].append((con.zone2, con))
            self.adj[con.zone2.name].append((con.zone1, con))

    def __repr__(self):
        lines = ["Graph adjacency list:"]

        for zone_name, neighbors in self.adj.items():
            adj = ", ".join(
                f"{neighbor.name} ({connection})"
                for neighbor, connection in neighbors
            )
            lines.append(f"{zone_name}: [{adj}]")

        return "\n".join(lines)
