"""

"""

import arcade
import math
import time
from enum import Enum
from copy import deepcopy

SCREEN_WIDTH  = 1000
SCREEN_HEIGHT = 760
SCREEN_TITLE  = "Fanorontelo Telo"

COLOR_BG_TOP        = (20,  24,  38)
COLOR_BG_BOTTOM     = (10,  12,  20)
COLOR_BOARD_TOP     = (92,  64,  38)
COLOR_BOARD_SIDE    = (52,  36,  22)
COLOR_BOARD_EDGE    = (140, 102, 58)
COLOR_LINE          = (224, 196, 140)
COLOR_LINE_SHADOW   = (40,  28,  16)
COLOR_NODE_IDLE     = (224, 196, 140)
COLOR_NODE_HOVER    = (255, 224, 130)
COLOR_NODE_VALID    = (110, 220, 150)

# Skins disponibles
class PieceSkin(Enum):
    CIRCLE = "Cercle"
    SQUARE = "Carré"
    DIAMOND = "Diamant"
    STAR = "Étoile"
    HEXAGON = "Hexagone"

PLAYER_COLORS = {
    1: {"base": (224,  86,  86), "light": (255, 150, 130), "dark": (120, 30,  30),  "name": "Rouge"},
    2: {"base": ( 70, 150, 235), "light": (150, 210, 255), "dark": ( 20, 60, 120),  "name": "Bleu"},
}

# Palettes de couleurs alternatives pour les skins
COLOR_PALETTES = {
    "Classique": {
        1: {"base": (224, 86, 86), "light": (255, 150, 130), "dark": (120, 30, 30)},
        2: {"base": (70, 150, 235), "light": (150, 210, 255), "dark": (20, 60, 120)},
    },
    "Or & Argent": {
        1: {"base": (218, 165, 32), "light": (255, 215, 0), "dark": (139, 105, 20)},
        2: {"base": (192, 192, 192), "light": (220, 220, 220), "dark": (128, 128, 128)},
    },
    "Vert & Violet": {
        1: {"base": (50, 205, 50), "light": (100, 255, 100), "dark": (0, 100, 0)},
        2: {"base": (138, 43, 226), "light": (180, 100, 255), "dark": (75, 0, 130)},
    },
    "Rose & Cyan": {
        1: {"base": (255, 105, 180), "light": (255, 150, 210), "dark": (200, 50, 120)},
        2: {"base": (0, 255, 255), "light": (100, 255, 255), "dark": (0, 150, 150)},
    },
    "Orange & Noir": {
        1: {"base": (255, 140, 0), "light": (255, 180, 50), "dark": (200, 100, 0)},
        2: {"base": (50, 50, 50), "light": (80, 80, 80), "dark": (20, 20, 20)},
    },
}

PIECE_RADIUS = 28
NODE_RADIUS  = 16
HOVER_RADIUS = 24

# Durée de l'animation de vol (secondes)
FLY_DURATION = 0.38
# Hauteur max du vol (pixels)
FLY_HEIGHT   = 90

# ----------------------------------------------------------------------
# GÉOMÉTRIE DU PLATEAU
# ----------------------------------------------------------------------

NODE_IDS = ["NO", "N", "NE", "O", "C", "E", "SO", "S", "SE"]

RAW_POSITIONS = {
    "NO": (-1.0,  1.0), "N":  ( 0.0,  1.0), "NE": ( 1.0,  1.0),
    "O":  (-1.0,  0.0), "C":  ( 0.0,  0.0), "E":  ( 1.0,  0.0),
    "SO": (-1.0, -1.0), "S":  ( 0.0, -1.0), "SE": ( 1.0, -1.0),
}

EDGES = [
    ("NO","N"),  ("N","NE"),
    ("SO","S"),  ("S","SE"),
    ("NO","O"),  ("O","SO"),
    ("NE","E"),  ("E","SE"),
    ("N","C"),   ("C","S"),
    ("O","C"),   ("C","E"),
    ("NO","C"),  ("C","SE"),
    ("NE","C"),  ("C","SO"),
]

WINNING_LINES = [
    ("NO","N","NE"),
    ("SO","S","SE"),
    ("NO","O","SO"),
    ("NE","E","SE"),
    ("N","C","S"),
    ("O","C","E"),
    ("NO","C","SE"),
    ("NE","C","SO"),
]

ADJACENCY = {n: set() for n in NODE_IDS}
for _a, _b in EDGES:
    ADJACENCY[_a].add(_b)
    ADJACENCY[_b].add(_a)

# Placement initial :  Joueur 1 (Rouge) en haut, Joueur 2 (Bleu) en bas
INITIAL_PLACEMENT = {
    "NO": 1, "N": 1, "NE": 1,
    "O":  None, "C": None, "E": None,
    "SO": 2, "S": 2, "SE": 2,
}


def project(pos, cx, cy, scale, tilt=0.62):
    x, y = pos
    return cx + x * scale, cy + y * scale * tilt


# ----------------------------------------------------------------------
# ANIMATION DE VOL
# ----------------------------------------------------------------------

class FlyAnimation:

    def __init__(self, src_pos, dst_pos, player, duration=FLY_DURATION):
        self.src  = src_pos
        self.dst  = dst_pos
        self.player = player
        self.dur  = duration
        self.t    = 0.0       # temps écoulé
        self.done = False

    def update(self, dt):
        self.t = min(self.t + dt, self.dur)
        if self.t >= self.dur:
            self.done = True

    @property
    def progress(self):
        """Progression lissée 0→1 (ease-in-out)."""
        p = self.t / self.dur
        return p * p * (3 - 2 * p)   # smoothstep

    @property
    def current_pos(self):
        p   = self.progress
        x   = self.src[0] + (self.dst[0] - self.src[0]) * p
        y   = self.src[1] + (self.dst[1] - self.src[1]) * p
        arc = math.sin(p * math.pi) * FLY_HEIGHT   # arc parabolique
        return x, y + arc

    @property
    def shadow_alpha(self):
        # l'ombre s'estompe au milieu du vol
        p = self.progress
        return int(90 * (1 - math.sin(p * math.pi) * 0.7))


# ----------------------------------------------------------------------
# BOUTON UNDO
# ----------------------------------------------------------------------

