"""Arcade window for visualizing the drone simulation."""

from collections import defaultdict
from math import cos, pi, sin
from typing import cast

from .graph import Graph
from .models import Zone, Connection, Drone
from .similation import Simulation

import arcade

SPACING_X = 200
SPACING_Y = 270
MARGIN_X = 50
MARGIN_Y = 10
ZONE_RADIUS = 58
DRONE_RADIUS = 13
LINE_WIDTH = 3

WINDOW_WIDTH = 1180
WINDOW_HEIGHT = 740
HUD_TOP = 86
HUD_BOTTOM = 56

MIN_ZOOM = 0.15
MAX_ZOOM = 4.0
ZOOM_STEP = 1.1
PAN_SPEED = 600.0

# Mission-control palette
BG = (7, 10, 18, 255)
GRID = (22, 32, 52, 70)
INK = (12, 16, 28, 230)
INK_SOFT = (16, 22, 36, 200)
LINE = (58, 78, 108)
LINE_GLOW = (56, 140, 168, 55)
LINE_HOT = (232, 176, 72)
ACCENT = (64, 214, 196)
GOLD = (232, 196, 104)
CYAN = (92, 196, 255)
DANGER = (255, 92, 98)
MUTED = (148, 162, 178)
PAPER = (236, 240, 246)
DRONE_FILL = (28, 86, 132)
DRONE_GLOW = (80, 196, 255, 70)


