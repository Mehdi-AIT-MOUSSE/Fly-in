
from .graph import Graph, Zone, Connection
from .similation import Simulation

import arcade

SPACING_X = 200        # pixel distance between grid columns
SPACING_Y = 170         # pixel distance between grid rows
MARGIN_X = 150          # left/right margin so edge zones aren't clipped
MARGIN_Y = 150          # top/bottom margin (also leaves room for the HUD)
ZONE_RADIUS = 46
DRONE_RADIUS = 16
LINE_WIDTH = 3
BACK_GROUND_COLOR = arcade.color.BLACK

# The window is a fixed, comfortable size -- independent of how large the map
# is. Large maps (more zones than fit on screen at zoom 1.0) are explored with
# the mouse wheel / keyboard zoom and pan controls added to DroneSimWindow below.
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 680
HUD_HEIGHT = 60          # reserved band at the top of the screen for the HUD

MIN_ZOOM = 0.15
MAX_ZOOM = 4.0
ZOOM_STEP = 1.1          # multiplicative zoom per scroll notch / key press
PAN_SPEED = 600.0        # world units per second, for keyboard panning

TYPE_LABELS = {
    "normal": "normal",
    "restricted": "restricted (2-turn dwell)",
    "priority": "priority (fast)",
    "blocked": "blocked",
}


def resolve_color(color):
    """Zone.color can be a named arcade color string ('GREEN') or an
    already-resolved RGB(A) tuple -- support both."""
    if isinstance(color, str):
        resolved = getattr(arcade.color, color.upper(), None)
        if resolved is not None:
            return resolved
        return arcade.color.GRAY
    return color


