
from src.models import ParseError, GraphError
from src.parsing import Parse
from src.graph import Graph


def main(path: str) -> None:
    try:
        p = Parse(path)
        zones = p.get_zones()
        connections = p.get_connection()
    except ParseError as error:
        print(error)
        exit()

    graph = Graph(zones, connections)

    start = next(z for z in zones.values() if z.is_start)
    end = next(z for z in zones.values() if z.is_end)

    try:
        paths = graph.shortest_paths(start, end)
        for i, (dist, path) in enumerate(paths):
            print(f"Path {i + 1}: {' -> '.join(path)} (Distance: {dist})")
    except GraphError as error:
        print(error)


if __name__ == "__main__":
    file_path = "maps/easy/02_simple_fork.txt"
    main(file_path)
