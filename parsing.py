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

class Parse:
    def __init__(self, path:str):
        self.f = open(path)
        self.clean_lines = [s for line in self.f if (s := line.strip()) and not s.startswith("#")]
        self.nb_drones:int = self.get_nb_drones()
        self.zones: list[Zone] = []

    
    def get_nb_drones(self):
        line = self.clean_lines[0]

        if line.startswith("nb_drones"):
            if ":" not in line:
                raise ValueError("nb_drones must be followed by ':'")
            try:
                value = int(line.split(":",1)[1].strip())
                
                if value < 0 :
                    raise ValueError
            except ValueError:
                raise ValueError("The nb_drones must be one positive integer")

            return value       
        else:
            raise ValueError("The first line must be nb_drones")


    def verify_hub(self, line, is_start, is_end, names = set()):
        parts = line.split('[', 1)
        data = parts[0].split()

        if len(data) != 3:
            raise ValueError("Requires <name>, <x>, and <y>, with optional [metadata].")

        name, x, y = data

        if '-' in name:
            raise ValueError("Dashes and Spaces are forbidden in zone names.")

        if name in names:
            raise ValueError("Each zone must have a unique name.")

        names.add(name)

        try:
            x, y = int(x), int(y)
        except ValueError:
            raise ValueError("Each zone must have valid integer coordinates.")

        if len(parts) == 2:
            metadata_dict = {
                'zone' : 'normal',
                'color' : None,
                'max_drones' : 1
            }
            allowed_metadata = ["zone", "max_drones", "color"]
            allowed_zones = ['normal', 'blocked', 'restricted', 'priority']
            raw, after = parts[1].strip().split("]")

            if after:
                raise ValueError("Nothing is allowed after [metadata]")
            
            equal_conter = sum([1 for i in raw if i == "="])
            metadata = " ".join(raw.split()).replace(" = ", "=").split()

            if (len(metadata) != equal_conter):
                raise ValueError("Metadata must be in the [key=value key=value] format.")
            
            for meta in metadata:
                if '=' not in meta:
                    raise ValueError("Each metadata element must be in the key=value format.")
                key, value = meta.split("=", 1)
                
                if key not in allowed_metadata:
                    raise ValueError("Only zone, color and max_drones metadata are allowed.")
                    
                if key == "max_drones":
                    try:
                        value = int(value)
                        if value <= 0:
                            raise ValueError()
                    except ValueError:
                        raise ValueError("max_drones must be positive integer.")
                    
                elif key == "zone":
                    if value not in allowed_zones:
                        raise ValueError("Only normal, blocked, restricted or priority zone types are allowed.")
                
                metadata_dict[key] = value
            
            z = Zone(name, x, y, metadata_dict, is_start, is_end)
            return z

        
    def get_zones(self):
        hub_lines = list(filter(lambda line: line.startswith("hub"),
                                self.clean_lines))
        
        start_hub = list(filter(lambda line: line.startswith("start_hub"),
                                self.clean_lines))

        if (len(start_hub) == 0 or len(start_hub) > 1):
            raise ValueError("One start_hub must be present.")

        end_hub = list(filter(lambda line: line.startswith("end_hub"),
                                self.clean_lines))
        
        if (len(end_hub) == 0 or len(end_hub) > 1):
            raise ValueError("One end_hub must be present.")

        for line in hub_lines:
            line = line.split(":", 1)[1]
            zone = self.verify_hub(line, False, False)
            self.zones.append(zone)
        
            


file_path = "maps/easy/01_linear_path.txt"

try:
    p = Parse(file_path)
    p.get_zones()
    for i in p.zones:
        print(i.name)
        print(i.x)
        print(i.y)
        print(i.type)
        print(i.color)
        print(i.is_end)
        print("-" * 45)

except ValueError as Error:
    print(Error)
