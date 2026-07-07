import heapq
from itertools import count

# ==========================================
# 1. MOCK CLASSES (Mimicking your project)
# ==========================================
class Zone:
    def __init__(self, name):
        self.name = name
        
    def is_blocked(self):
        return False # No blocked zones in this test

class Connection:
    def __init__(self, zone1, zone2, weight):
        self.zone1 = zone1
        self.zone2 = zone2
        self.weight = weight # Storing the test weight here

class Graph:
    def __init__(self):
        self.zones = {}
        self.adj = {}

    def add_edge(self, u_name, v_name, weight):
        # Create zones if they don't exist
        if u_name not in self.zones:
            self.zones[u_name] = Zone(u_name)
            self.adj[u_name] = []
        if v_name not in self.zones:
            self.zones[v_name] = Zone(v_name)
            self.adj[v_name] = []

        u_zone = self.zones[u_name]
        v_zone = self.zones[v_name]
        
        # Create connection object
        connection = Connection(u_zone, v_zone, weight)
        
        # Directed edge for the test case
        self.adj[u_name].append((v_zone, connection))


# ==========================================
# 2. ALGORITHMS (Using your exact logic)
# ==========================================
def dijkstra(graph, start_name, end_name, removed_nodes=None, removed_connections=None):
    if removed_nodes is None:
        removed_nodes = set()
    if removed_connections is None:
        removed_connections = set()

    distances = {name: float('inf') for name in graph.zones}
    distances[start_name] = 0
    previous = {name: None for name in graph.zones}
    
    pq = [(0, start_name)]

    while pq:
        current_dist, current_name = heapq.heappop(pq)

        if current_name == end_name:
            break
        if current_dist > distances[current_name]:
            continue

        for neighbor, connection in graph.adj[current_name]:
            neighbor_name = neighbor.name

            # The exact logic from your project
            if neighbor.is_blocked(): continue
            if neighbor_name in removed_nodes: continue
            if connection in removed_connections: continue

            # For the test, we read weight from the connection
            weight = connection.weight
            distance = current_dist + weight

            if distance < distances[neighbor_name]:
                distances[neighbor_name] = distance
                previous[neighbor_name] = current_name
                heapq.heappush(pq, (distance, neighbor_name))

    if distances[end_name] == float('inf'):
        return float('inf'), []

    path = []
    curr = end_name
    while curr is not None:
        path.insert(0, curr)
        curr = previous[curr]

    return distances[end_name], path


def yens_algorithm(graph, start_name, end_name, K=3):
    A = []
    B = []
    tie_breaker = count()

    # 1. Determine the shortest path
    initial_cost, initial_path = dijkstra(graph, start_name, end_name)
    if not initial_path:
        return A

    A.append((initial_cost, initial_path))
    print(f"--- [k=1] Found Absolute Shortest Path: {' -> '.join(initial_path)} (Cost: {initial_cost}) ---\n")

    # 2. Iterate to find the K-1 alternative paths
    for k in range(1, K):
        prev_cost, prev_path = A[k - 1]
        print(f"--- [k={k+1}] Searching for next path based on: {' -> '.join(prev_path)} ---")

        for i in range(len(prev_path) - 1):
            spur_node = prev_path[i]
            root_path = prev_path[:i + 1]

            removed_connections = set()
            removed_nodes = set(root_path[:-1])

            # Block connections used by previous identical root paths
            for _, p in A:
                if len(p) > i and p[:i + 1] == root_path:
                    node_u = p[i]
                    node_v = p[i + 1]
                    
                    for neighbor, connection in graph.adj[node_u]:
                        if neighbor.name == node_v:
                            removed_connections.add(connection)
                            print(f"  [Roadblock Placed] Node: {node_u} -> {node_v}")
                            break

            # Find the spur path
            spur_cost, spur_path = dijkstra(graph, spur_node, end_name, removed_nodes, removed_connections)

            if spur_path:
                total_path = root_path[:-1] + spur_path

                # Recalculate cost for the test graph
                total_cost = 0
                for j in range(len(total_path) - 1):
                    u = total_path[j]
                    v = total_path[j+1]
                    for neighbor, conn in graph.adj[u]:
                        if neighbor.name == v:
                            total_cost += conn.weight
                            break

                # Add to candidate waiting room
                if not any(total_path == candidate_path for _, _, candidate_path in B):
                    heapq.heappush(B, (total_cost, next(tie_breaker), total_path))
                    print(f"  [Candidate Found] Spur at {spur_node}: {' -> '.join(total_path)} (Cost: {total_cost})")

        if not B:
            print("  No more candidates found in waiting room.")
            break

        lowest_cost, _, best_path = heapq.heappop(B)
        A.append((lowest_cost, best_path))
        print(f"--- WINNER for k={k+1}: {' -> '.join(best_path)} (Cost: {lowest_cost}) ---\n")

    return A


# ==========================================
# 3. RUN THE TEST CASE
# ==========================================
if __name__ == "__main__":
    test_edges = [
        ('A', 'B', 1),
        ('A', 'C', 5),
        ('B', 'C', 1),
        ('B', 'D', 2),
        ('C', 'D', 1),
        ('D', 'E', 3),
        ('C', 'E', 5),
    ]

    graph = Graph()
    for u, v, w in test_edges:
        graph.add_edge(u, v, w)

    print("Executing Yen's Algorithm...\n")
    final_paths = yens_algorithm(graph, 'A', 'E', K=3)

    print("========================================")
    print("FINAL RESULTS")
    print("========================================")
    for i, (cost, path) in enumerate(final_paths, 1):
        print(f"Path {i}: {' -> '.join(path)} | Total Cost: {cost}")