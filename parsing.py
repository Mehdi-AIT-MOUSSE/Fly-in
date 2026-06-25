class ParseError(Exception):
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

# connection: <zone1>-<zone2> [metadata]
class Connection:
    def __init__(self, zone1, zone2, max_link_capacity=1):
        self.zone1: Zone = zone1
        self.zone2: Zone = zone2
        self.max_link_capacity: int = max_link_capacity


class Parse:
    def __init__(self, path:str):
        self.path = path
        self.clean_lines = self.get_clean_lines()
        self.nb_drones:int = self.get_nb_drones()
        self.zones: list[Zone] = []

    def get_clean_lines(self):
        try:
            file = open(self.path)
        except Exception:
            raise ParseError("Invalid file operation")
        
        lines = [s for line in file if (s := line.strip()) and not s.startswith("#")]
        if not len(lines):
            raise ParseError("Empty file!")
        allowed_starts_words = ("nb_drones:", "start_hub:", "end_hub:", "hub:", "connection:")
        for line in lines:
            if not line.startswith(allowed_starts_words):
                word = line.split()[0]
                raise ParseError(f"Unknown {word}!,use only nb_drones, start_hub, end_hub, hub, connection with ':' after it directly")
        file.close()
        return lines
    
    def get_nb_drones(self):
        line = self.clean_lines[0]

        if line.startswith("nb_drones"):
            if ":" not in line:
                raise ParseError("nb_drones must be followed by ':'")
            try:
                value = int(line.split(":",1)[1].strip())
                
                if value < 0 :
                    raise ValueError()
            except ValueError:
                raise ParseError("The nb_drones must be one positive integer")

            return value       
        else:
            raise ParseError("The first line must be nb_drones")

    def verify_hub(self, line, is_start, is_end, names = set()):
        parts = line.split('[', 1)
        data = parts[0].split()
        metadata_dict = {
                        'zone' : 'normal',
                        'color' : None,
                        'max_drones' : 1
                    }
        if len(data) != 3:
            raise ParseError("Requires <name>, <x>, and <y>, with optional [metadata].")

        name, x, y = data

        if '-' in name:
            raise ParseError("Dashes and Spaces are forbidden in zone names.")

        if name in names:
            raise ParseError("Each zone must have a unique name.")

        names.add(name)

        try:
            x, y = int(x), int(y)
        except ValueError:
            raise ParseError("Each zone must have valid integer coordinates.")
        if len(parts) == 2:
            allowed_metadata = ["zone", "max_drones", "color"]
            allowed_zones = ['normal', 'blocked', 'restricted', 'priority']
            raw, after = parts[1].strip().split("]")

            if after:
                raise ParseError("Nothing is allowed after [metadata]")
            
            equal_conter = sum([1 for i in raw if i == "="])
            metadata = " ".join(raw.split()).replace(" = ", "=").split()

            if (len(metadata) != equal_conter):
                raise ParseError("Metadata must be in the [key=value key=value] format.")
            
            for meta in metadata:
                if '=' not in meta:
                    raise ParseError("Each metadata element must be in the key=value format.")
                key, value = meta.split("=", 1)
                
                if key not in allowed_metadata:
                    raise ParseError("Only zone, color and max_drones metadata are allowed.")
                    
                if key == "max_drones":
                    try:
                        value = int(value)
                        if value <= 0:
                            raise ValueError()
                    except ValueError:
                        raise ParseError("max_drones must be positive integer.")
                    
                elif key == "zone":
                    if value not in allowed_zones:
                        raise ParseError("Only normal, blocked, restricted or priority zone types are allowed.")
                
                metadata_dict[key] = value
            
        z = Zone(name, x, y, metadata_dict, is_start, is_end)
        return z
        
    def get_zones(self):
        hub_lines = list(filter(lambda line: line.startswith("hub"),
                                self.clean_lines))

        start_hub = list(filter(lambda line: line.startswith("start_hub"),
                                self.clean_lines))

        if (len(start_hub) == 0 or len(start_hub) > 1):
            raise ParseError("One start_hub must be present.")

        end_hub = list(filter(lambda line: line.startswith("end_hub"),
                                self.clean_lines))
        
        if (len(end_hub) == 0 or len(end_hub) > 1):
            raise ParseError("One end_hub must be present.")

        line = start_hub[0].split(":", 1)[1]
        zone = self.verify_hub(line, True, False)
        self.zones.append(zone)

        line = end_hub[0].split(":", 1)[1]
        zone = self.verify_hub(line, False, True)
        self.zones.append(zone)

        for line in hub_lines:
            line = line.split(":", 1)[1]
            zone = self.verify_hub(line, False, False)
            self.zones.append(zone)


    def get_connection(self):
        connections = list(filter(lambda line: line.startswith("connection"),
                                self.clean_lines))
        
        zones_names = [zone.name for zone in self.zones]
        max_link_capacity = 1

#   waypoint1-waypoint2  [max_link_capacity=2]
        for line in connections:

            line = line.split(":", 1)[1]
            line = line.split()
            if len(line) > 2:
                raise ParseError("The connection must follow this format:\n"
                                 "      connection: <zone1>-<zone2> [metadata]")
            
            data = line[0].split()

            if len(data) != 1:
                raise ParseError("The connection must follow this format:\n"
                                 "      connection: <zone1>-<zone2> [metadata]")
            if "-" not in data:
                raise ParseError("The connection must have '-' between zones : <zone1>-<zone2>")
            
            zone1, zone2 = data.split("-")
            print(zone1, zone2)

            print(data)



file_path = "maps/easy/01_linear_path.txt"

try:
    p = Parse(file_path)
    p.get_zones()
    # for i in p.zones:
    #     for name, zone in i.items():
    #         print(name,":")

    #         print(zone.name)
    #         print(zone.x)
    #         print(zone.y)
    #         print(zone.type)
    #         print(zone.color)
    #         print(zone.is_end)
    #     print("-" * 45)

    for zone in p.zones:
        print(zone)
        print(zone.name)
        print(zone.x)
        print(zone.y)
        print(zone.type)
        print(zone.color)
        
        print(zone.is_end)
        print("-" * 45) 

    print(p.nb_drones)

    # p.get_connection()

except ParseError as Error:
    print(Error)