class DroneSimWindow(arcade.Window):
    def __init__(self, graph: Graph, start: Zone, end: Zone, paths, nb_drones: int):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, "Drone Fleet Simulation", resizable=True)
        arcade.set_background_color(BACK_GROUND_COLOR)

        self.graph = graph
        self.start = start
        self.end = end
        self.paths = paths
        self.nb_drones = nb_drones

        self.simulation = None
        self.turn_number = 0
        self.last_turn_log = []
        self.finished = False

        self.camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()

        self.keys_held = set()
        self._dragging = False
        self.min_zoom = MIN_ZOOM

        self._reset_simulation()
        self._fit_view()

    # ---- setup / reset -----------------------------------------------------

    def _reset_simulation(self):
        for zone in self.graph.zones.values():
            zone.current_drones = self.nb_drones if zone.is_start else 0
        for conn in self.graph.connections:
            conn.current_drones = 0

        self.simulation = Simulation(self.graph, self.paths, nb_drones=self.nb_drones)

        self.simulation.creat_drones(start_zone=self.start)

        self.turn_number = 0
        self.last_turn_log = []
        self.finished = False

    # ---- coordinate mapping -------------------------------------------------

    def zone_screen_pos(self, zone: Zone):
        sx = MARGIN_X + zone.x * SPACING_X
        sy = MARGIN_Y + zone.y * SPACING_Y
        return sx, sy

    def connection_midpoint(self, connection: Connection):
        x1, y1 = self.zone_screen_pos(connection.zone1)
        x2, y2 = self.zone_screen_pos(connection.zone2)
        return (x1 + x2) / 2, (y1 + y2) / 2

    # ---- camera: fit / zoom / pan -------------------------------------------

    def _map_bounds(self):
        """World-space bounding box that encloses every zone (plus padding
        for their radius/labels), used to fit the whole map -- start to
        end -- in view."""
        pad = ZONE_RADIUS + 40
        xs, ys = [], []
        for zone in self.graph.zones.values():
            x, y = self.zone_screen_pos(zone)
            xs.append(x)
            ys.append(y)
        min_x, max_x = min(xs) - pad, max(xs) + pad
        min_y, max_y = min(ys) - pad, max(ys) + pad
        return min_x, max_x, min_y, max_y

    def _fit_view(self):
        """Reset the camera to show the entire map (start to end) at once."""
        min_x, max_x, min_y, max_y = self._map_bounds()
        map_w = max(max_x - min_x, 1)
        map_h = max(max_y - min_y, 1)

        # Leave room for the HUD band at the top of the window.
        usable_h = max(self.height - HUD_HEIGHT, 1)
        fit_zoom = min(self.width / map_w, usable_h / map_h)
        fit_zoom = min(fit_zoom, MAX_ZOOM)
        self.min_zoom = min(MIN_ZOOM, fit_zoom * 0.8)

        self.camera.zoom = fit_zoom
        # shift the vertical center down a touch so the HUD band doesn't
        # cover the top of the map
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2 - (HUD_HEIGHT / 2) / fit_zoom
        self.camera.position = (center_x, center_y)

    def _zoom_camera(self, factor, anchor_screen):
        """Zoom in/out by `factor`, keeping the world point under
        `anchor_screen` (screen-space x, y) fixed in place."""
        old_zoom = self.camera.zoom
        new_zoom = min(MAX_ZOOM, max(self.min_zoom, old_zoom * factor))
        if new_zoom == old_zoom:
            return

        before = self.camera.unproject(anchor_screen)
        self.camera.zoom = new_zoom
        after = self.camera.unproject(anchor_screen)

        px, py = self.camera.position
        self.camera.position = (px + (before.x - after.x), py + (before.y - after.y))

    def _pan_camera(self, world_dx, world_dy):
        px, py = self.camera.position
        self.camera.position = (px - world_dx, py - world_dy)

    # ---- drawing --------------------------------------------------------

    def on_draw(self):
        self.clear()

        self.camera.use()
        self._draw_connections()
        self._draw_zones()
        self._draw_drones()

        self.gui_camera.use()
        self._draw_hud()

    def _draw_connections(self):
        for conn in self.graph.connections:
            x1, y1 = self.zone_screen_pos(conn.zone1)
            x2, y2 = self.zone_screen_pos(conn.zone2)

            full = not conn.con_has_capacity()
            line_color = arcade.color.GREEN if full else arcade.color.LIGHT_GRAY
            arcade.draw_line(x1, y1, x2, y2, line_color, LINE_WIDTH)

            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            label = f"{conn.current_drones}/{conn.max_link_capacity}"

            # small background chip so the capacity label is readable over the line
            arcade.draw_lrbt_rectangle_filled(
                mx - 22, mx + 22, my - 11, my + 11, arcade.color.BLACK
            )
            arcade.draw_lrbt_rectangle_outline(
                mx - 22, mx + 22, my - 11, my + 11, line_color, 1
            )
            arcade.draw_text(
                label, mx, my, arcade.color.WHITE, 12,
                anchor_x="center", anchor_y="center", bold=True
            )

    def _draw_zones(self):
        for zone in self.graph.zones.values():
            x, y = self.zone_screen_pos(zone)
            zone_color = resolve_color(zone.color)
            arcade.draw_circle_filled(x, y, ZONE_RADIUS, zone_color)

            if not zone.is_blocked():
                outline_color = arcade.color.WHITE
            else:
                outline_color = arcade.color.RED
            outline_width = 4 if (zone.is_start or zone.is_end) else 2
            arcade.draw_circle_outline(x, y, ZONE_RADIUS,
                                       outline_color, outline_width)

            if zone.is_blocked():
                # draw an X across blocked zones
                r = ZONE_RADIUS * 0.65
                arcade.draw_line(x - r, y - r, x + r, y + r,
                                 arcade.color.RED, 3)
                arcade.draw_line(x - r, y + r, x + r, y - r,
                                 arcade.color.RED, 3)

            arcade.draw_text(
                zone.name, x, y + ZONE_RADIUS + 6, arcade.color.WHITE, 15,
                anchor_x="center", anchor_y="bottom", bold=True
            )

            if zone.is_start:
                tag = "START"
            elif zone.is_end:
                tag = "END"
            else:
                tag = zone.type

            arcade.draw_text(
                tag, x, y - ZONE_RADIUS - 4, arcade.color.LIGHT_GRAY, 11,
                anchor_x="center", anchor_y="top",
            )

            if not zone.zone_has_capacity():
                occ_color = arcade.color.GREEN
            else:
                occ_color = arcade.color.WHITE

            arcade.draw_text(
                f"{zone.current_drones}/{zone.max_drones}", x, y, occ_color,
                13, anchor_x="center", anchor_y="center", bold=True,
            )

    def _draw_drones(self):
        for drone in self.simulation.drones:
            if drone.in_the_restricted_con:
                next_zone = self.graph.get_zone(drone.path[drone.paths_index])
                conn = self.graph.get_connection(drone.current_zone.name,
                                                 next_zone.name)
                dx, dy = self.connection_midpoint(conn)
            else:
                dx, dy = self.zone_screen_pos(drone.current_zone)

            color = arcade.color.AIR_FORCE_BLUE
            arcade.draw_circle_filled(dx, dy, DRONE_RADIUS, color)

            arcade.draw_text(str(drone.id), dx, dy, arcade.color.WHITE, 9,
                             anchor_x="center", anchor_y="center", bold=True)

    def _draw_hud(self):
        arcade.draw_lrbt_rectangle_filled(
            0, self.width, self.height - HUD_HEIGHT, self.height, (0, 0, 0,
                                                                   180)
        )

        top = self.height - 12
        status = "FINISHED" if self.finished else "RUNNING"
        arcade.draw_text(
            f"Turn {self.turn_number}   |   Status: {status}   "
            f"|   Zoom: {self.camera.zoom:.2f}x   |   "
            f"SPACE = step turn, R = reset",
            14, top, arcade.color.WHITE, 14, anchor_y="top", bold=True,
        )

        arcade.draw_text(
            "Zoom: + - keys   |   Pan: drag with mouse or arrow keys "
            " |  Num 0: fit whole map",
            14, top - 42, arcade.color.LIGHT_GRAY, 12, anchor_y="top",
        )

    # ---- input: keyboard ------------------------------------------------

    def on_key_press(self, key, modifiers):
        self.keys_held.add(key)

        if key == arcade.key.SPACE:
            if not self.finished:
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
            self._zoom_camera(ZOOM_STEP, (self.width / 2, self.height / 2))
        elif key in (arcade.key.MINUS, arcade.key.NUM_SUBTRACT):
            self._zoom_camera(1 / ZOOM_STEP, (self.width / 2, self.height / 2))
        elif key == arcade.key.ESCAPE:
            arcade.close_window()

    def on_key_release(self, key, modifiers):
        self.keys_held.discard(key)

    def on_update(self, delta_time: float):
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

    # ---- input: mouse (wheel zoom, drag pan) ---------------------------------

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self._dragging = True

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self._dragging = False

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self._dragging:
            self._pan_camera(dx / self.camera.zoom, dy / self.camera.zoom)

    # ---- window resize -------------------------------------------------------

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.camera.match_window(position=False)
        self.gui_camera.match_window(position=True)


def run_display(graph, start, end, paths, nb_drones):
    DroneSimWindow(graph, start, end, paths, nb_drones)
    arcade.run()
