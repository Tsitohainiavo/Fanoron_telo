"""
Fanoron-telo (Bitboard + Skins & Palette + Démo IA vs IA + Undo/Redo + Perf)
================================================================================
Jeu de stratégie malgache avec moteur bitboard, IA (facile/moyen/difficile),
skins de pions, palettes de couleurs, annulation/rétablissement de coup,
mode démonstration automatique (IA contre IA) et mesure du temps de l'IA.
"""

import arcade
import math
import time
from enum import Enum
import alphabeta
import moteur_ia

# ----------------------------------------------------------------------
# CONFIGURATION GÉNÉRALE
# ----------------------------------------------------------------------

SCREEN_WIDTH  = 1000
SCREEN_HEIGHT = 760
SCREEN_TITLE  = "Fanoron-telo"

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

FLY_DURATION = 0.38
FLY_HEIGHT   = 90

# ----------------------------------------------------------------------
# GÉOMÉTRIE ET CONSTANTES BITBOARD
# ----------------------------------------------------------------------

NODE_IDS = ["NO", "N", "NE", "O", "C", "E", "SO", "S", "SE"]
NODE_TO_BIT = {name: idx for idx, name in enumerate(NODE_IDS)}

RAW_POSITIONS = {
    "NO": (-1.0,  1.0), "N":  ( 0.0,  1.0), "NE": ( 1.0,  1.0),
    "O":  (-1.0,  0.0), "C":  ( 0.0,  0.0), "E":  ( 1.0,  0.0),
    "SO": (-1.0, -1.0), "S":  ( 0.0, -1.0), "SE": ( 1.0, -1.0),
}

EDGES = [
    ("NO","N"),  ("N","NE"), ("SO","S"),  ("S","SE"),
    ("NO","O"),  ("O","SO"), ("NE","E"),  ("E","SE"),
    ("N","C"),   ("C","S"),  ("O","C"),   ("C","E"),
    ("NO","C"),  ("C","SE"), ("NE","C"),  ("C","SO"),
]

WINNING_LINES = [
    ("NO","N","NE"), ("SO","S","SE"), ("NO","O","SO"), ("NE","E","SE"),
    ("N","C","S"),  ("O","C","E"),  ("NO","C","SE"), ("NE","C","SO"),
]

ADJACENCY_MASKS = {i: 0 for i in range(9)}
for _a, _b in EDGES:
    bit_a = NODE_TO_BIT[_a]
    bit_b = NODE_TO_BIT[_b]
    ADJACENCY_MASKS[bit_a] |= (1 << bit_b)
    ADJACENCY_MASKS[bit_b] |= (1 << bit_a)

WINNING_MASKS = []
for line in WINNING_LINES:
    mask = 0
    for node in line:
        mask |= (1 << NODE_TO_BIT[node])
    WINNING_MASKS.append(mask)

INITIAL_P1_BITBOARD = 7       # NO, N, NE
INITIAL_P2_BITBOARD = 448     # SO, S, SE

def project(pos, cx, cy, scale, tilt=0.62):
    x, y = pos
    return cx + x * scale, cy + y * scale * tilt


# ----------------------------------------------------------------------
# MOTEUR DE JEU LOGIQUE
# ----------------------------------------------------------------------

class FanoronteloEngine:
    def __init__(self):
        self.reset()

    def reset(self):
        self.bitboard_p1 = INITIAL_P1_BITBOARD
        self.bitboard_p2 = INITIAL_P2_BITBOARD
        self.tour = 1
        self.moved_once_p1 = 0
        self.moved_once_p2 = 0

    def get_occupied(self):
        return self.bitboard_p1 | self.bitboard_p2

    def get_occupant(self, bit_idx):
        if (self.bitboard_p1 & (1 << bit_idx)) != 0:
            return 1
        if (self.bitboard_p2 & (1 << bit_idx)) != 0:
            return 2
        return None

    def verifier_alignement_et_mouvement(self, bb_joueur, moved_joueur):
        if (bb_joueur & moved_joueur) != bb_joueur:
            return False
        for masque in WINNING_MASKS:
            if (bb_joueur & masque) == masque:
                return True
        return False

    def valider_et_deplacer(self, bit_src, bit_dst):
        mask_src = 1 << bit_src
        mask_dst = 1 << bit_dst
        occupied = self.get_occupied()

        bb_actuel = self.bitboard_p1 if self.tour == 1 else self.bitboard_p2
        if (bb_actuel & mask_src) == 0:
            return False
        if (occupied & mask_dst) != 0:
            return False
        if (ADJACENCY_MASKS[bit_src] & mask_dst) == 0:
            return False

        if self.tour == 1:
            self.bitboard_p1 &= ~mask_src
            self.bitboard_p1 |= mask_dst
            self.moved_once_p1 |= mask_dst
        else:
            self.bitboard_p2 &= ~mask_src
            self.bitboard_p2 |= mask_dst
            self.moved_once_p2 |= mask_dst
        return True

    def copier(self):
        copie = FanoronteloEngine()
        copie.bitboard_p1 = self.bitboard_p1
        copie.bitboard_p2 = self.bitboard_p2
        copie.tour = self.tour
        copie.moved_once_p1 = self.moved_once_p1
        copie.moved_once_p2 = self.moved_once_p2
        return copie

    def get_successeurs(self):
        """Génère la liste des états successeurs légaux (utilisé par l'IA)."""
        successeurs = []
        occupied = self.get_occupied()
        bb_actuel = self.bitboard_p1 if self.tour == 1 else self.bitboard_p2

        for src in range(9):
            if (bb_actuel & (1 << src)) != 0:
                destinations_possibles = ADJACENCY_MASKS[src] & ~occupied
                for dst in range(9):
                    if (destinations_possibles & (1 << dst)) != 0:
                        enfant = self.copier()
                        enfant.valider_et_deplacer(src, dst)
                        enfant.tour = 2 if enfant.tour == 1 else 1
                        successeurs.append(enfant)
        return successeurs


