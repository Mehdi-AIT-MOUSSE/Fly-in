*This project has been created as part of the 42 curriculum by mait-mou.*

# Fly-in — Drone Fleet Routing Simulation

## Description

Fly-in is a Python simulation that routes a fleet of drones through a network
of connected zones, from a single start zone to a single end zone, in as few
simulation turns as possible.

The map (zones, connections, and drone count) is loaded from a text file.
Each zone has a type — `normal`, `restricted`, `priority`, or `blocked` —
that affects movement cost, and a capacity limiting how many drones can
occupy it at once. Connections between zones also have a capacity limiting
how many drones can traverse them in the same turn. The simulation advances
turn by turn: each drone either moves to an adjacent zone (respecting zone
and connection capacity) or waits, until every drone has reached the end
zone.

The project is fully object-oriented and written without any external graph
library — pathfinding, capacity handling, and turn scheduling are all
implemented from scratch.

## Instructions

```bash
# install dependencies
make install

# run the simulation on a map file
make run MAP=maps/easy/01_linear_path.txt

# run in debug mode (drops into pdb)
make debug MAP=maps/easy/01_linear_path.txt

# lint the project (flake8 + mypy)
make lint

# stricter lint pass
make lint-strict

# remove caches and temporary files
make clean
```

Controls in the graphical view (Arcade window):

| Key / mouse             | Action                                   |
|-------------------------|------------------------------------------|
| `SPACE`                 | Advance the simulation by one turn       |
| `R`                     | Reset the simulation                     |
| `0`                     | Fit the whole map back into view         |
| `+` / `-`               | Zoom in / out (centered on screen)       |
| Left-click drag         | Pan the camera                           |
| Arrow keys              | Pan the camera                           |
| `ESC`                   | Quit                                     |

## Algorithm & Implementation Strategy

- **Parsing:** the map file is parsed line by line into `Zone` and
  `Connection` objects, validating zone types, capacities, and connection
  syntax, and raising a clear error (with line number) on malformed input.
- **Graph:** zones and connections are stored in an adjacency list. Zone
  type drives movement cost (`normal` = 1, `priority` = 0.9 so it's
  preferred, `restricted` = 2, `blocked` = unreachable).
- **Pathfinding:** a Dijkstra-based K-shortest-paths search finds several
  low-cost start→end routes, so drones can be spread across multiple paths
  instead of all queuing on a single one.
- **Simulation:** each turn, every drone attempts to move to the next zone
  on its assigned path. A move only succeeds if both the destination zone
  and the connection still have free capacity that turn; otherwise the
  drone waits. Restricted-zone connections take two turns to cross, and a
  drone committed to one must arrive on the following turn — it cannot wait
  mid-connection.
- **Turn output:** each turn prints the moves made that turn in
  `D<id>-<zone_or_connection>` format, omitting drones that didn't move,
  until all drones have reached the end zone.

## Visual Representation

The simulation ships with an Arcade-based graphical view (`DroneSimWindow`):

- Zones are drawn as colored circles (using each zone's declared color),
  labeled with their name, type, and current occupancy (`current/max`).
- Connections are drawn as lines labeled with current traversal count vs.
  capacity, turning red when full.
- Drones are drawn as small markers on their current zone, or at the
  midpoint of a connection while transiting a restricted zone.
- A camera system lets you pan and zoom independently of map size, so
  large maps can be viewed as a whole or inspected up close — the view
  starts fitted to show the entire start-to-end layout.
- A HUD overlays the current turn number, run status, zoom level, and
  stays fixed on screen regardless of pan/zoom.

This makes it easy to visually verify that capacity and movement rules are
respected, and to see how drones distribute across the available paths.

## Resources

- [Arcade documentation](https://api.arcade.academy/) — window, camera, and
  drawing API used for the visualization.
- [Dijkstra's algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
  — basis for the shortest-path search over zone costs.
