from models import Zone, Connection


class ParseError(Exception):
    pass


class Parse:
    def __init__(self, path: str):
        self.path = path
        self.clean_lines = self.get_clean_lines()
        self.nb_drones: int = self.get_nb_drones()
        self.zones: dict[str:Zone] = dict()
        self.connections: list[Connection] = []

    def get_clean_lines(self):
        try:
            with open(self.path) as file:
                lines = [
                    (i, s)
                    for i, line in enumerate(file, start=1)
                    if (s := " ".join(line.strip().split()))
                    and not s.startswith("#")
                ]
        except FileNotFoundError:
            raise ParseError(f"File Not Found in path {self.path}")
        except PermissionError:
            raise ParseError("File Permission Error")
        except Exception:
            raise ParseError("Invalid file operation")

        if not len(lines):
            raise ParseError("Empty file!")

        lines = [
            (lineno,
             raw.replace('[ ', '[').replace(' ]', ']')
                .replace(' =', '=').replace('= ', '=')
                .replace(" :", ":").replace('"', '')
                .replace("'", ""))
            for lineno, raw in lines
        ]

        allowed_starts_words = ("nb_drones:", "start_hub:",
                                "end_hub:", "hub:", "connection:")

        for i, data in enumerate(lines):
            lineno, raw = data
            if not raw.startswith(allowed_starts_words):
                word = raw.split()[0]
                raise ParseError(
                    f"Line {lineno}: Unknown '{word}'!, use only nb_drones, "
                    "start_hub, end_hub, hub, "
                    "connection with ':' after it directly"
                )

            if "#" in raw:
                idx = raw.index('#')
                lines[i] = (lineno, raw[:idx].strip())

        return lines

    def get_nb_drones(self):
        lineno, raw = self.clean_lines[0]
        nbs = list(filter(lambda line: line[1].startswith("nb_drones"),
                          self.clean_lines))

        if len(nbs) > 1:
            raise ParseError("Duplicate nb_drones found. Use only one.")

        if raw.startswith("nb_drones"):
            if ":" not in raw:
                raise ParseError(
                    f"Line {lineno}: nb_drones must be followed by ':'")
            try:
                value = int(raw.split(":", 1)[1].strip())
                if value <= 0:
                    raise ValueError()
            except ValueError:
                raise ParseError(f"Line {lineno}: "
                                 "The nb_drones must be one positive integer")

            return value
        else:
            raise ParseError(
                f"Line {lineno}: The first line must be nb_drones")

    def verify_hub(self, line, is_start,
                   is_end, lineno=None, names=set(), cords=set()):
        loc = f"Line {lineno}: " if lineno is not None else ""

        parts = line.split()
        if len(parts) < 3:
            raise ParseError(f"{loc}Requires <name>, <x>, and <y>,"
                             " with optional [metadata].")

        data = parts[0:3]

        metadata_dict = {
            'zone': 'normal',
            'color': "none",
            'max_drones': 1
        }

        name, x, y = data
        if '-' in name:
            raise ParseError(
                f"{loc}Dashes and Spaces are forbidden in zone names.")

        if name in names:
            raise ParseError(f"{loc}Each zone must have a unique name.")
        names.add(name)

        try:
            x, y = int(x), int(y)
        except ValueError:
            raise ParseError(
                f"{loc}Each zone must have valid integer coordinates.")

        if (x, y) in cords:
            raise ParseError(f"{loc}Each zone must have unique x and y.")
        cords.add((x, y))

        if len(parts) > 3:
            allowed_metadata = {"zone", "max_drones", "color"}
            allowed_zones = {'normal', 'blocked', 'restricted', 'priority'}
            allowed_colors = {
                "red", "blue", "green", "yellow", "orange", 'crimson', 'gold',
                'magenta', 'darkred', 'lime', 'brown', 'cyan', 'violet',
                'purple', 'maroon', 'black'}

            metadata = " ".join(parts[3:])

            if not (metadata.startswith('[') and metadata.endswith(']')):
                raise ParseError(
                    f"{loc}Metadata must be written between square brackets []"
                    )

            metadata = metadata[1:-1]
            if "[" in metadata or "]" in metadata:
                raise ParseError(
                    f"{loc}square brackets are not allow between the metadata"
                    )

            metadata = metadata.split()

            keys = set()
            for meta in metadata:
                if '=' not in meta:
                    raise ParseError(f"{loc}Each metadata element"
                                     " must be in the key=value format")
                key, value = meta.split("=", 1)
                if key not in allowed_metadata:
                    raise ParseError(f"{loc}Only zone, color and max_drones"
                                     " metadata are allowed.")

                if key in keys:
                    raise ParseError(f"{loc}Don't duplicate the metadata.")
                keys.add(key)

                if key == "max_drones":
                    try:
                        value = int(value)
                        if value <= 0:
                            raise ValueError()
                    except ValueError:
                        raise ParseError(
                            f"{loc}max_drones must be positive integer.")

                elif key == "zone":
                    if value not in allowed_zones:
                        raise ParseError(
                            f"{loc}Only normal, blocked, restricted or "
                            "priority zone types are allowed.")
                else:
                    if "=" in value:
                        raise ParseError(
                                    f"{loc}Unvalid color value")

                    if value not in allowed_colors:
                        value = "none"

                metadata_dict[key] = value

        if is_start or is_end:
            metadata_dict["max_drones"] = self.nb_drones

        z = Zone(name, x, y, metadata_dict, is_start, is_end)
        return z

    def get_zones(self):
        hub_lines = list(filter(lambda line: line[1].startswith("hub"),
                                self.clean_lines))

        start_hub = list(filter(lambda line: line[1].startswith("start_hub"),
                                self.clean_lines))

        if (len(start_hub) == 0 or len(start_hub) > 1):
            raise ParseError("line 1: One start_hub must be present.")

        end_hub = list(filter(lambda line: line[1].startswith("end_hub"),
                              self.clean_lines))

        if (len(end_hub) == 0 or len(end_hub) > 1):
            raise ParseError("One end_hub must be present.")

        lineno, raw = start_hub[0]
        line = raw.split(":", 1)[1]
        zone = self.verify_hub(line, True, False, lineno)
        self.zones[zone.name] = zone

        lineno, raw = end_hub[0]
        line = raw.split(":", 1)[1]
        zone = self.verify_hub(line, False, True, lineno)
        self.zones[zone.name] = zone

        for lineno, raw in hub_lines:
            line = raw.split(":", 1)[1]
            zone = self.verify_hub(line, False, False, lineno)
            self.zones[zone.name] = zone

        return self.zones

    def get_connection(self):
        connections = list(filter(lambda t: t[1].startswith("connection"),
                                  self.clean_lines))

        zones_names = set([name for name in self.zones])
        exist_comb = set()
        for lineno, raw in connections:
            max_link_capacity = 1

            line = raw.split(":", 1)[1]
            line = line.split()

            if len(line) == 0:
                raise ParseError(
                    f"Line {lineno}: Empty connection, follow this format:"
                    " connection: <zone1>-<zone2> [metadata]")

            data = line[0]
            if "-" not in data:
                raise ParseError(
                    f"Line {lineno}: The connection must have '-' between"
                    " zones: <zone1>-<zone2>")

            zone1, zone2 = data.split("-", 1)

            if zone1 not in zones_names or zone2 not in zones_names:
                raise ParseError(
                    f"Line {lineno}: Unknown zone in '{data}' connection")

            comb1, comb2 = f"{zone1}-{zone2}", f"{zone2}-{zone1}"
            if comb1 in exist_comb or comb2 in exist_comb:
                raise ParseError(
                    f"Line {lineno}: Duplicate connection: {comb1}")

            exist_comb.add(comb1)
            exist_comb.add(comb2)

            if len(line) > 1:
                metadata = " ".join(line[1:])
                if not (metadata.startswith('[') and metadata.endswith(']')):
                    raise ParseError(
                        f"Line {lineno}: Metadata must be written between "
                        "square brackets []")

                metadata = metadata[1:-1].split()

                if len(metadata) > 1:
                    raise ParseError(
                        f"Line {lineno}: Connection metadata only supports"
                        " one max_link_capacity (max_link_capacity=int).")

                if (len(metadata) == 1):
                    metadata = metadata[0]
                    if "=" not in metadata:
                        raise ParseError(
                            f"Line {lineno}: Metadata must be in the "
                            "[key=value] format.")

                    key, value = metadata.split("=")
                    if key != "max_link_capacity":
                        raise ParseError(
                            f"Line {lineno}: The connection metadata allows "
                            "only max_link_capacity (max_link_capacity=int).")

                    try:
                        value = int(value)
                        if value <= 0:
                            raise ValueError()
                    except ValueError:
                        raise ParseError(
                            f"Line {lineno}: max_link_capacity must be "
                            "a positive integer.")

                    max_link_capacity = value

            zone1: Zone = self.zones[zone1]
            zone2: Zone = self.zones[zone2]

            connection = Connection(zone1, zone2, max_link_capacity)
            self.connections.append(connection)

        return self.connections


file_path = "maps/easy/01_linear_path.txt"

try:
    p = Parse(file_path)
    zones = p.get_zones()
    connections = p.get_connection()

    for c in connections:
        print(c)

except ParseError as Error:
    print(Error)