class FlyAnimation:
    def __init__(self, src_pos, dst_pos, player, duration=FLY_DURATION):
        self.src  = src_pos
        self.dst  = dst_pos
        self.player = player
        self.dur  = duration
        self.t    = 0.0
        self.done = False

    def update(self, dt):
        self.t = min(self.t + dt, self.dur)
        if self.t >= self.dur:
            self.done = True

    @property
    def progress(self):
        p = self.t / self.dur
        return p * p * (3 - 2 * p)

    @property
    def current_pos(self):
        p   = self.progress
        x   = self.src[0] + (self.dst[0] - self.src[0]) * p
        y   = self.src[1] + (self.dst[1] - self.src[1]) * p
        arc = math.sin(p * math.pi) * FLY_HEIGHT
        return x, y + arc

    @property
    def shadow_alpha(self):
        p = self.progress
        return int(90 * (1 - math.sin(p * math.pi) * 0.7))


# ----------------------------------------------------------------------
# BOUTONS DE L'INTERFACE (Undo, Redo, Menu)
# ----------------------------------------------------------------------

class UndoButton:
    def __init__(self, x, y, size=40):
        self.x = x
        self.y = y
        self.size = size
        self.hovered = False
        self.clicked = False

    def draw(self, enabled=True):
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

        arcade.draw_circle_filled(self.x, self.y, self.size//2, bg_color)
        arcade.draw_circle_outline(self.x, self.y, self.size//2, border_color, 2)

        arcade.draw_text("⤺", self.x, self.y - 4, icon_color, 18, anchor_x="center", anchor_y="center")
        arcade.draw_text("UNDO", self.x, self.y - self.size//2 - 12, icon_color, 10, anchor_x="center", bold=True)

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


class RedoButton:
    def __init__(self, x, y, size=40):
        self.x = x
        self.y = y
        self.size = size
        self.hovered = False
        self.clicked = False

    def draw(self, enabled=True):
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

        arcade.draw_circle_filled(self.x, self.y, self.size//2, bg_color)
        arcade.draw_circle_outline(self.x, self.y, self.size//2, border_color, 2)

        arcade.draw_text("⤻", self.x, self.y - 4, icon_color, 18, anchor_x="center", anchor_y="center")
        arcade.draw_text("REDO", self.x, self.y - self.size//2 - 12, icon_color, 10, anchor_x="center", bold=True)

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


class MenuButton:
    """Bouton 'MENU' pour retourner à l'accueil."""
    def __init__(self, x, y, size=40):
        self.x = x
        self.y = y
        self.size = size
        self.hovered = False
        self.clicked = False

    def draw(self, enabled=True):
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

        arcade.draw_circle_filled(self.x, self.y, self.size//2, bg_color)
        arcade.draw_circle_outline(self.x, self.y, self.size//2, border_color, 2)

        arcade.draw_text("⌂", self.x, self.y - 4, icon_color, 20, anchor_x="center", anchor_y="center")
        arcade.draw_text("MENU", self.x, self.y - self.size//2 - 12, icon_color, 10, anchor_x="center", bold=True)

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


class SkinMenuButton:
    """Bouton 'SKIN' pour ouvrir le menu de personnalisation (ancien MenuButton renommé)."""
    def __init__(self, x, y, width=80, height=36):
        self.x = x
        self.y = y
        self.w = width
        self.h = height
        self.hovered = False
        self.clicked = False

    def _hit(self, x, y):
        return (abs(x - self.x) <= self.w // 2 and abs(y - self.y) <= self.h // 2)

    def draw(self, active=False):
        if active:
            bg, fg, border = (240, 210, 90, 230), (30, 30, 30), (255, 230, 120)
        elif self.clicked:
            bg, fg, border = (90, 110, 160, 230), (240, 240, 255), (160, 180, 220)
        elif self.hovered:
            bg, fg, border = (70, 90, 140, 220), (230, 235, 255), (150, 170, 210)
        else:
            bg, fg, border = (45, 52, 78, 210), (190, 200, 230), (80, 90, 130)

        left, right = self.x - self.w // 2, self.x + self.w // 2
        bottom, top = self.y - self.h // 2, self.y + self.h // 2

        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, bg)
        arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, border, 2)

        arcade.draw_circle_filled(self.x - 18, self.y + 2, 4, (224, 86,  86))
        arcade.draw_circle_filled(self.x - 8,  self.y + 2, 4, (218, 165, 32))
        arcade.draw_circle_filled(self.x + 2,  self.y + 2, 4, (70, 150, 235))

        arcade.draw_text("SKIN", self.x + 12, self.y, fg, 11, bold=True, anchor_x="center", anchor_y="center")

    def on_mouse_motion(self, x, y):
        self.hovered = self._hit(x, y)
        return self.hovered

    def on_mouse_press(self, x, y):
        if self._hit(x, y):
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

        self.game_mode = "HvH"          # "HvH", "HvIA", "demo"
        self.ai_difficulty = "facile"
        self.demo_mode = False          # True si on est en mode IA vs IA
        self.demo_difficulty = "facile"

        self.node_screen_pos = {}
        self.update_node_positions()

        self.fly_anim = None
        self.flying_from = None
        self.flying_to = None

        self.time_elapsed = 0.0
        self.piece_bounce = {}

        self.engine = FanoronteloEngine()
        self.selected_node = None
        self.hovered_node = None
        self.winner = None
        self.winning_line = None

        self.undo_stack = []
        self.redo_stack = []           # pour le rétablissement
        self.current_skin = PieceSkin.CIRCLE
        self.current_palette = "Classique"
        self.show_menu = False

        # Positions initiales (seront ajustées dans on_resize)
        self.undo_button = UndoButton(SCREEN_WIDTH - 70, SCREEN_HEIGHT - 150)
        self.redo_button = RedoButton(SCREEN_WIDTH - 70, SCREEN_HEIGHT - 210)
        self.menu_button = MenuButton(SCREEN_WIDTH - 70, SCREEN_HEIGHT - 270)   # retour accueil
        self.skin_button = SkinMenuButton(SCREEN_WIDTH - 70, SCREEN_HEIGHT - 330)  # SKIN

        # Performance de l'IA
        self.last_ia_time_ms = 0.0
        self.demo_next_move_time = 0.0  # pour ralentir la démo

        self.reset_game()

    def update_node_positions(self):
        self.node_screen_pos = {
            n: project(RAW_POSITIONS[n], self.board_cx, self.board_cy, self.scale)
            for n in NODE_IDS
        }

    def configure_game(self, mode, diff):
        self.game_mode = mode
        self.ai_difficulty = diff
        self.demo_mode = False
        self.reset_game()

    def configure_demo(self, difficulty="facile"):
        """Lance un affrontement IA vs IA (démo automatique)."""
        self.game_mode = "demo"
        self.demo_difficulty = difficulty
        self.demo_mode = True
        self.reset_game()
        self.message = f"Démo IA vs IA ({difficulty}) — Réflexion..."
        self.demo_next_move_time = time.time() + 0.5  # petit délai avant le premier coup

    def reset_game(self):
        self.engine.reset()
        self.selected_node = None
        self.hovered_node = None
        self.winner = None
        self.winning_line = None
        self.piece_bounce = {}
        self.fly_anim = None
        self.flying_from = None
        self.flying_to = None
        self.undo_stack.clear()
        self.redo_stack.clear()

        if self.game_mode == "demo":
            mode_str = f"Démo IA vs IA ({self.demo_difficulty})"
        elif self.game_mode == "HvIA":
            mode_str = f" vs IA ({self.ai_difficulty})"
        else:
            mode_str = " vs Humain"
        self.message = f"Déplacez un pion — Joueur {PLAYER_COLORS[1]['name']}{mode_str}"

    # ---------- Undo / Redo ----------
    def save_state(self):
        # En mode HvIA, on ne sauvegarde que lorsque c'est au tour du joueur humain (tour 1)
        # pour qu'un seul Undo annule le coup humain + la réponse IA.
        if self.game_mode == "HvIA" and self.engine.tour != 1:
            return
        if self.demo_mode:
            return
        self.undo_stack.append((self.engine.copier(), self.message))
        self.redo_stack.clear()   # tout nouveau mouvement vide la pile de redo
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack or self.fly_anim is not None:
            return
        # Sauvegarder l'état actuel dans la pile redo
        self.redo_stack.append((self.engine.copier(), self.message))
        engine_copy, msg = self.undo_stack.pop()
        self.engine = engine_copy
        self.selected_node = None
        self.winner = None
        self.winning_line = None
        self.piece_bounce = {}
        self.fly_anim = None
        self.flying_from = None
        self.flying_to = None
        self.message = f"↩ Annulation — {msg}"

    def redo(self):
        if not self.redo_stack or self.fly_anim is not None:
            return
        # Sauvegarder l'état actuel dans la pile undo
        self.undo_stack.append((self.engine.copier(), self.message))
        engine_copy, msg = self.redo_stack.pop()
        self.engine = engine_copy
        self.selected_node = None
        self.winner = None
        self.winning_line = None
        self.piece_bounce = {}
        self.fly_anim = None
        self.flying_from = None
        self.flying_to = None
        self.message = f"↪ Rétablissement — {msg}"

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
        bit_src = NODE_TO_BIT[node]
        occupied = self.engine.get_occupied()
        allowed_dest_mask = ADJACENCY_MASKS[bit_src] & ~occupied
        targets = set()
        for n in NODE_IDS:
            if (allowed_dest_mask & (1 << NODE_TO_BIT[n])) != 0:
                targets.add(n)
        return targets

    def try_select_or_move(self, node):
        if self.fly_anim is not None:
            return
        bit_idx = NODE_TO_BIT[node]
        occupant = self.engine.get_occupant(bit_idx)

        if self.selected_node is None:
            if occupant == self.engine.tour:
                self.selected_node = node
            return

        if node == self.selected_node:
            self.selected_node = None
            return

        if occupant == self.engine.tour:
            self.selected_node = node
            return

        if occupant is None:
            bit_src = NODE_TO_BIT[self.selected_node]
            if (ADJACENCY_MASKS[bit_src] & (1 << bit_idx)) != 0:
                self._start_fly(self.selected_node, node)

    def _start_fly(self, src, dst):
        self.save_state()
        src_pos = self.node_screen_pos[src]
        dst_pos = self.node_screen_pos[dst]
        self.fly_anim    = FlyAnimation(src_pos, dst_pos, self.engine.tour)
        self.flying_from = src
        self.flying_to   = dst
        self.selected_node = None

    def _finish_fly(self):
        src, dst = self.flying_from, self.flying_to
        bit_src, bit_dst = NODE_TO_BIT[src], NODE_TO_BIT[dst]
        player = self.engine.tour

        if self.engine.valider_et_deplacer(bit_src, bit_dst):
            self.piece_bounce[dst] = self.time_elapsed

        self.fly_anim    = None
        self.flying_from = None
        self.flying_to   = None

        bb_joueur = self.engine.bitboard_p1 if player == 1 else self.engine.bitboard_p2
        moved_joueur = self.engine.moved_once_p1 if player == 1 else self.engine.moved_once_p2

        if self.engine.verifier_alignement_et_mouvement(bb_joueur, moved_joueur):
            self.winner = player
            for line in WINNING_LINES:
                mask = 0
                for n in line:
                    mask |= (1 << NODE_TO_BIT[n])
                if (bb_joueur & mask) == mask:
                    self.winning_line = line
                    break
            self.message = f"🏆 Joueur {PLAYER_COLORS[player]['name']} a gagné !"
            return

        # Ralentir la démo après chaque coup
        if self.demo_mode:
            self.demo_next_move_time = time.time() + 3.0   # 3 secondes de pause

        self.switch_player()

    def switch_player(self):
        self.engine.tour = 2 if self.engine.tour == 1 else 1
        if self.winner:
            return

        # Mode Démo ou tour de l'IA en mode HvIA
        if self.demo_mode or (self.game_mode == "HvIA" and self.engine.tour == 2):
            self.message = f"L'IA ({self.demo_difficulty if self.demo_mode else self.ai_difficulty}) réfléchit..."
            src_idx, dst_idx = None, None

            t_start = time.perf_counter()

            if self.ai_difficulty in ["facile", "moyen"]:
                prochain_etat = moteur_ia.obtenir_coup_ia(self.engine, niveau=self.ai_difficulty)
                if prochain_etat:
                    if self.engine.tour == 2:
                        ancien_bb = self.engine.bitboard_p2
                        nouveau_bb = prochain_etat.bitboard_p2
                    else:
                        ancien_bb = self.engine.bitboard_p1
                        nouveau_bb = prochain_etat.bitboard_p1
                    bit_perdu = ancien_bb & ~nouveau_bb
                    bit_gagne = nouveau_bb & ~ancien_bb
                    if bit_perdu and bit_gagne:
                        src_idx = int(math.log2(bit_perdu))
                        dst_idx = int(math.log2(bit_gagne))
            elif self.ai_difficulty == "difficile":
                _, src_idx, dst_idx = alphabeta.alpha_beta(
                    self.engine, profondeur=6, alpha=-float('inf'), beta=float('inf'), joueur_max=self.engine.tour
                )

            t_end = time.perf_counter()
            self.last_ia_time_ms = (t_end - t_start) * 1000

            if src_idx is not None and dst_idx is not None:
                self._start_fly(NODE_IDS[src_idx], NODE_IDS[dst_idx])
            else:
                if self.demo_mode:
                    self.message = "Aucun mouvement possible. Partie terminée."
                else:
                    self.message = f"Au tour de {PLAYER_COLORS[self.engine.tour]['name']} — Aucun mouvement possible"
        else:
            mode_str = " " if self.game_mode == "HvIA" else ""
            self.message = f"Au tour de {PLAYER_COLORS[self.engine.tour]['name']}{mode_str} — Sélectionnez un pion"

    # ----------------------------------------------------------------------
    # ENTRÉES
    # ----------------------------------------------------------------------
    def on_mouse_motion(self, x, y, dx, dy):
        self.skin_button.on_mouse_motion(x, y)
        if self.fly_anim is None and not self.show_menu:
            self.hovered_node = self.node_at_pixel(x, y)
            self.undo_button.on_mouse_motion(x, y)
            self.redo_button.on_mouse_motion(x, y)
            self.menu_button.on_mouse_motion(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.fly_anim is not None:
            return

        # Bouton SKIN
        if self.skin_button.on_mouse_press(x, y):
            self.show_menu = not self.show_menu
            return

        # Bouton Undo
        if self.undo_button.on_mouse_press(x, y):
            self.undo()
            return

        # Bouton Redo
        if self.redo_button.on_mouse_press(x, y):
            self.redo()
            return

        # Bouton Menu (retour accueil)
        if self.menu_button.on_mouse_press(x, y):
            from accueil import AccueilView
            accueil = AccueilView()
            self.window.show_view(accueil)
            return

        if self.show_menu:
            w, h = self.window.width, self.window.height
            menu_w, menu_h = 440, 550
            menu_x, menu_y = w // 2 - menu_w // 2, h // 2 - menu_h // 2

            close_x, close_y = menu_x + menu_w - 30, menu_y + menu_h - 30
            if abs(x - close_x) <= 15 and abs(y - close_y) <= 15:
                self.show_menu = False
                return

            row_y = menu_y + menu_h - 70
            for skin in PieceSkin:
                if (menu_x + 20 < x < menu_x + menu_w - 20 and row_y - 16 < y < row_y + 16):
                    self.current_skin = skin
                    return
                row_y -= 45

            row_y -= 50
            for palette_name in COLOR_PALETTES.keys():
                if (menu_x + 20 < x < menu_x + menu_w - 20 and row_y - 14 < y < row_y + 14):
                    self.current_palette = palette_name
                    PLAYER_COLORS[1].update(COLOR_PALETTES[palette_name][1])
                    PLAYER_COLORS[2].update(COLOR_PALETTES[palette_name][2])
                    return
                row_y -= 35

            if (menu_x < x < menu_x + menu_w and menu_y < y < menu_y + menu_h):
                return
            self.show_menu = False
            return

        # Bloquer les clics humains pendant le mode démo ou le tour de l'IA
        if self.demo_mode or (self.game_mode == "HvIA" and self.engine.tour == 2):
            return
        node = self.node_at_pixel(x, y)
        if node is not None:
            self.try_select_or_move(node)

    def on_mouse_release(self, x, y, button, modifiers):
        self.undo_button.on_mouse_release()
        self.redo_button.on_mouse_release()
        self.menu_button.on_mouse_release()
        self.skin_button.on_mouse_release()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            self.reset_game()
        elif key == arcade.key.U:
            self.undo()
        elif key == arcade.key.Y:
            self.redo()
        elif key == arcade.key.M:
            from accueil import AccueilView
            accueil = AccueilView()
            self.window.show_view(accueil)
        elif key == arcade.key.ESCAPE:
            if self.show_menu:
                self.show_menu = False
            else:
                arcade.close_window()

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.board_cx = width  / 2
        self.board_cy = height / 2 + 10
        self.scale    = min(width, height) * 0.32
        self.update_node_positions()
        if self.fly_anim and self.flying_from and self.flying_to:
            prog = self.fly_anim.progress
            remaining = self.fly_anim.dur * (1 - prog)
            new_anim = FlyAnimation(
                self.node_screen_pos[self.flying_from],
                self.node_screen_pos[self.flying_to],
                self.fly_anim.player,
                duration=max(remaining, 0.05)
            )
            self.fly_anim = new_anim

        # Repositionnement des boutons de contrôle
        self.undo_button.x = width - 70
        self.undo_button.y = height - 150
        self.redo_button.x = width - 70
        self.redo_button.y = height - 210
        self.menu_button.x = width - 70
        self.menu_button.y = height - 270
        self.skin_button.x = width - 70
        self.skin_button.y = height - 330

    # ----------------------------------------------------------------------
    # MISE À JOUR
    # ----------------------------------------------------------------------
    def on_update(self, delta_time):
        self.time_elapsed += delta_time
        if self.fly_anim is not None:
            self.fly_anim.update(delta_time)
            if self.fly_anim.done:
                self._finish_fly()
        # En mode démo, on attend le délai avant de lancer le prochain coup
        if self.demo_mode and not self.winner and self.fly_anim is None:
            if time.time() >= self.demo_next_move_time:
                self.switch_player()

    # ----------------------------------------------------------------------
    # RENDU
    # ----------------------------------------------------------------------
    def on_draw(self):
        self.clear()
        self.draw_background()
        self.draw_board_3d()
        self.draw_lines()
        self.draw_nodes_and_pieces()
        self.draw_fly_piece()
        self.draw_hud()

        # Boutons (Undo, Redo, Menu)
        enabled_undo = bool(self.undo_stack) and self.fly_anim is None and not self.demo_mode
        self.undo_button.draw(enabled_undo)

        enabled_redo = bool(self.redo_stack) and self.fly_anim is None and not self.demo_mode
        self.redo_button.draw(enabled_redo)

        self.menu_button.draw(True)   # toujours actif

        self.skin_button.draw(active=self.show_menu)

        if self.show_menu:
            self.draw_menu()

    def draw_background(self):
        steps = 40
        h = self.window.height
        w = self.window.width
        for i in range(steps):
            t = i / steps
            color = tuple(
                int(COLOR_BG_BOTTOM[c] + (COLOR_BG_TOP[c] - COLOR_BG_BOTTOM[c]) * t)
                for c in range(3)
            )
            arcade.draw_lrbt_rectangle_filled(0, w, h * t, h * (t + 1/steps), color)

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

    def draw_nodes_and_pieces(self):
        targets = self.valid_targets(self.selected_node)
        for n in NODE_IDS:
            if n == self.flying_from:
                continue
            x, y     = self.node_screen_pos[n]
            occupant = self.engine.get_occupant(NODE_TO_BIT[n])
            if occupant is None:
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
        bounce = 0.0
        if node_id and node_id in self.piece_bounce:
            dt = self.time_elapsed - self.piece_bounce[node_id]
            if dt < 0.35:
                bounce = math.sin(dt / 0.35 * math.pi) * 7
        radius = PIECE_RADIUS
        cy = y + bounce
        if selected:
            beat = 0.5 + 0.5*math.sin(self.time_elapsed * 6)
            pulse_r = radius + 10 + beat * 6
            arcade.draw_circle_filled(x, y, pulse_r, (255, 230, 150, int(70 * alpha_factor)))
            arcade.draw_circle_outline(x, y, pulse_r - 4, (255, 220, 120), 3)

        self.draw_piece_shadow(x, cy, radius, alpha_factor)
        self.draw_piece_shape(x, cy, radius, player, colors, alpha_factor)

    def draw_piece_shadow(self, x, y, radius, alpha_factor=1.0):
        alpha = int(90 * alpha_factor)
        if self.current_skin == PieceSkin.CIRCLE:
            arcade.draw_circle_filled(x + 5, y - 8, radius * 0.95, (0, 0, 0, alpha))
        elif self.current_skin == PieceSkin.SQUARE:
            half = radius * 0.75
            points = [(x+5-half, y-8-half), (x+5+half, y-8-half), (x+5+half, y-8+half), (x+5-half, y-8+half)]
            arcade.draw_polygon_filled(points, (0, 0, 0, alpha))
        elif self.current_skin == PieceSkin.DIAMOND:
            points = [(x+5, y-8-radius*0.85), (x+5+radius*0.85, y-8), (x+5, y-8+radius*0.85), (x+5-radius*0.85, y-8)]
            arcade.draw_polygon_filled(points, (0, 0, 0, alpha))
        elif self.current_skin == PieceSkin.STAR:
            points = []
            for i in range(10):
                angle = i * math.pi / 5 - math.pi / 2
                r = radius * 0.85 if i % 2 == 0 else radius * 0.4
                points.append((x+5 + r*math.cos(angle), y-8 + r*math.sin(angle)))
            arcade.draw_polygon_filled(points, (0, 0, 0, alpha))
        elif self.current_skin == PieceSkin.HEXAGON:
            points = []
            for i in range(6):
                angle = i * math.pi / 3 - math.pi / 6
                points.append((x+5 + radius*0.8*math.cos(angle), y-8 + radius*0.8*math.sin(angle)))
            arcade.draw_polygon_filled(points, (0, 0, 0, alpha))

    def draw_piece_shape(self, x, y, radius, player, colors, alpha_factor=1.0):
        alpha = int(255 * alpha_factor)
        dark = (*colors["dark"], alpha)
        base = (*colors["base"], alpha)
        light = (*colors["light"], alpha)

        if self.current_skin == PieceSkin.CIRCLE:
            arcade.draw_circle_filled(x, y, radius * 0.92, base)
            arcade.draw_circle_filled(x - radius*0.32, y + radius*0.38, radius*0.42, light)
            arcade.draw_circle_filled(x - radius*0.45, y + radius*0.50, radius*0.14, (255, 255, 255, alpha))
            arcade.draw_circle_outline(x, y, radius * 0.92, dark, 2)
        elif self.current_skin == PieceSkin.SQUARE:
            half = radius * 0.75
            points = [(x-half, y-half), (x+half, y-half), (x+half, y+half), (x-half, y+half)]
            arcade.draw_polygon_filled(points, base)
            reflect = [(x-half*0.6, y+half*0.8), (x+half*0.8, y+half*0.8), (x+half*0.8, y+half*0.4)]
            arcade.draw_polygon_filled(reflect, light)
            arcade.draw_polygon_outline(points, dark, 2)
        elif self.current_skin == PieceSkin.DIAMOND:
            points = [(x, y-radius*0.85), (x+radius*0.85, y), (x, y+radius*0.85), (x-radius*0.85, y)]
            arcade.draw_polygon_filled(points, base)
            reflect = [(x, y-radius*0.5), (x+radius*0.3, y), (x, y+radius*0.2)]
            arcade.draw_polygon_filled(reflect, light)
            arcade.draw_polygon_outline(points, dark, 2)
        elif self.current_skin == PieceSkin.STAR:
            points = []
            for i in range(10):
                angle = i * math.pi / 5 - math.pi / 2
                r = radius * 0.85 if i % 2 == 0 else radius * 0.4
                points.append((x + r*math.cos(angle), y + r*math.sin(angle)))
            arcade.draw_polygon_filled(points, base)
            arcade.draw_polygon_outline(points, dark, 2)
        elif self.current_skin == PieceSkin.HEXAGON:
            points = []
            for i in range(6):
                angle = i * math.pi / 3 - math.pi / 6
                points.append((x + radius*0.8*math.cos(angle), y + radius*0.8*math.sin(angle)))
            arcade.draw_polygon_filled(points, base)
            reflect = [(x, y+radius*0.6), (x+radius*0.3, y+radius*0.3), (x+radius*0.4, y), (x, y+radius*0.4)]
            arcade.draw_polygon_filled(reflect, light)
            arcade.draw_polygon_outline(points, dark, 2)

    def draw_fly_piece(self):
        if self.fly_anim is None:
            return
        fx, fy = self.fly_anim.current_pos
        player  = self.fly_anim.player
        if self.flying_to:
            dx, dy = self.node_screen_pos[self.flying_to]
            p = self.fly_anim.progress
            sx = self.fly_anim.src[0] + (dx - self.fly_anim.src[0]) * p
            sy = self.fly_anim.src[1] + (dy - self.fly_anim.src[1]) * p
            shadow_a = self.fly_anim.shadow_alpha
            scale    = 0.6 + 0.4*(1 - math.sin(p * math.pi))
            arcade.draw_ellipse_filled(sx+3, sy-6, PIECE_RADIUS*scale*2, PIECE_RADIUS*scale, (0,0,0, shadow_a))
        self.draw_piece(fx, fy, player, selected=False, node_id=None)

    def draw_hud(self):
        w = self.window.width
        h = self.window.height

        arcade.draw_lrbt_rectangle_filled(0, w, h-64, h, (12, 14, 22, 230))
        arcade.draw_text("FANORON-TELO", 24, h-40, (240,220,170), 22, bold=True, anchor_y="center")

        if self.winner:
            color = (255, 215, 110)
        else:
            color = PLAYER_COLORS[self.engine.tour]["light"]

        msg = self.message
        if self.last_ia_time_ms > 0 and not self.winner:
            if self.demo_mode or (self.game_mode == "HvIA" and self.engine.tour == 2):
                msg += f"  ({self.last_ia_time_ms:.0f} ms)"
        arcade.draw_text(msg, 24, h-90, color, 15)

        if not self.winner:
            moved_p1 = bin(self.engine.moved_once_p1).count("1")
            moved_p2 = bin(self.engine.moved_once_p2).count("1")
            self.draw_piece(w-60, h-32, self.engine.tour, node_id=None)

        # Bandeau bas (commandes)
        arcade.draw_lrbt_rectangle_filled(0, w, 0, 40, (12,14,22,230))
        arcade.draw_text(
            "Clic : jouer | R:reset | U:undo | Y:redo | M:menu | Échap:quitter",
            w / 2, 20, (170,170,185), 10, anchor_x="center", anchor_y="center"
        )
        arcade.draw_text(
            "Règle : aligner 3 pions ayant tous bougé",
            # w - 24, 20, (130, 130, 150), 11, anchor_x="right", anchor_y="center"
             w / 2, 40, (130, 130, 150), 10, anchor_x="center", anchor_y="center"

        )

        if self.winner:
            bw, bh = 360, 120
            bx, by = w/2 - bw/2, h/2 - bh/2 - 30
            arcade.draw_lrbt_rectangle_filled(bx, bx+bw, by, by+bh, (20, 22, 36, 240))
            arcade.draw_lrbt_rectangle_outline(bx, bx+bw, by, by+bh, (255,215,110), 3)
            arcade.draw_text(self.message, w/2, by+bh-35, (255, 215, 110), 18, anchor_x="center", bold=True)
            arcade.draw_text("Appuyez sur R pour rejouer", w/2, by+35, (220, 200, 150), 14, anchor_x="center")

    def draw_menu(self):
        w = self.window.width
        h = self.window.height
        menu_w, menu_h = 440, 550
        menu_x = w//2 - menu_w//2
        menu_y = h//2 - menu_h//2

        arcade.draw_lrbt_rectangle_filled(0, w, 0, h, (0, 0, 0, 180))
        arcade.draw_lrbt_rectangle_filled(menu_x, menu_x+menu_w, menu_y, menu_y+menu_h, (30, 35, 50, 240))
        arcade.draw_lrbt_rectangle_outline(menu_x, menu_x+menu_w, menu_y, menu_y+menu_h, (240, 220, 170), 3)

        arcade.draw_text("CHOIX DU SKIN", w//2, menu_y+menu_h-30, (240, 220, 170), 20, anchor_x="center", bold=True)
        arcade.draw_line(menu_x+20, menu_y+menu_h-45, menu_x+menu_w-20, menu_y+menu_h-45, (100, 100, 120), 2)

        close_x = menu_x + menu_w - 30
        close_y = menu_y + menu_h - 30
        arcade.draw_text("✕", close_x, close_y, (255, 100, 100), 20, anchor_x="center", anchor_y="center")
        arcade.draw_lrbt_rectangle_outline(close_x-15, close_x+15, close_y-15, close_y+15, (100, 100, 120), 2)

        y = menu_y + menu_h - 70
        for skin in PieceSkin:
            is_selected = (skin == self.current_skin)
            color = (240, 220, 170) if is_selected else (170, 170, 185)
            rect_color = (60, 65, 80, 200) if is_selected else (40, 45, 60, 150)
            arcade.draw_lrbt_rectangle_filled(menu_x+20, menu_x+menu_w-20, y-16, y+16, rect_color)
            if is_selected:
                arcade.draw_lrbt_rectangle_outline(menu_x+20, menu_x+menu_w-20, y-16, y+16, (240, 220, 170), 2)

            preview_x = menu_x + 50
            preview_y = y
            radius = 12
            temp_colors = PLAYER_COLORS[1]
            old_skin = self.current_skin
            self.current_skin = skin
            self.draw_piece_shape(preview_x, preview_y, radius, 1, temp_colors, 1.0)
            self.current_skin = old_skin
            arcade.draw_text(skin.value, menu_x + 80, y, color, 14, anchor_y="center")
            if is_selected:
                arcade.draw_text("✓", menu_x + menu_w - 40, y, (100, 255, 100), 16, anchor_y="center")
            y -= 45

        y -= 20
        arcade.draw_text("PALETTES DE COULEURS", menu_x + 20, y, (200, 200, 210), 13, anchor_x="left")
        y -= 30
        for palette_name in COLOR_PALETTES.keys():
            is_selected = (palette_name == self.current_palette)
            color = (240, 220, 170) if is_selected else (170, 170, 185)
            rect_color = (60, 65, 80, 200) if is_selected else (40, 45, 60, 150)
            arcade.draw_lrbt_rectangle_filled(menu_x+20, menu_x+menu_w-20, y-14, y+14, rect_color)
            if is_selected:
                arcade.draw_lrbt_rectangle_outline(menu_x+20, menu_x+menu_w-20, y-14, y+14, (240, 220, 170), 2)
            arcade.draw_text(palette_name, menu_x + 80, y, color, 14, anchor_y="center")
            if is_selected:
                arcade.draw_text("✓", menu_x + menu_w - 40, y, (100, 255, 100), 16, anchor_y="center")
            y -= 35

        arcade.draw_text("Cliquez sur un skin ou une palette", w//2, menu_y + 15, (130, 130, 150), 12, anchor_x="center")


# ----------------------------------------------------------------------
# POINT D'ENTRÉE
# ----------------------------------------------------------------------

def main():
    window = arcade.Window(
        SCREEN_WIDTH, 
        SCREEN_HEIGHT, 
        SCREEN_TITLE, 
        resizable=True,
        antialiasing=True
    )
    window.set_minimum_size(600, 500)
    view = FanoronteloView()
    window.show_view(view)
    arcade.run()


if __name__ == "__main__":
    main()