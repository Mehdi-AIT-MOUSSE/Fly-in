from .models import Zone, Connection, GraphError
import heapq


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

    def shortest_paths(self, start: Zone, end: Zone, K: int = 4):

        path = [start.name]
        priority_queue = [(0, start.name, path)]

        paths = []

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

    def __repr__(self):
        lines = ["Graph adjacency list:"]

        for zone_name, neighbors in self.adj.items():
            adj = ", ".join(
                f"{neighbor.name} ({connection})"
                for neighbor, connection in neighbors
            )
            lines.append(f"{zone_name}: [{adj}]")

        return "\n".join(lines)