class UndoButton:
    def __init__(self, x, y, size=40):
        self.x = x
        self.y = y
        self.size = size
        self.hovered = False
        self.clicked = False
        
    def draw(self, enabled=True):
        # Couleurs
        if not enabled:
            bg_color = (60, 60, 70, 150)
            icon_color = (100, 100, 110, 150)
            border_color = (60, 60, 70, 150)
        elif self.clicked:
            bg_color = (70, 80, 100, 220)
            icon_color = (200, 200, 210)
            border_color = (150, 170, 200)
        elif self.hovered:
            bg_color = (60, 70, 90, 220)
            icon_color = (230, 230, 240)
            border_color = (180, 200, 230)
        else:
            bg_color = (40, 45, 60, 200)
            icon_color = (200, 200, 210)
            border_color = (80, 85, 100)
        
        # Fond du bouton (cercle)
        arcade.draw_circle_filled(self.x, self.y, self.size//2, bg_color)
        arcade.draw_circle_outline(self.x, self.y, self.size//2, border_color, 2)
        
        # Icône de retour (flèche courbée)
        if enabled:
            # Flèche courbée vers la gauche
            radius = self.size * 0.35
            
            # Arc de cercle
            start_angle = math.pi * 0.1
            end_angle = math.pi * 0.9
            
            # Dessiner l'arc
            points = []
            steps = 20
            for i in range(steps + 1):
                t = i / steps
                angle = start_angle + (end_angle - start_angle) * t
                px = self.x + radius * math.cos(angle - math.pi/2)
                py = self.y + radius * math.sin(angle - math.pi/2)
                points.append((px, py))
            
            # Corps de la flèche
            for i in range(len(points) - 1):
                arcade.draw_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], icon_color, 3)
            
            # Pointe de la flèche
            tip_x = self.x - radius * 0.6
            tip_y = self.y
            arcade.draw_line(tip_x, tip_y, tip_x + 10, tip_y - 7, icon_color, 3)
            arcade.draw_line(tip_x, tip_y, tip_x + 10, tip_y + 7, icon_color, 3)
            
            # Petite barre verticale au début de la flèche
            start_x = self.x + radius * 0.2
            start_y_bottom = self.y + radius * 0.8
            start_y_top = self.y - radius * 0.2
            arcade.draw_line(start_x, start_y_bottom, start_x, start_y_top, icon_color, 3)
            
            # Texte "UNDO" en dessous
            arcade.draw_text(
                "UNDO", self.x, self.y - self.size//2 - 12,
                icon_color, 10, anchor_x="center", bold=True
            )
        else:
            # Version désactivée (grisée)
            arcade.draw_text(
                "⤺", self.x, self.y - 10,
                icon_color, 20, anchor_x="center"
            )
            arcade.draw_text(
                "UNDO", self.x, self.y - self.size//2 - 12,
                icon_color, 10, anchor_x="center", bold=True
            )
    
    def on_mouse_motion(self, x, y):
        self.hovered = (x - self.x)**2 + (y - self.y)**2 <= (self.size//2)**2
        return self.hovered
    
    def on_mouse_press(self, x, y):
        if (x - self.x)**2 + (y - self.y)**2 <= (self.size//2)**2:
            self.clicked = True
            return True
        return False
    
    def on_mouse_release(self):
        self.clicked = False


# ----------------------------------------------------------------------
# VUE PRINCIPALE
# ----------------------------------------------------------------------

class FanoronteloView(arcade.View):
    def __init__(self):
        super().__init__()
        self.board_cx = SCREEN_WIDTH  / 2
        self.board_cy = SCREEN_HEIGHT / 2 + 10
        self.scale    = 230

        self.node_screen_pos = {}
        self.update_node_positions()

        # Animation de vol courante (None si aucune)
        self.fly_anim: FlyAnimation | None = None
        # Noeud source du vol (caché pendant l'animation)
        self.flying_from: str | None = None
        # Noeud destination (destiné à recevoir le pion après le vol)
        self.flying_to:   str | None = None

        self.time_elapsed = 0.0
        self.piece_bounce: dict[str, float] = {}

        # Historique pour undo
        self.history: list[dict] = []
        
        # Skins et palettes
        self.current_skin = PieceSkin.CIRCLE
        self.current_palette = "Classique"
        self.show_menu = False
        
        # Bouton Undo
        self.undo_button = UndoButton(SCREEN_WIDTH - 70, SCREEN_HEIGHT - 200)
        
        self.reset_game()

    # ------------------------------------------------------------------
    def update_node_positions(self):
        self.node_screen_pos = {
            n: project(RAW_POSITIONS[n], self.board_cx, self.board_cy, self.scale)
            for n in NODE_IDS
        }

    def on_show_view(self):
        arcade.set_background_color((15, 17, 26))

    # ------------------------------------------------------------------
    def reset_game(self):
        self.board           = dict(INITIAL_PLACEMENT)   # placement initial
        self.current_player  = 1
        self.phase           = "movement"               # on démarre directement en mouvement
        self.selected_node   = None
        self.hovered_node    = None
        self.winner          = None
        self.winning_line    = None
        self.piece_bounce    = {}
        self.fly_anim        = None
        self.flying_from     = None
        self.flying_to       = None
        # Ensemble de nœuds ayant été déplacés au moins une fois par chaque joueur
        self.moved_once: dict[int, set] = {1: set(), 2: set()}
        self.history = []
        self.message = f"Déplacez un pion — Joueur {PLAYER_COLORS[1]['name']}"

    def save_state(self):
        """Sauvegarde l'état actuel pour undo."""
        state = {
            'board': dict(self.board),
            'current_player': self.current_player,
            'moved_once': {1: set(self.moved_once[1]), 2: set(self.moved_once[2])},
            'selected_node': self.selected_node,
            'message': self.message,
        }
        self.history.append(state)
        # Limiter l'historique à 50 coups
        if len(self.history) > 50:
            self.history.pop(0)

    def undo(self):
        """Annule le dernier coup."""
        if not self.history or self.fly_anim is not None or self.winner is not None:
            return
        
        state = self.history.pop()
        self.board = state['board']
        self.current_player = state['current_player']
        self.moved_once = state['moved_once']
        self.selected_node = None
        self.message = f"↩ Annulation — Au tour de {PLAYER_COLORS[self.current_player]['name']}"
        self.winner = None
        self.winning_line = None
        
        # Supprimer l'animation en cours
        self.fly_anim = None
        self.flying_from = None
        self.flying_to = None

    # ------------------------------------------------------------------
    # LOGIQUE
    # ------------------------------------------------------------------
    def check_winner(self, player):
        """Retourne la ligne gagnante si le joueur a 3 pions alignés
        ET que chacun de ses pions a été déplacé au moins une fois."""
        # Vérifier que tous les pions du joueur ont bougé
        player_nodes = [n for n in NODE_IDS if self.board[n] == player]
        if not all(n in self.moved_once[player] for n in player_nodes):
            return None
        for line in WINNING_LINES:
            if all(self.board[n] == player for n in line):
                return line
        return None

    def node_at_pixel(self, x, y):
        best, best_d = None, 1e9
        for n, (nx, ny) in self.node_screen_pos.items():
            d = math.hypot(x - nx, y - ny)
            if d < best_d:
                best_d, best = d, n
        if best_d <= max(PIECE_RADIUS, NODE_RADIUS) + 12:
            return best
        return None

    def valid_targets(self, node):
        """Cases où le pion sélectionné peut aller."""
        if node is None:
            return set()
        return {n for n in ADJACENCY[node] if self.board[n] is None}

    def try_select_or_move(self, node):
        """Gestion du clic pendant la phase de déplacement."""
        if self.fly_anim is not None:
            return   # on ne clique pas pendant un vol

        if self.selected_node is None:
            if self.board[node] == self.current_player:
                self.selected_node = node
            return

        # Clic sur le même pion → désélection
        if node == self.selected_node:
            self.selected_node = None
            return

        # Clic sur un autre pion du même joueur → changer la sélection
        if self.board[node] == self.current_player:
            self.selected_node = node
            return

        # Clic sur une cible valide → lancer le vol
        if self.board[node] is None and node in ADJACENCY[self.selected_node]:
            self._start_fly(self.selected_node, node)

    def _start_fly(self, src, dst):
        self.save_state()  # Sauvegarder l'état avant le mouvement
        src_pos = self.node_screen_pos[src]
        dst_pos = self.node_screen_pos[dst]
        self.fly_anim    = FlyAnimation(src_pos, dst_pos, self.current_player)
        self.flying_from = src
        self.flying_to   = dst
        self.selected_node = None

    def _finish_fly(self):
        """Applique le mouvement après que l'animation de vol est terminée."""
        src, dst = self.flying_from, self.flying_to
        player = self.board[src]

        self.board[src]  = None
        self.board[dst]  = player
        self.piece_bounce[dst] = self.time_elapsed
        self.moved_once[player].add(dst)

        self.fly_anim    = None
        self.flying_from = None
        self.flying_to   = None

        win_line = self.check_winner(player)
        if win_line:
            self.winner      = player
            self.winning_line = win_line
            self.message = f"🏆 Joueur {PLAYER_COLORS[player]['name']} a gagné !"
            return

        self.switch_player()

    def switch_player(self):
        self.current_player = 2 if self.current_player == 1 else 1
        self.message = (
            f"Au tour de {PLAYER_COLORS[self.current_player]['name']} — "
            "Sélectionnez un pion"
        )

    # ------------------------------------------------------------------
    # DESSIN DES PIONS SELON LE SKIN
    # ------------------------------------------------------------------
    def draw_piece_shape(self, x, y, radius, player, colors, alpha_factor=1.0):
        """Dessine un pion selon le skin sélectionné."""
        alpha = int(255 * alpha_factor)
        dark = (*colors["dark"], alpha)
        base = (*colors["base"], alpha)
        light = (*colors["light"], alpha)
        
        if self.current_skin == PieceSkin.CIRCLE:
            # Pion rond classique
            arcade.draw_circle_filled(x, y, radius * 0.92, base)
            arcade.draw_circle_filled(x - radius*0.32, y + radius*0.38, radius*0.42, light)
            arcade.draw_circle_filled(x - radius*0.45, y + radius*0.50, radius*0.14, (255, 255, 255, alpha))
            arcade.draw_circle_outline(x, y, radius * 0.92, dark, 2)
            
        elif self.current_skin == PieceSkin.SQUARE:
            # Pion carré
            half = radius * 0.75
            points = [(x-half, y-half), (x+half, y-half), (x+half, y+half), (x-half, y+half)]
            arcade.draw_polygon_filled(points, base)
            # Reflet
            reflect = [(x-half*0.6, y+half*0.8), (x+half*0.8, y+half*0.8), (x+half*0.8, y+half*0.4)]
            arcade.draw_polygon_filled(reflect, light)
            arcade.draw_polygon_outline(points, dark, 2)
            
        elif self.current_skin == PieceSkin.DIAMOND:
            # Pion en losange
            points = [(x, y-radius*0.85), (x+radius*0.85, y), (x, y+radius*0.85), (x-radius*0.85, y)]
            arcade.draw_polygon_filled(points, base)
            # Reflet
            reflect = [(x, y-radius*0.5), (x+radius*0.3, y), (x, y+radius*0.2)]
            arcade.draw_polygon_filled(reflect, light)
            arcade.draw_polygon_outline(points, dark, 2)
            
        elif self.current_skin == PieceSkin.STAR:
            # Pion en étoile à 5 branches
            points = []
            for i in range(10):
                angle = i * math.pi / 5 - math.pi / 2
                r = radius * 0.85 if i % 2 == 0 else radius * 0.4
                points.append((x + r * math.cos(angle), y + r * math.sin(angle)))
            arcade.draw_polygon_filled(points, base)
            arcade.draw_polygon_outline(points, dark, 2)
            
        elif self.current_skin == PieceSkin.HEXAGON:
            # Pion hexagonal
            points = []
            for i in range(6):
                angle = i * math.pi / 3 - math.pi / 6
                points.append((x + radius * 0.8 * math.cos(angle), y + radius * 0.8 * math.sin(angle)))
            arcade.draw_polygon_filled(points, base)
            # Reflet
            reflect = [(x, y+radius*0.6), (x+radius*0.3, y+radius*0.3), (x+radius*0.4, y), (x, y+radius*0.4)]
            arcade.draw_polygon_filled(reflect, light)
            arcade.draw_polygon_outline(points, dark, 2)

    # ------------------------------------------------------------------
    # ENTRÉES
    # ------------------------------------------------------------------
    def on_mouse_motion(self, x, y, dx, dy):
        if self.fly_anim is None and not self.show_menu:
            self.hovered_node = self.node_at_pixel(x, y)
            # Mettre à jour le survol du bouton undo
            self.undo_button.on_mouse_motion(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.fly_anim is not None:
            return
        
        # Vérifier le clic sur le bouton undo
        if self.undo_button.on_mouse_press(x, y):
            self.undo()
            return
            
        if self.winner is not None:
            return
            
        # Gestion du menu
        if self.show_menu:
            # Vérifier les clics sur les boutons du menu
            menu_x = SCREEN_WIDTH // 2 - 200
            menu_y = SCREEN_HEIGHT // 2 + 100
            
            # Boutons de skin
            for i, skin in enumerate(PieceSkin):
                btn_y = menu_y - 30 - i * 45
                if (menu_x < x < menu_x + 400 and 
                    btn_y - 20 < y < btn_y + 20):
                    self.current_skin = skin
                    self.show_menu = False
                    return
            
            # Boutons de palette
            palette_start_y = menu_y - 30 - len(PieceSkin) * 45 - 30
            for i, palette_name in enumerate(COLOR_PALETTES.keys()):
                btn_y = palette_start_y - 20 - i * 40
                if (menu_x < x < menu_x + 400 and 
                    btn_y - 18 < y < btn_y + 18):
                    self.current_palette = palette_name
                    # Mettre à jour les couleurs
                    global PLAYER_COLORS
                    PLAYER_COLORS[1] = COLOR_PALETTES[palette_name][1]
                    PLAYER_COLORS[2] = COLOR_PALETTES[palette_name][2]
                    self.show_menu = False
                    return
            
            # Fermer le menu
            if (menu_x + 400 - 60 < x < menu_x + 400 - 20 and 
                menu_y + 20 - 25 < y < menu_y + 20 + 25):
                self.show_menu = False
                return
            
            return
        
        node = self.node_at_pixel(x, y)
        if node is None:
            return
        self.try_select_or_move(node)

    def on_mouse_release(self, x, y, button, modifiers):
        self.undo_button.on_mouse_release()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            self.reset_game()
        elif key == arcade.key.Z and modifiers & arcade.key.MOD_CTRL:
            self.undo()
        elif key == arcade.key.U:
            self.undo()
        elif key == arcade.key.M:
            self.show_menu = not self.show_menu
        elif key == arcade.key.ESCAPE:
            arcade.close_window()

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.board_cx = width  / 2
        self.board_cy = height / 2 + 10
        self.scale    = min(width, height) * 0.32
        self.update_node_positions()
        # Recalculer la position de départ du vol en cours si besoin
        if self.fly_anim and self.flying_from and self.flying_to:
            # Relancer l'animation depuis la position actuelle du pion volant
            prog = self.fly_anim.progress
            remaining = self.fly_anim.dur * (1 - prog)
            new_anim = FlyAnimation(
                self.node_screen_pos[self.flying_from],
                self.node_screen_pos[self.flying_to],
                self.fly_anim.player,
                duration=max(remaining, 0.05)
            )
            new_anim.t = 0.0
            self.fly_anim = new_anim
        
        # Mettre à jour la position du bouton undo
        self.undo_button.x = width - 70
        self.undo_button.y = height - 200

    # ------------------------------------------------------------------
    # MISE À JOUR
    # ------------------------------------------------------------------
    def on_update(self, delta_time):
        self.time_elapsed += delta_time
        if self.fly_anim is not None:
            self.fly_anim.update(delta_time)
            if self.fly_anim.done:
                self._finish_fly()

    # ------------------------------------------------------------------
    # RENDU
    # ------------------------------------------------------------------
    def on_draw(self):
        self.clear()
        self.draw_background()
        self.draw_board_3d()
        self.draw_lines()
        self.draw_nodes_and_pieces()
        self.draw_fly_piece()
        self.draw_hud()
        
        # Dessiner le bouton undo (enabled si historique non vide et pas de victoire)
        enabled = bool(self.history) and self.winner is None and self.fly_anim is None
        self.undo_button.draw(enabled)
        
        if self.show_menu:
            self.draw_menu()

    # ------------------- fond dégradé -----------------------------------
    def draw_background(self):
        steps = 40
        h = self.window.height
        for i in range(steps):
            t = i / steps
            color = tuple(
                int(COLOR_BG_BOTTOM[c] + (COLOR_BG_TOP[c] - COLOR_BG_BOTTOM[c]) * t)
                for c in range(3)
            )
            arcade.draw_lrbt_rectangle_filled(
                0, self.window.width,
                h * t, h * (t + 1/steps),
                color
            )

    # ------------------- plateau pseudo-3D ------------------------------
    def draw_board_3d(self):
        pts   = [self.node_screen_pos[n] for n in ("NO","NE","SE","SO")]
        depth = 26

        side_pts = [(x, y - depth) for x, y in pts]
        n = len(pts)
        for i in range(n):
            p1, p2 = pts[i], pts[(i+1)%n]
            s1, s2 = side_pts[i], side_pts[(i+1)%n]
            arcade.draw_polygon_filled([p1, p2, s2, s1], COLOR_BOARD_SIDE)

        shadow_pts = [(x+14, y-depth-18) for x, y in pts]
        arcade.draw_polygon_filled(shadow_pts, (0, 0, 0, 110))

        margin_pts = self._expand(pts, 1.28)
        arcade.draw_polygon_filled(margin_pts, COLOR_BOARD_TOP)
        arcade.draw_polygon_outline(margin_pts, COLOR_BOARD_EDGE, 4)

        inner_pts = self._expand(pts, 1.12)
        arcade.draw_polygon_outline(inner_pts, COLOR_BOARD_EDGE, 2)

    @staticmethod
    def _expand(pts, factor):
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        return [(cx + (x-cx)*factor, cy + (y-cy)*factor) for x, y in pts]

    # ------------------- lignes ------------------------------------------
    def draw_lines(self):
        for a, b in EDGES:
            p1, p2 = self.node_screen_pos[a], self.node_screen_pos[b]
            arcade.draw_line(p1[0]+2, p1[1]-3, p2[0]+2, p2[1]-3, COLOR_LINE_SHADOW, 5)
            arcade.draw_line(p1[0], p1[1], p2[0], p2[1], COLOR_LINE, 3)

        if self.winning_line:
            pts   = [self.node_screen_pos[n] for n in self.winning_line]
            pulse = 0.5 + 0.5*math.sin(self.time_elapsed * 4)
            glow  = (255, int(210+30*pulse), 90)
            for i in range(len(pts)-1):
                arcade.draw_line(*pts[i], *pts[i+1], glow, 8)

    # ------------------- noeuds + pions ---------------------------------
    def draw_nodes_and_pieces(self):
        targets = self.valid_targets(self.selected_node)

        for n in NODE_IDS:
            # Masquer la source du vol (le pion est en train de voler)
            if n == self.flying_from:
                continue

            x, y     = self.node_screen_pos[n]
            occupant = self.board[n]

            if occupant is None:
                # Halo cible valide (pulsant)
                if n in targets:
                    pulse = 0.5 + 0.5*math.sin(self.time_elapsed * 7)
                    r_halo = NODE_RADIUS + 6 + pulse * 5
                    arcade.draw_circle_filled(x, y, r_halo, (*COLOR_NODE_VALID, 55))
                    arcade.draw_circle_outline(x, y, r_halo, COLOR_NODE_VALID, 3)
                elif n == self.hovered_node:
                    arcade.draw_circle_filled(x, y, HOVER_RADIUS, (*COLOR_NODE_HOVER, 70))

                arcade.draw_circle_filled(x, y, NODE_RADIUS * 0.55, COLOR_LINE_SHADOW)
                arcade.draw_circle_filled(x, y, NODE_RADIUS * 0.40, COLOR_NODE_IDLE)
            else:
                is_selected = (n == self.selected_node)
                self.draw_piece(x, y, occupant, selected=is_selected, node_id=n)

    def draw_piece(self, x, y, player, selected=False, node_id=None, alpha_factor=1.0):
        colors = PLAYER_COLORS[player]

        # Animation de pose (rebond)
        bounce = 0.0
        if node_id and node_id in self.piece_bounce:
            dt = self.time_elapsed - self.piece_bounce[node_id]
            if dt < 0.35:
                bounce = math.sin(dt / 0.35 * math.pi) * 7

        radius = PIECE_RADIUS

        # Battement si sélectionné
        if selected:
            beat = 0.5 + 0.5*math.sin(self.time_elapsed * 6)
            pulse_r = radius + 10 + beat * 6
            arcade.draw_circle_filled(x, y, pulse_r, (255, 230, 150, int(70 * alpha_factor)))
            arcade.draw_circle_outline(x, y, pulse_r - 4, (255, 220, 120), 3)

        cy = y + bounce

        # Ombre portée
        arcade.draw_circle_filled(x+5, cy-8, radius*0.95, (0, 0, 0, int(90*alpha_factor)))
        
        # Dessiner la forme selon le skin
        self.draw_piece_shape(x, cy, radius, player, colors, alpha_factor)

    # ------------------- pion en vol ------------------------------------
    def draw_fly_piece(self):
        if self.fly_anim is None:
            return
        fx, fy = self.fly_anim.current_pos
        player  = self.fly_anim.player

        # Ombre au sol (s'estompe en hauteur)
        if self.flying_to:
            dx, dy = self.node_screen_pos[self.flying_to]
            # Ombre au sol qui glisse vers la destination
            p = self.fly_anim.progress
            sx = self.fly_anim.src[0] + (dx - self.fly_anim.src[0]) * p
            sy = self.fly_anim.src[1] + (dy - self.fly_anim.src[1]) * p
            shadow_a = self.fly_anim.shadow_alpha
            scale    = 0.6 + 0.4*(1 - math.sin(p * math.pi))
            arcade.draw_ellipse_filled(sx+3, sy-6, PIECE_RADIUS*scale*2, PIECE_RADIUS*scale, (0,0,0, shadow_a))

        # Pion en vol (sans node_id pour éviter le rebond, alpha=1)
        self.draw_piece(fx, fy, player, selected=False, node_id=None)

    # ------------------- HUD --------------------------------------------
    def draw_hud(self):
        w = self.window.width
        h = self.window.height

        # Bandeau titre
        arcade.draw_lrbt_rectangle_filled(0, w, h-64, h, (12, 14, 22, 230))
        arcade.draw_text("FANORONTELO TELO", 24, h-46, (240,220,170), 24, bold=True)

        # Message courant
        if self.winner:
            color = (255, 215, 110)
        else:
            color = PLAYER_COLORS[self.current_player]["light"]
        arcade.draw_text(self.message, 24, h-90, color, 16)

        # Raccourcis clavier (sans le undo car maintenant en bouton)
        arcade.draw_text("M : Menu skin", w-24, h-46, (170,170,185), 13, anchor_x="right")

        # Indicateur de pions ayant déjà bougé
        if not self.winner:
            for p, col_key, bx in ((1, "base", 24), (2, "base", w//2)):
                moved  = len(self.moved_once[p])
                total  = 3
                pname  = PLAYER_COLORS[p]["name"]
                color  = PLAYER_COLORS[p][col_key]
                

        # Pastille joueur courant
        if not self.winner:
            self.draw_piece(w-60, h-32, self.current_player, node_id=None)

        # Bandeau bas
        arcade.draw_lrbt_rectangle_filled(0, w, 0, 40, (12,14,22,230))
        arcade.draw_text(
            "Clic : sélectionner / déplacer   |   R : recommencer   |   Échap : quitter",
            24, 12, (170,170,185), 13
        )

        # Règle-rappel (bas droite)
        arcade.draw_text(
            "Règle : aligner 3 pions, chacun ayant bougé au moins une fois",
            w - 24, 12, (130, 130, 150), 11, anchor_x="right"
        )

        # Skin actuel
        arcade.draw_text(
            f"Skin: {self.current_skin.value} | Palette: {self.current_palette}",
            w//2, 12, (170,170,185), 13, anchor_x="center"
        )

        # Écran de victoire
        if self.winner:
            bw, bh = 360, 120
            bx, by = w/2 - bw/2, h/2 - bh/2 - 30
            arcade.draw_lrbt_rectangle_filled(bx, bx+bw, by, by+bh, (20, 22, 36, 240))
            arcade.draw_lrbt_rectangle_outline(bx, bx+bw, by, by+bh, (255,215,110), 3)
            arcade.draw_text(
                self.message, w/2, by+bh-28,
                (255, 215, 110), 22, anchor_x="center", bold=True
            )
            arcade.draw_text(
                "Appuyez sur R pour rejouer", w/2, by+28,
                (220, 200, 150), 15, anchor_x="center"
            )

    # ------------------- MENU DE SKIN ------------------------------------
    def draw_menu(self):
        w = self.window.width
        h = self.window.height
        
        # Fond semi-transparent
        arcade.draw_lrbt_rectangle_filled(0, w, 0, h, (0, 0, 0, 180))
        
        # Fenêtre du menu
        menu_w, menu_h = 440, 500
        menu_x = w//2 - menu_w//2
        menu_y = h//2 - menu_h//2
        
        arcade.draw_lrbt_rectangle_filled(menu_x, menu_x+menu_w, menu_y, menu_y+menu_h, (30, 35, 50, 240))
        arcade.draw_lrbt_rectangle_outline(menu_x, menu_x+menu_w, menu_y, menu_y+menu_h, (240, 220, 170), 3)
        
        # Titre
        arcade.draw_text("CHOIX DU SKIN", w//2, menu_y+menu_h-30, (240, 220, 170), 22, anchor_x="center", bold=True)
        
        # Séparateur
        arcade.draw_line(menu_x+20, menu_y+menu_h-45, menu_x+menu_w-20, menu_y+menu_h-45, (100, 100, 120), 2)
        
        # Bouton fermeture
        close_x = menu_x + menu_w - 30
        close_y = menu_y + menu_h - 30
        arcade.draw_text("✕", close_x, close_y-8, (255, 100, 100), 24, anchor_x="center")
        arcade.draw_rectangle_outline(close_x, close_y, 30, 30, (100, 100, 120), 2)
        
        # Liste des skins
        y = menu_y + menu_h - 70
        for skin in PieceSkin:
            is_selected = (skin == self.current_skin)
            color = (240, 220, 170) if is_selected else (170, 170, 185)
            rect_color = (60, 65, 80, 200) if is_selected else (40, 45, 60, 150)
            
            arcade.draw_lrbt_rectangle_filled(menu_x+20, menu_x+menu_w-20, y-16, y+16, rect_color)
            if is_selected:
                arcade.draw_rectangle_outline(menu_x+menu_w//2, y, menu_w-40, 32, (240, 220, 170), 2)
            
            # Aperçu du pion
            preview_x = menu_x + 50
            preview_y = y
            radius = 14
            
            # Simuler les couleurs du joueur 1 pour l'aperçu
            temp_colors = PLAYER_COLORS[1]
            
            # Sauvegarder le skin actuel
            old_skin = self.current_skin
            self.current_skin = skin
            # Dessiner un petit aperçu
            self.draw_piece_shape(preview_x, preview_y, radius, 1, temp_colors, 1.0)
            self.current_skin = old_skin
            
            arcade.draw_text(skin.value, menu_x + 80, y-6, color, 16)
            
            # Indicateur sélectionné
            if is_selected:
                arcade.draw_text("✓", menu_x + menu_w - 40, y-6, (100, 255, 100), 18)
            
            y -= 45
        
        # Section palettes
        arcade.draw_text("PALETTES DE COULEURS", w//2, y-5, (200, 190, 170), 16, anchor_x="center")
        y -= 30
        
        for i, palette_name in enumerate(COLOR_PALETTES.keys()):
            is_selected = (palette_name == self.current_palette)
            color = (240, 220, 170) if is_selected else (170, 170, 185)
            rect_color = (60, 65, 80, 200) if is_selected else (40, 45, 60, 150)
            
            arcade.draw_lrbt_rectangle_filled(menu_x+20, menu_x+menu_w-20, y-14, y+14, rect_color)
            if is_selected:
                arcade.draw_rectangle_outline(menu_x+menu_w//2, y, menu_w-40, 28, (240, 220, 170), 2)
            
            # Aperçu des couleurs
            c1 = COLOR_PALETTES[palette_name][1]["base"]
            c2 = COLOR_PALETTES[palette_name][2]["base"]
            arcade.draw_circle_filled(menu_x + 40, y, 8, c1)
            arcade.draw_circle_filled(menu_x + 60, y, 8, c2)
            
            arcade.draw_text(palette_name, menu_x + 80, y-5, color, 14)
            
            if is_selected:
                arcade.draw_text("✓", menu_x + menu_w - 40, y-5, (100, 255, 100), 16)
            
            y -= 35
        
        # Instructions
        arcade.draw_text(
            "Cliquez sur un skin ou une palette pour le sélectionner",
            w//2, menu_y+20, (130, 130, 150), 13, anchor_x="center"
        )


# ----------------------------------------------------------------------
# POINT D'ENTRÉE
# ----------------------------------------------------------------------

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=True)
    view   = FanoronteloView()
    window.show_view(view)
    arcade.run()


if __name__ == "__main__":
    main()






"""
import arcade
import math
import time



SCREEN_WIDTH  = 1000
SCREEN_HEIGHT = 760
SCREEN_TITLE  = "Fanorontelo Telo"

COLOR_BG_TOP        = (20,  24,  38)
COLOR_BG_BOTTOM     = (10,  12,  20)
COLOR_BOARD_TOP     = (92,  64,  38)
COLOR_BOARD_SIDE    = (52,  36,  22)
COLOR_BOARD_EDGE    = (140, 102, 58)
COLOR_LINE          = (224, 196, 140)
COLOR_LINE_SHADOW   = (40,  28,  16)
COLOR_NODE_IDLE     = (224, 196, 140)
COLOR_NODE_HOVER    = (255, 224, 130)
COLOR_NODE_VALID    = (110, 220, 150)

PLAYER_COLORS = {
    1: {"base": (224,  86,  86), "light": (255, 150, 130), "dark": (120, 30,  30),  "name": "Rouge"},
    2: {"base": ( 70, 150, 235), "light": (150, 210, 255), "dark": ( 20, 60, 120),  "name": "Bleu"},
}

PIECE_RADIUS = 28
NODE_RADIUS  = 16
HOVER_RADIUS = 24

# Durée de l'animation de vol (secondes)
FLY_DURATION = 0.38
# Hauteur max du vol (pixels)
FLY_HEIGHT   = 90

# ----------------------------------------------------------------------
# GÉOMÉTRIE DU PLATEAU
# ----------------------------------------------------------------------

NODE_IDS = ["NO", "N", "NE", "O", "C", "E", "SO", "S", "SE"]

RAW_POSITIONS = {
    "NO": (-1.0,  1.0), "N":  ( 0.0,  1.0), "NE": ( 1.0,  1.0),
    "O":  (-1.0,  0.0), "C":  ( 0.0,  0.0), "E":  ( 1.0,  0.0),
    "SO": (-1.0, -1.0), "S":  ( 0.0, -1.0), "SE": ( 1.0, -1.0),
}

EDGES = [
    ("NO","N"),  ("N","NE"),
    ("SO","S"),  ("S","SE"),
    ("NO","O"),  ("O","SO"),
    ("NE","E"),  ("E","SE"),
    ("N","C"),   ("C","S"),
    ("O","C"),   ("C","E"),
    ("NO","C"),  ("C","SE"),
    ("NE","C"),  ("C","SO"),
]

WINNING_LINES = [
    ("NO","N","NE"),
    ("SO","S","SE"),
    ("NO","O","SO"),
    ("NE","E","SE"),
    ("N","C","S"),
    ("O","C","E"),
    ("NO","C","SE"),
    ("NE","C","SO"),
]

ADJACENCY = {n: set() for n in NODE_IDS}
for _a, _b in EDGES:
    ADJACENCY[_a].add(_b)
    ADJACENCY[_b].add(_a)

# Placement initial :  Joueur 1 (Rouge) en haut, Joueur 2 (Bleu) en bas
INITIAL_PLACEMENT = {
    "NO": 1, "N": 1, "NE": 1,
    "O":  None, "C": None, "E": None,
    "SO": 2, "S": 2, "SE": 2,
}


def project(pos, cx, cy, scale, tilt=0.62):
    x, y = pos
    return cx + x * scale, cy + y * scale * tilt


# ----------------------------------------------------------------------
# ANIMATION DE VOL
# ----------------------------------------------------------------------

class FlyAnimation:

    def __init__(self, src_pos, dst_pos, player, duration=FLY_DURATION):
        self.src  = src_pos
        self.dst  = dst_pos
        self.player = player
        self.dur  = duration
        self.t    = 0.0       # temps écoulé
        self.done = False

    def update(self, dt):
        self.t = min(self.t + dt, self.dur)
        if self.t >= self.dur:
            self.done = True

    @property
    def progress(self):
       
        p = self.t / self.dur
        return p * p * (3 - 2 * p)   # smoothstep

    @property
    def current_pos(self):
        p   = self.progress
        x   = self.src[0] + (self.dst[0] - self.src[0]) * p
        y   = self.src[1] + (self.dst[1] - self.src[1]) * p
        arc = math.sin(p * math.pi) * FLY_HEIGHT   # arc parabolique
        return x, y + arc

    @property
    def shadow_alpha(self):
        # l'ombre s'estompe au milieu du vol
        p = self.progress
        return int(90 * (1 - math.sin(p * math.pi) * 0.7))


# ----------------------------------------------------------------------
# VUE PRINCIPALE
# ----------------------------------------------------------------------

class FanoronteloView(arcade.View):
    def __init__(self):
        super().__init__()
        self.board_cx = SCREEN_WIDTH  / 2
        self.board_cy = SCREEN_HEIGHT / 2 + 10
        self.scale    = 230

        self.node_screen_pos = {}
        self.update_node_positions()

        # Animation de vol courante (None si aucune)
        self.fly_anim: FlyAnimation | None = None
        # Noeud source du vol (caché pendant l'animation)
        self.flying_from: str | None = None
        # Noeud destination (destiné à recevoir le pion après le vol)
        self.flying_to:   str | None = None

        self.time_elapsed = 0.0
        self.piece_bounce: dict[str, float] = {}

        self.reset_game()

    # ------------------------------------------------------------------
    def update_node_positions(self):
        self.node_screen_pos = {
            n: project(RAW_POSITIONS[n], self.board_cx, self.board_cy, self.scale)
            for n in NODE_IDS
        }

    def on_show_view(self):
        arcade.set_background_color((15, 17, 26))

    # ------------------------------------------------------------------
    def reset_game(self):
        self.board           = dict(INITIAL_PLACEMENT)   # placement initial
        self.current_player  = 1
        self.phase           = "movement"               # on démarre directement en mouvement
        self.selected_node   = None
        self.hovered_node    = None
        self.winner          = None
        self.winning_line    = None
        self.piece_bounce    = {}
        self.fly_anim        = None
        self.flying_from     = None
        self.flying_to       = None
        # Ensemble de nœuds ayant été déplacés au moins une fois par chaque joueur
        self.moved_once: dict[int, set] = {1: set(), 2: set()}
        self.message = f"Déplacez un pion — Joueur {PLAYER_COLORS[1]['name']}"

    # ------------------------------------------------------------------
    # LOGIQUE
    # ------------------------------------------------------------------
    def check_winner(self, player):
       
        # Vérifier que tous les pions du joueur ont bougé
        player_nodes = [n for n in NODE_IDS if self.board[n] == player]
        if not all(n in self.moved_once[player] for n in player_nodes):
            return None
        for line in WINNING_LINES:
            if all(self.board[n] == player for n in line):
                return line
        return None

    def node_at_pixel(self, x, y):
        best, best_d = None, 1e9
        for n, (nx, ny) in self.node_screen_pos.items():
            d = math.hypot(x - nx, y - ny)
            if d < best_d:
                best_d, best = d, n
        if best_d <= max(PIECE_RADIUS, NODE_RADIUS) + 12:
            return best
        return None

    def valid_targets(self, node):
       
        if node is None:
            return set()
        return {n for n in ADJACENCY[node] if self.board[n] is None}

    def try_select_or_move(self, node):
        
        if self.fly_anim is not None:
            return   # on ne clique pas pendant un vol

        if self.selected_node is None:
            if self.board[node] == self.current_player:
                self.selected_node = node
            return

        # Clic sur le même pion → désélection
        if node == self.selected_node:
            self.selected_node = None
            return

        # Clic sur un autre pion du même joueur → changer la sélection
        if self.board[node] == self.current_player:
            self.selected_node = node
            return

        # Clic sur une cible valide → lancer le vol
        if self.board[node] is None and node in ADJACENCY[self.selected_node]:
            self._start_fly(self.selected_node, node)

    def _start_fly(self, src, dst):
        src_pos = self.node_screen_pos[src]
        dst_pos = self.node_screen_pos[dst]
        self.fly_anim    = FlyAnimation(src_pos, dst_pos, self.current_player)
        self.flying_from = src
        self.flying_to   = dst
        self.selected_node = None

    def _finish_fly(self):
       
        src, dst = self.flying_from, self.flying_to
        player = self.board[src]

        self.board[src]  = None
        self.board[dst]  = player
        self.piece_bounce[dst] = self.time_elapsed
        self.moved_once[player].add(dst)

        self.fly_anim    = None
        self.flying_from = None
        self.flying_to   = None

        win_line = self.check_winner(player)
        if win_line:
            self.winner      = player
            self.winning_line = win_line
            self.message = f"Joueur {PLAYER_COLORS[player]['name']} a gagné !"
            return

        self.switch_player()

    def switch_player(self):
        self.current_player = 2 if self.current_player == 1 else 1
        self.message = (
            f"Au tour de {PLAYER_COLORS[self.current_player]['name']} — "
            "Sélectionnez un pion"
        )

    # ------------------------------------------------------------------
    # ENTRÉES
    # ------------------------------------------------------------------
    def on_mouse_motion(self, x, y, dx, dy):
        if self.fly_anim is None:
            self.hovered_node = self.node_at_pixel(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.winner is not None or self.fly_anim is not None:
            return
        node = self.node_at_pixel(x, y)
        if node is None:
            return
        self.try_select_or_move(node)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            self.reset_game()
        elif key == arcade.key.ESCAPE:
            arcade.close_window()

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.board_cx = width  / 2
        self.board_cy = height / 2 + 10
        self.scale    = min(width, height) * 0.32
        self.update_node_positions()
        # Recalculer la position de départ du vol en cours si besoin
        if self.fly_anim and self.flying_from and self.flying_to:
            # Relancer l'animation depuis la position actuelle du pion volant
            prog = self.fly_anim.progress
            remaining = self.fly_anim.dur * (1 - prog)
            new_anim = FlyAnimation(
                self.node_screen_pos[self.flying_from],
                self.node_screen_pos[self.flying_to],
                self.fly_anim.player,
                duration=max(remaining, 0.05)
            )
            new_anim.t = 0.0
            self.fly_anim = new_anim

    # ------------------------------------------------------------------
    # MISE À JOUR
    # ------------------------------------------------------------------
    def on_update(self, delta_time):
        self.time_elapsed += delta_time
        if self.fly_anim is not None:
            self.fly_anim.update(delta_time)
            if self.fly_anim.done:
                self._finish_fly()

    # ------------------------------------------------------------------
    # RENDU
    # ------------------------------------------------------------------
    def on_draw(self):
        self.clear()
        self.draw_background()
        self.draw_board_3d()
        self.draw_lines()
        self.draw_nodes_and_pieces()
        self.draw_fly_piece()
        self.draw_hud()

    # ------------------- fond dégradé -----------------------------------
    def draw_background(self):
        steps = 40
        h = self.window.height
        for i in range(steps):
            t = i / steps
            color = tuple(
                int(COLOR_BG_BOTTOM[c] + (COLOR_BG_TOP[c] - COLOR_BG_BOTTOM[c]) * t)
                for c in range(3)
            )
            arcade.draw_lrbt_rectangle_filled(
                0, self.window.width,
                h * t, h * (t + 1/steps),
                color
            )

    # ------------------- plateau pseudo-3D ------------------------------
    def draw_board_3d(self):
        pts   = [self.node_screen_pos[n] for n in ("NO","NE","SE","SO")]
        depth = 26

        side_pts = [(x, y - depth) for x, y in pts]
        n = len(pts)
        for i in range(n):
            p1, p2 = pts[i], pts[(i+1)%n]
            s1, s2 = side_pts[i], side_pts[(i+1)%n]
            arcade.draw_polygon_filled([p1, p2, s2, s1], COLOR_BOARD_SIDE)

        shadow_pts = [(x+14, y-depth-18) for x, y in pts]
        arcade.draw_polygon_filled(shadow_pts, (0, 0, 0, 110))

        margin_pts = self._expand(pts, 1.28)
        arcade.draw_polygon_filled(margin_pts, COLOR_BOARD_TOP)
        arcade.draw_polygon_outline(margin_pts, COLOR_BOARD_EDGE, 4)

        inner_pts = self._expand(pts, 1.12)
        arcade.draw_polygon_outline(inner_pts, COLOR_BOARD_EDGE, 2)

    @staticmethod
    def _expand(pts, factor):
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        return [(cx + (x-cx)*factor, cy + (y-cy)*factor) for x, y in pts]

    # ------------------- lignes ------------------------------------------
    def draw_lines(self):
        for a, b in EDGES:
            p1, p2 = self.node_screen_pos[a], self.node_screen_pos[b]
            arcade.draw_line(p1[0]+2, p1[1]-3, p2[0]+2, p2[1]-3, COLOR_LINE_SHADOW, 5)
            arcade.draw_line(p1[0], p1[1], p2[0], p2[1], COLOR_LINE, 3)

        if self.winning_line:
            pts   = [self.node_screen_pos[n] for n in self.winning_line]
            pulse = 0.5 + 0.5*math.sin(self.time_elapsed * 4)
            glow  = (255, int(210+30*pulse), 90)
            for i in range(len(pts)-1):
                arcade.draw_line(*pts[i], *pts[i+1], glow, 8)

    # ------------------- noeuds + pions ---------------------------------
    def draw_nodes_and_pieces(self):
        targets = self.valid_targets(self.selected_node)

        for n in NODE_IDS:
            # Masquer la source du vol (le pion est en train de voler)
            if n == self.flying_from:
                continue

            x, y     = self.node_screen_pos[n]
            occupant = self.board[n]

            if occupant is None:
                # Halo cible valide (pulsant)
                if n in targets:
                    pulse = 0.5 + 0.5*math.sin(self.time_elapsed * 7)
                    r_halo = NODE_RADIUS + 6 + pulse * 5
                    arcade.draw_circle_filled(x, y, r_halo, (*COLOR_NODE_VALID, 55))
                    arcade.draw_circle_outline(x, y, r_halo, COLOR_NODE_VALID, 3)
                elif n == self.hovered_node:
                    arcade.draw_circle_filled(x, y, HOVER_RADIUS, (*COLOR_NODE_HOVER, 70))

                arcade.draw_circle_filled(x, y, NODE_RADIUS * 0.55, COLOR_LINE_SHADOW)
                arcade.draw_circle_filled(x, y, NODE_RADIUS * 0.40, COLOR_NODE_IDLE)
            else:
                is_selected = (n == self.selected_node)
                self.draw_piece(x, y, occupant, selected=is_selected, node_id=n)

    def draw_piece(self, x, y, player, selected=False, node_id=None, alpha_factor=1.0):
        colors = PLAYER_COLORS[player]

        # Animation de pose (rebond)
        bounce = 0.0
        if node_id and node_id in self.piece_bounce:
            dt = self.time_elapsed - self.piece_bounce[node_id]
            if dt < 0.35:
                bounce = math.sin(dt / 0.35 * math.pi) * 7

        radius = PIECE_RADIUS

        # Battement si sélectionné
        if selected:
            beat = 0.5 + 0.5*math.sin(self.time_elapsed * 6)
            pulse_r = radius + 10 + beat * 6
            arcade.draw_circle_filled(x, y, pulse_r, (255, 230, 150, int(70 * alpha_factor)))
            arcade.draw_circle_outline(x, y, pulse_r - 4, (255, 220, 120), 3)

        cy = y + bounce

        # Ombre portée
        arcade.draw_circle_filled(x+5, cy-8, radius*0.95, (0, 0, 0, int(90*alpha_factor)))
        # Corps sombre (bord)
        arcade.draw_circle_filled(x, cy, radius, (*colors["dark"], int(255*alpha_factor)))
        # Corps principal
        arcade.draw_circle_filled(x, cy+2, radius*0.92, (*colors["base"], int(255*alpha_factor)))
        # Reflet diffus
        arcade.draw_circle_filled(
            x - radius*0.32, cy + radius*0.38, radius*0.42,
            (*colors["light"], int(180*alpha_factor))
        )
        # Point spéculaire
        arcade.draw_circle_filled(
            x - radius*0.45, cy + radius*0.50, radius*0.14,
            (255, 255, 255, int(200*alpha_factor))
        )
        # Contour
        arcade.draw_circle_outline(x, cy+2, radius*0.92, (*colors["dark"], int(200*alpha_factor)), 2)

    # ------------------- pion en vol ------------------------------------
    def draw_fly_piece(self):
        if self.fly_anim is None:
            return
        fx, fy = self.fly_anim.current_pos
        player  = self.fly_anim.player

        # Ombre au sol (s'estompe en hauteur)
        if self.flying_to:
            dx, dy = self.node_screen_pos[self.flying_to]
            # Ombre au sol qui glisse vers la destination
            p = self.fly_anim.progress
            sx = self.fly_anim.src[0] + (dx - self.fly_anim.src[0]) * p
            sy = self.fly_anim.src[1] + (dy - self.fly_anim.src[1]) * p
            shadow_a = self.fly_anim.shadow_alpha
            scale    = 0.6 + 0.4*(1 - math.sin(p * math.pi))
            arcade.draw_ellipse_filled(sx+3, sy-6, PIECE_RADIUS*scale*2, PIECE_RADIUS*scale, (0,0,0, shadow_a))

        # Pion en vol (sans node_id pour éviter le rebond, alpha=1)
        self.draw_piece(fx, fy, player, selected=False, node_id=None)

    # ------------------- HUD --------------------------------------------
    def draw_hud(self):
        w = self.window.width
        h = self.window.height

        # Bandeau titre
        arcade.draw_lrbt_rectangle_filled(0, w, h-64, h, (12, 14, 22, 230))
        arcade.draw_text("FANORONTELO TELO", 24, h-46, (240,220,170), 24, bold=True)

        # Message courant
        if self.winner:
            color = (255, 215, 110)
        else:
            color = PLAYER_COLORS[self.current_player]["light"]
        arcade.draw_text(self.message, 24, h-90, color, 16)

        # Indicateur de pions ayant déjà bougé
        if not self.winner:
            for p, col_key, bx in ((1, "base", 24), (2, "base", w//2)):
                moved  = len(self.moved_once[p])
                pname  = PLAYER_COLORS[p]["name"]
                

        # Pastille joueur courant
        if not self.winner:
            self.draw_piece(w-60, h-32, self.current_player, node_id=None)

        # Bandeau bas
        arcade.draw_lrbt_rectangle_filled(0, w, 0, 40, (12,14,22,230))
        arcade.draw_text(
            "Clic : sélectionner / déplacer   |   R : recommencer   |   Échap : quitter",
            24, 12, (170,170,185), 13
        )

        # Règle-rappel (bas droite)
        arcade.draw_text(
            "Règle : aligner 3 pions, chacun ayant bougé au moins une fois",
            w - 24, 12, (130, 130, 150), 11, anchor_x="right"
        )

        # Écran de victoire
        if self.winner:
            bw, bh = 360, 120
            bx, by = w/2 - bw/2, h/2 - bh/2 - 30
            arcade.draw_lrbt_rectangle_filled(bx, bx+bw, by, by+bh, (20, 22, 36, 240))
            arcade.draw_lrbt_rectangle_outline(bx, bx+bw, by, by+bh, (255,215,110), 3)
            arcade.draw_text(
                self.message, w/2, by+bh-28,
                (255, 215, 110), 22, anchor_x="center", bold=True
            )
            arcade.draw_text(
                "Appuyez sur R pour rejouer", w/2, by+28,
                (220, 200, 150), 15, anchor_x="center"
            )


# ----------------------------------------------------------------------
# POINT D'ENTRÉE
# ----------------------------------------------------------------------

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=True)
    view   = FanoronteloView()
    window.show_view(view)
    arcade.run()


if __name__ == "__main__":
    main()
"""