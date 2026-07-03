
from src.parsing import Parse, ParseError
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
    print(graph)

    start = next(z for z in zones.values() if z.is_start)
    end = next(z for z in zones.values() if z.is_end)
    print(start)
    print(end)


if __name__ == "__main__":
    file_path = "maps/easy/01_linear_path.txt"
    main(file_path)