class DroneSimWindow(arcade.Window):
    """Arcade window that renders and controls the drone simulation."""

    def __init__(
        self,
        graph: Graph,
        start: Zone,
        end: Zone,
        paths: list[tuple[float, list[str]]],
        nb_drones: int,
    ) -> None:
        """Initialize the simulation window and fit the map in view."""
        super().__init__(
            WINDOW_WIDTH, WINDOW_HEIGHT, "FLY-IN  ·  Fleet Command",
            resizable=True,
        )
        arcade.set_background_color(BG)

        self.graph = graph
        self.start = start
        self.end = end
        self.paths = paths
        self.nb_drones = nb_drones

        self.simulation: Simulation | None = None
        self.turn_number = 0
        self.last_turn_log: list[str] = []
        self.finished = False

        self.camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()

        self.keys_held: set[int] = set()
        self._dragging = False

        self._reset_simulation()
        self._fit_view()

    def _reset_simulation(self) -> None:
        """Reset zone counts and recreate the simulation."""
        for zone in self.graph.zones.values():
            zone.current_drones = self.nb_drones if zone.is_start else 0
        for conn in self.graph.connections:
            conn.current_drones = 0

        self.simulation = Simulation(
            self.graph, self.paths, nb_drones=self.nb_drones,
        )

        self.simulation.creat_drones(start_zone=self.start)

        self.turn_number = 0
        self.last_turn_log = []
        self.finished = False

    def get_color(self, zone_color: str) -> tuple[int, int, int]:
        """Zone.color can be a named arcade color string ('GREEN')."""
        color = getattr(arcade.color, zone_color.upper(), None)

        if not color:
            return cast(tuple[int, int, int], arcade.color.GRAY)

        return cast(tuple[int, int, int], color)

    def zone_screen_pos(self, zone: Zone) -> tuple[float, float]:
        """Return screen coordinates for a zone."""
        sx = MARGIN_X + zone.x * SPACING_X
        sy = MARGIN_Y + zone.y * SPACING_Y
        return sx, sy

    def connection_midpoint(
        self,
        connection: Connection,
    ) -> tuple[float, float]:
        """Return the screen midpoint of a connection."""
        x1, y1 = self.zone_screen_pos(connection.zone1)
        x2, y2 = self.zone_screen_pos(connection.zone2)
        return (x1 + x2) / 2, (y1 + y2) / 2

    def _map_bounds(self) -> tuple[float, float, float, float]:
        """World-space bounding box that encloses every zone (plus padding
        for their radius/labels), used to fit the whole map -- start to
        end -- in view."""
        pad = ZONE_RADIUS + 56
        xs, ys = [], []
        for zone in self.graph.zones.values():
            x, y = self.zone_screen_pos(zone)
            xs.append(x)
            ys.append(y)
        min_x, max_x = min(xs) - pad, max(xs) + pad
        min_y, max_y = min(ys) - pad, max(ys) + pad
        return min_x, max_x, min_y, max_y

    def _fit_view(self) -> None:
        """Reset the camera to show the entire map (start to end) at once."""
        min_x, max_x, min_y, max_y = self._map_bounds()
        map_w = max(max_x - min_x, 1)
        map_h = max(max_y - min_y, 1)

        usable_w = max(self.width - 40, 1)
        usable_h = max(self.height - HUD_TOP - HUD_BOTTOM - 24, 1)

        multiplier_w = usable_w / map_w
        multiplier_h = usable_h / map_h

        self.camera.zoom = min(multiplier_w, multiplier_h)

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        self.camera.position = (center_x, center_y)

    def _zoom_camera(self, factor: float) -> None:
        """Zoom the camera in or out by the given factor."""
        old_zoom = self.camera.zoom
        new_zoom = old_zoom * factor

        if new_zoom > MAX_ZOOM:
            new_zoom = MAX_ZOOM
        elif new_zoom < MIN_ZOOM:
            new_zoom = MIN_ZOOM

        if new_zoom == old_zoom:
            return

        self.camera.zoom = new_zoom

    def _pan_camera(self, world_dx: float, world_dy: float) -> None:
        """Pan the camera by the given world-space offset."""
        px, py = self.camera.position
        self.camera.position = (px - world_dx, py - world_dy)

    def on_draw(self) -> None:
        """Draw the map, drones, and HUD."""
        self.clear()

        self.camera.use()
        self._draw_world_grid()
        self._draw_route_halos()
        self._draw_connections()
        self._draw_zones()
        self._draw_drones()

        self.gui_camera.use()
        self._draw_hud()

    def _blend(
        self,
        color: tuple[int, ...],
        toward: tuple[int, int, int],
        amount: float,
    ) -> tuple[int, int, int]:
        """Mix a color toward another color."""
        r, g, b = color[:3]
        return (
            int(r * (1 - amount) + toward[0] * amount),
            int(g * (1 - amount) + toward[1] * amount),
            int(b * (1 - amount) + toward[2] * amount),
        )

    def _draw_world_grid(self) -> None:
        """Draw a faint technical grid behind the map."""
        min_x, max_x, min_y, max_y = self._map_bounds()
        pad = 220
        min_x -= pad
        max_x += pad
        min_y -= pad
        max_y += pad
        step = 48
        x = min_x - (min_x % step)
        while x <= max_x:
            arcade.draw_line(x, min_y, x, max_y, GRID, 1)
            x += step
        y = min_y - (min_y % step)
        while y <= max_y:
            arcade.draw_line(min_x, y, max_x, y, GRID, 1)
            y += step

        sx, sy = self.zone_screen_pos(self.start)
        for radius, alpha in ((160, 28), (240, 16), (320, 10)):
            arcade.draw_circle_outline(
                sx, sy, radius, (64, 214, 196, alpha), 1,
            )

    def _draw_route_halos(self) -> None:
        """Draw the planned fleet routes as soft underlays."""
        palettes = (
            (64, 214, 196, 90),
            (92, 196, 255, 55),
            (232, 196, 104, 40),
        )
        for i, (_cost, names) in enumerate(self.paths[:3]):
            color = palettes[i % len(palettes)]
            points = [
                self.zone_screen_pos(self.graph.get_zone(name))
                for name in names
            ]
            for (x1, y1), (x2, y2) in zip(points, points[1:]):
                arcade.draw_line(x1, y1, x2, y2, color, 10)

    def _draw_connections(self) -> None:
        """Draw connections and their capacity labels."""
        for conn in self.graph.connections:
            x1, y1 = self.zone_screen_pos(conn.zone1)
            x2, y2 = self.zone_screen_pos(conn.zone2)

            full = not conn.con_has_capacity()
            core = LINE_HOT if full else (118, 148, 176)
            arcade.draw_line(x1, y1, x2, y2, LINE_GLOW, LINE_WIDTH + 8)
            arcade.draw_line(x1, y1, x2, y2, core, LINE_WIDTH)

            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            label = f"{conn.current_drones}/{conn.max_link_capacity}"
            chip_w, chip_h = 28, 13
            arcade.draw_lrbt_rectangle_filled(
                mx - chip_w, mx + chip_w, my - chip_h, my + chip_h, INK,
            )
            arcade.draw_lrbt_rectangle_outline(
                mx - chip_w, mx + chip_w, my - chip_h, my + chip_h,
                GOLD if full else ACCENT, 1.5,
            )
            arcade.draw_text(
                label, mx, my, GOLD if full else PAPER, 11,
                anchor_x="center", anchor_y="center", bold=True,
            )

    def _hexagon(
        self, x: float, y: float, radius: float,
    ) -> list[tuple[float, float]]:
        """Return flat-top hexagon vertices around a point."""
        points: list[tuple[float, float]] = []
        for i in range(6):
            angle = pi / 6 + i * pi / 3
            points.append((x + radius * cos(angle), y + radius * sin(angle)))
        return points

    def _draw_zones(self) -> None:
        """Draw zones with labels and occupancy counts."""
        for zone in self.graph.zones.values():
            x, y = self.zone_screen_pos(zone)
            base = self.get_color(zone.color)
            fill = self._blend(base, BG[:3], 0.42)
            rim = self._blend(base, PAPER, 0.15)

            if zone.is_blocked():
                fill = self._blend(base, (40, 12, 16), 0.45)
                rim = DANGER

            arcade.draw_circle_filled(x, y, ZONE_RADIUS + 10, (*fill, 40))
            arcade.draw_circle_filled(x, y, ZONE_RADIUS, fill)
            arcade.draw_circle_filled(
                x, y + 10, ZONE_RADIUS * 0.72, (*PAPER, 18),
            )

            if zone.is_start:
                arcade.draw_circle_outline(
                    x, y, ZONE_RADIUS + 8, GOLD, 2,
                )
            elif zone.is_end:
                arcade.draw_circle_outline(
                    x, y, ZONE_RADIUS + 8, ACCENT, 2,
                )

            outline_width = 5 if (zone.is_start or zone.is_end) else 2.5
            arcade.draw_circle_outline(
                x, y, ZONE_RADIUS, rim, outline_width,
            )
            arcade.draw_circle_outline(
                x, y, ZONE_RADIUS - 7, (255, 255, 255, 28), 1,
            )

            if zone.is_blocked():
                r = ZONE_RADIUS * 0.52
                arcade.draw_line(x - r, y - r, x + r, y + r, DANGER, 3)
                arcade.draw_line(x - r, y + r, x + r, y - r, DANGER, 3)

            arcade.draw_text(
                zone.name, x, y + ZONE_RADIUS + 10, PAPER, 14,
                anchor_x="center", anchor_y="bottom", bold=True,
            )

            if zone.is_start:
                tag = "ORIGIN"
            elif zone.is_end:
                tag = "TARGET"
            else:
                tag = zone.type.upper()

            tag_color = GOLD if zone.is_start else (
                ACCENT if zone.is_end else MUTED
            )
            arcade.draw_text(
                tag, x, y - ZONE_RADIUS - 6, tag_color, 10,
                anchor_x="center", anchor_y="top", bold=True,
            )

            occ_color = GOLD if not zone.zone_has_capacity() else PAPER
            arcade.draw_text(
                f"{zone.current_drones}/{zone.max_drones}", x, y - 2,
                occ_color, 20, anchor_x="center", anchor_y="center",
                bold=True,
            )

    def _draw_drones(self) -> None:
        """Draw all active drones on the map."""
        assert self.simulation is not None
        grouped: dict[
            tuple[float, float], list[tuple[Drone, tuple[float, float]]]
        ] = defaultdict(list)

        for drone in self.simulation.drones:
            if drone.in_the_restricted_con:
                assert drone.path is not None
                next_zone = self.graph.get_zone(drone.path[drone.paths_index])
                conn = self.graph.get_connection(
                    drone.current_zone.name, next_zone.name,
                )
                pos = self.connection_midpoint(conn)
            else:
                pos = self.zone_screen_pos(drone.current_zone)
            grouped[(round(pos[0], 1), round(pos[1], 1))].append(
                (drone, pos),
            )

        for cluster in grouped.values():
            n = len(cluster)
            for i, (drone, (bx, by)) in enumerate(cluster):
                dx, dy = bx, by
                if n > 1:
                    angle = (2 * pi * i) / n
                    spread = 18 if n < 6 else 24
                    dx += cos(angle) * spread
                    dy += sin(angle) * spread

                glow = self._hexagon(dx, dy, DRONE_RADIUS + 6)
                body = self._hexagon(dx, dy, DRONE_RADIUS)
                arcade.draw_polygon_filled(glow, DRONE_GLOW)
                arcade.draw_polygon_filled(body, DRONE_FILL)
                arcade.draw_polygon_outline(body, CYAN, 1.5)
                arcade.draw_text(
                    str(drone.id), dx, dy, PAPER, 9,
                    anchor_x="center", anchor_y="center", bold=True,
                )

    def _draw_panel(
        self,
        left: float,
        right: float,
        bottom: float,
        top: float,
        accent: tuple[int, int, int] = ACCENT,
    ) -> None:
        """Draw a glass HUD panel with a thin accent edge."""
        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, INK)
        arcade.draw_lrbt_rectangle_outline(
            left, right, bottom, top, (255, 255, 255, 22), 1,
        )
        arcade.draw_lrbt_rectangle_filled(
            left, left + 3, bottom, top, (*accent, 220),
        )

    def _draw_keycap(self, x: float, y: float, key: str) -> float:
        """Draw a small keycap and return the next x offset."""
        width = 10 + 7.2 * len(key)
        arcade.draw_lrbt_rectangle_filled(
            x, x + width, y - 9, y + 11, (28, 36, 52),
        )
        arcade.draw_lrbt_rectangle_outline(
            x, x + width, y - 9, y + 11, (90, 110, 138), 1,
        )
        arcade.draw_text(
            key, x + width / 2, y + 1, PAPER, 10,
            anchor_x="center", anchor_y="center", bold=True,
        )
        return x + width + 8

    def _draw_hud(self) -> None:
        """Draw the status bar and control hints."""
        assert self.simulation is not None
        w, h = self.width, self.height

        arcade.draw_lrbt_rectangle_filled(
            0, w, h - HUD_TOP, h, (6, 8, 14, 210),
        )
        arcade.draw_lrbt_rectangle_filled(
            0, w, 0, HUD_BOTTOM, (6, 8, 14, 210),
        )
        arcade.draw_lrbt_rectangle_filled(
            0, w, h - HUD_TOP, h - HUD_TOP + 1, (*ACCENT, 90),
        )
        arcade.draw_lrbt_rectangle_filled(
            0, w, HUD_BOTTOM - 1, HUD_BOTTOM, (255, 255, 255, 18),
        )

        self._draw_panel(16, 250, h - 74, h - 14, GOLD)
        arcade.draw_text(
            "FLY-IN", 32, h - 32, GOLD, 18,
            anchor_y="center", bold=True,
        )
        arcade.draw_text(
            "FLEET COMMAND", 32, h - 54, MUTED, 10, anchor_y="center",
        )

        self._draw_panel(266, 430, h - 74, h - 14)
        arcade.draw_text("TURN", 282, h - 28, MUTED, 10, anchor_y="center")
        arcade.draw_text(
            str(self.turn_number), 282, h - 54, PAPER, 22,
            anchor_y="center", bold=True,
        )

        status = "COMPLETE" if self.finished else "IN FLIGHT"
        status_color = ACCENT if self.finished else CYAN
        self._draw_panel(446, 640, h - 74, h - 14, status_color)
        arcade.draw_text("STATUS", 462, h - 28, MUTED, 10, anchor_y="center")
        arcade.draw_text(
            status, 462, h - 54, status_color, 16,
            anchor_y="center", bold=True,
        )

        arrived = sum(1 for drone in self.simulation.drones if drone.finished)
        self._draw_panel(656, 860, h - 74, h - 14, CYAN)
        arcade.draw_text("ARRIVED", 672, h - 28, MUTED, 10, anchor_y="center")
        arcade.draw_text(
            f"{arrived} / {self.nb_drones}", 672, h - 54, PAPER, 18,
            anchor_y="center", bold=True,
        )

        self._draw_panel(876, w - 16, h - 74, h - 14)
        arcade.draw_text("ZOOM", 892, h - 28, MUTED, 10, anchor_y="center")
        arcade.draw_text(
            f"{self.camera.zoom:.2f}×", 892, h - 54, PAPER, 18,
            anchor_y="center", bold=True,
        )

        y = 28.0
        x = 20.0
        arcade.draw_text("CONTROLS", x, y + 14, MUTED, 9, anchor_y="center")
        x = self._draw_keycap(x, y, "SPACE")
        arcade.draw_text("step", x, y, MUTED, 11, anchor_y="center")
        x += 52
        x = self._draw_keycap(x, y, "R")
        arcade.draw_text("reset", x, y, MUTED, 11, anchor_y="center")
        x += 58
        x = self._draw_keycap(x, y, "0")
        arcade.draw_text("fit map", x, y, MUTED, 11, anchor_y="center")
        x += 70
        x = self._draw_keycap(x, y, "+")
        x = self._draw_keycap(x - 4, y, "-")
        arcade.draw_text("zoom", x, y, MUTED, 11, anchor_y="center")
        x += 58
        arcade.draw_text(
            "drag  ·  arrows to pan", x, y, MUTED, 11, anchor_y="center",
        )

        if self.last_turn_log:
            log = "   ".join(self.last_turn_log[-4:])
            arcade.draw_text(
                log, w - 20, y, MUTED, 10,
                anchor_x="right", anchor_y="center",
            )

    def on_key_press(self, key: int, modifiers: int) -> None:
        """Handle keyboard input for simulation control."""
        self.keys_held.add(key)

        if key == arcade.key.SPACE:
            if not self.finished:
                assert self.simulation is not None
                turn_log, finished = self.simulation.step_turn()
                print(f"Turn {self.turn_number + 1}: {' '.join(turn_log)}")
                self.turn_number += 1
                self.last_turn_log = turn_log
                self.finished = finished

        elif key == arcade.key.R:
            self._reset_simulation()

        elif key in (arcade.key.NUM_0, arcade.key.KEY_0):
            self._fit_view()

        elif key in (arcade.key.PLUS, arcade.key.NUM_ADD):
            self._zoom_camera(ZOOM_STEP)

        elif key in (arcade.key.MINUS, arcade.key.NUM_SUBTRACT):
            self._zoom_camera(1 / ZOOM_STEP)

        elif key == arcade.key.ESCAPE:
            arcade.close_window()

    def on_key_release(self, key: int, modifiers: int) -> None:
        """Track released keys for continuous panning."""
        self.keys_held.discard(key)

    def on_update(self, delta_time: float) -> None:
        """Update camera position while arrow keys are held."""
        dx = dy = 0.0
        if arcade.key.LEFT in self.keys_held:
            dx -= 1
        if arcade.key.RIGHT in self.keys_held:
            dx += 1
        if arcade.key.UP in self.keys_held:
            dy += 1
        if arcade.key.DOWN in self.keys_held:
            dy -= 1

        if dx or dy:
            step = PAN_SPEED * delta_time / self.camera.zoom
            self._pan_camera(-dx * step, -dy * step)

    def on_mouse_press(
        self,
        x: float,
        y: float,
        button: int,
        modifiers: int,
    ) -> None:
        """Start panning when the left mouse button is pressed."""
        if button == arcade.MOUSE_BUTTON_LEFT:
            self._dragging = True

    def on_mouse_release(
        self,
        x: float,
        y: float,
        button: int,
        modifiers: int,
    ) -> None:
        """Stop panning when the left mouse button is released."""
        if button == arcade.MOUSE_BUTTON_LEFT:
            self._dragging = False

    def on_mouse_drag(
        self,
        x: float,
        y: float,
        dx: float,
        dy: float,
        buttons: int,
        modifiers: int,
    ) -> None:
        """Pan the camera while dragging with the mouse."""
        if self._dragging:
            self._pan_camera(dx, dy)

    def on_resize(self, width: int, height: int) -> None:
        """Refit cameras and view when the window is resized."""
        super().on_resize(width, height)
        self.camera.match_window(position=False)
        self.gui_camera.match_window(position=True)
        self._fit_view()
