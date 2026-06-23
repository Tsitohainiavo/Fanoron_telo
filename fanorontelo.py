"""
FANORONTELO TELO 3D
===================
Jeu de stratégie malgache traditionnel.

Règles :
- 2 joueurs, 3 pions chacun.
- Phase 1 (placement) : les pions sont déjà placés — Rouge en haut (NO, N, NE),
  Bleu en bas (SO, S, SE).
- Phase 2 (déplacement) : chaque joueur déplace l'un de ses pions vers un point
  voisin libre (le long d'une ligne).
- Pour gagner : aligner ses 3 pions sur une même ligne du plateau,
  ET chaque pion doit avoir été déplacé au moins une fois.

Animations :
- Lévitation/vol du pion sélectionné vers sa destination.
- Affichage des cibles valides avec halo pulsant.
- Battement du pion sélectionné.
- Effet pseudo-3D complet (plateau incliné, ombres, pions sphériques).

Installation :
    pip install arcade

Lancement :
    python fanorontelo.py
"""

import arcade
import math
import time

# ----------------------------------------------------------------------
# CONFIGURATION GÉNÉRALE
# ----------------------------------------------------------------------

SCREEN_WIDTH  = 1000
SCREEN_HEIGHT = 760
SCREEN_TITLE  = "Fanorontelo Telo 3D"

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
    """Anime un pion qui « lévite » de src_pos à dst_pos en arc de cercle."""

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
        arcade.draw_text("FANORONTELO TELO 3D", 24, h-46, (240,220,170), 24, bold=True)

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
                arcade.draw_text(
                    f"{pname} — pions bougés : {moved}/3",
                    bx, h-116,
                    PLAYER_COLORS[p]["light"], 13
                )

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
FANORONTELO 3D
==============
Jeu de stratégie malgache traditionnel (variante simplifiée du Fanorona),
joué sur un plateau triangulaire à 6 points reliés par 9 lignes.

modifie ce code(actuellement en règle de morpion) pour:
Règles fanorona telo:
- 2 joueurs, 3 pions chacun.
- Phase 1 (placement) : les poins respectifs des deux joueurs sont déja placés
sur le plateau, en haut à l'horizontale du plateau et en bas pour l'adversaire
- Phase 2 (déplacement) : chaque joueur
  déplace l'un de ses pions vers un point voisin libre (le long d'une ligne).
- Le premier joueur qui aligne ses 3 pions(chaque pion doit s'etre deplacé au moins une fois) sur une même ligne du plateau
  gagne la partie.
avec transition de lévitement des pions lors du déplacement
présentation des déplacements possibles après avoir séléctionné un pion, qui bat quand il est séléctionné

Rendu : effet pseudo-3D (plateau incliné, ombres portées, pions sphériques
avec dégradé, surbrillance douce, animations de survol/sélection).

Installation :
    pip install arcade

Lancement :
    python fanorontelo.py


import arcade
import math
import time

# ----------------------------------------------------------------------
# CONFIGURATION GÉNÉRALE
# ----------------------------------------------------------------------

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 760
SCREEN_TITLE = "Fanorontelo 3D"

# Palette moderne (bois sombre / or / bleu nuit / corail)
COLOR_BG_TOP = (20, 24, 38)
COLOR_BG_BOTTOM = (10, 12, 20)
COLOR_BOARD_TOP = (92, 64, 38)        # bois clair (face supérieure du plateau)
COLOR_BOARD_SIDE = (52, 36, 22)       # bois foncé (côté/épaisseur -> effet 3D)
COLOR_BOARD_EDGE = (140, 102, 58)
COLOR_LINE = (224, 196, 140)
COLOR_LINE_SHADOW = (40, 28, 16)
COLOR_NODE_IDLE = (224, 196, 140)
COLOR_NODE_HOVER = (255, 224, 130)
COLOR_NODE_VALID = (110, 220, 150)

PLAYER_COLORS = {
    1: {"base": (224, 86, 86), "light": (255, 150, 130), "dark": (120, 30, 30), "name": "Rouge"},
    2: {"base": (70, 150, 235), "light": (150, 210, 255), "dark": (20, 60, 120), "name": "Bleu"},
}

PIECE_RADIUS = 28
NODE_RADIUS = 16
HOVER_RADIUS = 24

# ----------------------------------------------------------------------
# GÉOMÉTRIE DU PLATEAU DE FANORONTELO
# ----------------------------------------------------------------------
# Le plateau est un carré de 9 points : les 4 coins, les 4 milieux des
# côtés, et 1 point central. Les lignes tracées sont : les 4 côtés du
# carré (chacun coupé en 2 segments par son point milieu), les 2 médianes
# (horizontale et verticale, passant par le centre), et les 2 diagonales.
# Toutes les lignes passant par 3 points alignés sont des lignes de
# victoire possibles : 3 lignes, 3 colonnes, 2 diagonales = 8 au total.

NODE_IDS = ["NO", "N", "NE", "O", "C", "E", "SO", "S", "SE"]
# Points cardinaux : N/S/E/O = milieux des côtés, NO/NE/SO/SE = coins, C = centre

# Coordonnées normalisées (avant transformation pseudo-3D), centrées sur (0,0)
RAW_POSITIONS = {
    "NO": (-1.0,  1.0),
    "N":  ( 0.0,  1.0),
    "NE": ( 1.0,  1.0),
    "O":  (-1.0,  0.0),
    "C":  ( 0.0,  0.0),
    "E":  ( 1.0,  0.0),
    "SO": (-1.0, -1.0),
    "S":  ( 0.0, -1.0),
    "SE": ( 1.0, -1.0),
}

# Toutes les lignes (segments) du plateau, utilisées pour le tracé ET
# pour savoir quels déplacements/alignements sont valides (un pion ne
# peut se déplacer que vers un point directement relié par un segment).
EDGES = [
    # côtés du carré (haut, bas, gauche, droite), coupés par leur milieu
    ("NO", "N"), ("N", "NE"),
    ("SO", "S"), ("S", "SE"),
    ("NO", "O"), ("O", "SO"),
    ("NE", "E"), ("E", "SE"),
    # médianes passant par le centre
    ("N", "C"), ("C", "S"),
    ("O", "C"), ("C", "E"),
    # diagonales passant par le centre
    ("NO", "C"), ("C", "SE"),
    ("NE", "C"), ("C", "SO"),
]

# Lignes complètes de 3 points alignés (utilisées pour vérifier la victoire)
WINNING_LINES = [
    ("NO", "N", "NE"),   # ligne du haut
    ("SO", "S", "SE"),   # ligne du bas
    ("NO", "O", "SO"),   # colonne de gauche
    ("NE", "E", "SE"),   # colonne de droite
    ("N", "C", "S"),     # médiane verticale
    ("O", "C", "E"),     # médiane horizontale
    ("NO", "C", "SE"),   # diagonale \
    ("NE", "C", "SO"),   # diagonale /
]

# Construction de la table d'adjacence (voisins directs) à partir des EDGES
ADJACENCY = {n: set() for n in NODE_IDS}
for a, b in EDGES:
    ADJACENCY[a].add(b)
    ADJACENCY[b].add(a)


def project(pos, center_x, center_y, scale, tilt=0.62):
    #Transforme une coordonnée 'logique' (x, y) en coordonnée écran,avec un léger aplatissement vertical pour donner une perspective    inclinée façon plateau de jeu vu en 3D.
    x, y = pos
    sx = center_x + x * scale
    sy = center_y + y * scale * tilt
    return sx, sy


# ----------------------------------------------------------------------
# CLASSE PRINCIPALE DU JEU
# ----------------------------------------------------------------------

class FanorontelView(arcade.View):
    def __init__(self):
        super().__init__()
        self.board_cx = SCREEN_WIDTH / 2
        self.board_cy = SCREEN_HEIGHT / 2 + 10
        self.scale = 230

        # positions écran de chaque noeud, calculées dans on_show_view / resize
        self.node_screen_pos = {}
        self.update_node_positions()

        # état du jeu
        self.board = {n: None for n in NODE_IDS}   # None, 1 ou 2
        self.current_player = 1
        self.phase = "placement"                    # "placement" puis "movement"
        self.placed_count = {1: 0, 2: 0}
        self.selected_node = None                    # noeud sélectionné en phase mouvement
        self.hovered_node = None
        self.winner = None
        self.winning_line = None
        self.message = "Phase de placement — Joueur Rouge commence"

        self.time_elapsed = 0.0
        self.piece_bounce = {}   # animation légère de "pose" pour chaque pion

        self.bg_shapes = None

    # ------------------------------------------------------------------
    def update_node_positions(self):
        self.node_screen_pos = {
            n: project(RAW_POSITIONS[n], self.board_cx, self.board_cy, self.scale)
            for n in NODE_IDS
        }

    # ------------------------------------------------------------------
    def on_show_view(self):
        arcade.set_background_color((15, 17, 26))

    # ------------------------------------------------------------------
    def on_update(self, delta_time):
        self.time_elapsed += delta_time

    # ------------------------------------------------------------------
    def reset_game(self):
        self.board = {n: None for n in NODE_IDS}
        self.current_player = 1
        self.phase = "placement"
        self.placed_count = {1: 0, 2: 0}
        self.selected_node = None
        self.hovered_node = None
        self.winner = None
        self.winning_line = None
        self.piece_bounce = {}
        self.message = "Phase de placement — Joueur Rouge commence"

    # ------------------------------------------------------------------
    # LOGIQUE DE JEU
    # ------------------------------------------------------------------
    def check_winner(self, player):
        for line in WINNING_LINES:
            if all(self.board[n] == player for n in line):
                return line
        return None

    def node_at_pixel(self, x, y):
        #Retourne l'id du noeud le plus proche du clic, si dans la zone cliquable.
        best, best_d = None, 1e9
        for n, (nx, ny) in self.node_screen_pos.items():
            d = math.hypot(x - nx, y - ny)
            if d < best_d:
                best_d = d
                best = n
        if best_d <= max(PIECE_RADIUS, NODE_RADIUS) + 10:
            return best
        return None

    def try_place(self, node):
        if self.board[node] is not None:
            return
        self.board[node] = self.current_player
        self.piece_bounce[node] = self.time_elapsed
        self.placed_count[self.current_player] += 1

        win_line = self.check_winner(self.current_player)
        if win_line:
            self.winner = self.current_player
            self.winning_line = win_line
            self.message = f"Joueur {PLAYER_COLORS[self.current_player]['name']} a gagné !"
            return

        if self.placed_count[1] == 3 and self.placed_count[2] == 3:
            self.phase = "movement"
            self.message = "Phase de déplacement — déplacez un pion vers un point voisin libre"

        self.switch_player()

    def try_select_or_move(self, node):
        if self.selected_node is None:
            # sélection d'un pion appartenant au joueur courant
            if self.board[node] == self.current_player:
                self.selected_node = node
            return
        else:
            if node == self.selected_node:
                self.selected_node = None
                return
            if self.board[node] == self.current_player:
                # changer la sélection vers un autre pion du joueur
                self.selected_node = node
                return
            if self.board[node] is None and node in ADJACENCY[self.selected_node]:
                # déplacement valide
                self.board[self.selected_node] = None
                self.board[node] = self.current_player
                self.piece_bounce[node] = self.time_elapsed
                self.selected_node = None

                win_line = self.check_winner(self.current_player)
                if win_line:
                    self.winner = self.current_player
                    self.winning_line = win_line
                    self.message = f"Joueur {PLAYER_COLORS[self.current_player]['name']} a gagné !"
                    return
                self.switch_player()

    def switch_player(self):
        self.current_player = 2 if self.current_player == 1 else 1
        if self.winner is None:
            verb = "placer un pion" if self.phase == "placement" else "déplacer un pion"
            self.message = f"Au tour de {PLAYER_COLORS[self.current_player]['name']} — {verb}"

    # ------------------------------------------------------------------
    # ENTRÉES UTILISATEUR
    # ------------------------------------------------------------------
    def on_mouse_motion(self, x, y, dx, dy):
        self.hovered_node = self.node_at_pixel(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.winner is not None:
            return
        node = self.node_at_pixel(x, y)
        if node is None:
            return
        if self.phase == "placement":
            self.try_place(node)
        else:
            self.try_select_or_move(node)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            self.reset_game()
        elif key == arcade.key.ESCAPE:
            arcade.close_window()

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.board_cx = width / 2
        self.board_cy = height / 2 + 10
        self.scale = min(width, height) * 0.32
        self.update_node_positions()

    # ------------------------------------------------------------------
    # RENDU
    # ------------------------------------------------------------------
    def on_draw(self):
        self.clear()
        self.draw_background()
        self.draw_board_3d()
        self.draw_lines()
        self.draw_nodes_and_pieces()
        self.draw_hud()

    # ----------------------- fond degrade -----------------------------
    def draw_background(self):
        arcade.draw_lrbt_rectangle_filled(
            0, self.window.width, 0, self.window.height, COLOR_BG_BOTTOM
        )
        # dégradé simple par bandes horizontales pour suggérer une ambiance studio
        steps = 40
        h = self.window.height
        for i in range(steps):
            t = i / steps
            y0 = h * t
            y1 = h * (t + 1 / steps)
            color = tuple(
                int(COLOR_BG_BOTTOM[c] + (COLOR_BG_TOP[c] - COLOR_BG_BOTTOM[c]) * t)
                for c in range(3)
            )
            arcade.draw_lrbt_rectangle_filled(0, self.window.width, y0, y1, color)

    # ----------------------- plateau pseudo-3D -------------------------
    def draw_board_3d(self):
        # coins du carré, dans l'ordre pour former un polygone fermé
        pts = [self.node_screen_pos[n] for n in ("NO", "NE", "SE", "SO")]
        n = len(pts)
        depth = 26  # épaisseur visuelle du plateau (effet 3D)

        # Face "côté" (ombre épaisse en dessous, légèrement décalée vers le bas)
        side_pts = [(x, y - depth) for x, y in pts]
        # On dessine un polygone qui relie le dessus et le dessous pour
        # simuler l'épaisseur du plateau (extrusion simple).
        for i in range(n):
            p1 = pts[i]
            p2 = pts[(i + 1) % n]
            s1 = side_pts[i]
            s2 = side_pts[(i + 1) % n]
            arcade.draw_polygon_filled([p1, p2, s2, s1], COLOR_BOARD_SIDE)

        # Ombre projetée au sol
        shadow_pts = [(x + 14, y - depth - 18) for x, y in pts]
        arcade.draw_polygon_filled(shadow_pts, (0, 0, 0, 110))

        # Face supérieure du plateau (légèrement plus grande que le carré de jeu)
        margin_pts = self.expand_polygon(pts, 1.28)
        arcade.draw_polygon_filled(margin_pts, COLOR_BOARD_TOP)
        arcade.draw_polygon_outline(margin_pts, COLOR_BOARD_EDGE, 4)

        # Liseré doré intérieur (effet incrustation)
        inner_pts = self.expand_polygon(pts, 1.12)
        arcade.draw_polygon_outline(inner_pts, COLOR_BOARD_EDGE, 2)

    @staticmethod
    def expand_polygon(pts, factor):
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        return [(cx + (x - cx) * factor, cy + (y - cy) * factor) for x, y in pts]

    # ----------------------- lignes du plateau -------------------------
    def draw_lines(self):
        for a, b in EDGES:
            p1 = self.node_screen_pos[a]
            p2 = self.node_screen_pos[b]
            # ombre légère sous la ligne (effet gravé dans le bois)
            arcade.draw_line(p1[0] + 2, p1[1] - 3, p2[0] + 2, p2[1] - 3, COLOR_LINE_SHADOW, 5)
            arcade.draw_line(p1[0], p1[1], p2[0], p2[1], COLOR_LINE, 3)

        # surbrillance de la ligne gagnante
        if self.winning_line:
            pts = [self.node_screen_pos[n] for n in self.winning_line]
            pulse = 0.5 + 0.5 * math.sin(self.time_elapsed * 4)
            glow_color = (255, int(210 + 30 * pulse), 90)
            for i in range(len(pts) - 1):
                arcade.draw_line(*pts[i], *pts[i + 1], glow_color, 7)

    # ----------------------- noeuds + pions -----------------------------
    def draw_nodes_and_pieces(self):
        valid_targets = set()
        if self.phase == "movement" and self.selected_node:
            valid_targets = {
                n for n in ADJACENCY[self.selected_node] if self.board[n] is None
            }

        for n in NODE_IDS:
            x, y = self.node_screen_pos[n]
            occupant = self.board[n]

            if occupant is None:
                # point vide : pastille creuse, avec effets hover/valid
                if n in valid_targets:
                    arcade.draw_circle_filled(x, y, NODE_RADIUS + 6, (*COLOR_NODE_VALID, 60))
                    arcade.draw_circle_outline(x, y, NODE_RADIUS + 6, COLOR_NODE_VALID, 3)
                elif n == self.hovered_node:
                    arcade.draw_circle_filled(x, y, HOVER_RADIUS, (*COLOR_NODE_HOVER, 70))

                arcade.draw_circle_filled(x, y, NODE_RADIUS * 0.55, COLOR_LINE_SHADOW)
                arcade.draw_circle_filled(x, y, NODE_RADIUS * 0.40, COLOR_NODE_IDLE)
            else:
                self.draw_piece(x, y, occupant, selected=(n == self.selected_node), node_id=n)

    def draw_piece(self, x, y, player, selected=False, node_id=None):
        colors = PLAYER_COLORS[player]

        # petite animation "rebond" quand un pion vient d'être posé
        bounce = 0.0
        if node_id in self.piece_bounce:
            dt = self.time_elapsed - self.piece_bounce[node_id]
            if dt < 0.25:
                bounce = math.sin(dt / 0.25 * math.pi) * 6
        radius = PIECE_RADIUS

        # halo de sélection animé
        if selected:
            pulse = 6 * (0.5 + 0.5 * math.sin(self.time_elapsed * 6))
            arcade.draw_circle_filled(x, y, radius + 12 + pulse, (255, 230, 150, 80))
            arcade.draw_circle_outline(x, y, radius + 10, (255, 220, 120), 3)

        # ombre portée du pion (effet de hauteur / 3D)
        arcade.draw_circle_filled(x + 5, y - 8 - bounce * 0.3, radius * 0.95, (0, 0, 0, 90))

        cy = y + bounce
        # corps du pion (cercle de base, plus sombre)
        arcade.draw_circle_filled(x, cy, radius, colors["dark"])
        # corps principal
        arcade.draw_circle_filled(x, cy + 2, radius * 0.92, colors["base"])
        # reflet supérieur gauche pour suggérer une sphère (effet 3D)
        arcade.draw_circle_filled(
            x - radius * 0.32, cy + radius * 0.38, radius * 0.42, colors["light"]
        )
        # petit point de lumière spéculaire
        arcade.draw_circle_filled(
            x - radius * 0.45, cy + radius * 0.5, radius * 0.14, (255, 255, 255, 200)
        )
        # contour fin
        arcade.draw_circle_outline(x, cy + 2, radius * 0.92, colors["dark"], 2)

    # ----------------------- interface (HUD) -----------------------------
    def draw_hud(self):
        w = self.window.width
        h = self.window.height

        # bandeau titre
        arcade.draw_lrbt_rectangle_filled(0, w, h - 64, h, (12, 14, 22, 230))
        arcade.draw_text(
            "FANORONTELO 3D", 24, h - 46, (240, 220, 170), 26,
            bold=True
        )

        # joueur courant / message
        if self.winner:
            txt = self.message
            color = (255, 215, 110)
        else:
            txt = self.message
            color = PLAYER_COLORS[self.current_player]["light"]
        arcade.draw_text(txt, 24, h - 90, color, 16)

        # scores / pions restants à placer
        if self.phase == "placement" and not self.winner:
            restants_1 = 3 - self.placed_count[1]
            restants_2 = 3 - self.placed_count[2]
            arcade.draw_text(
                f"Pions restants — Rouge: {restants_1}   Bleu: {restants_2}",
                24, h - 116, (200, 200, 210), 14
            )

        # pastille indicatrice du joueur courant (petit pion HUD)
        if not self.winner:
            self.draw_piece(w - 60, h - 32, self.current_player, selected=False, node_id=None)

        # bandeau bas : aide
        arcade.draw_lrbt_rectangle_filled(0, w, 0, 40, (12, 14, 22, 230))
        help_txt = "Clic : jouer   |   R : recommencer   |   Échap : quitter"
        arcade.draw_text(help_txt, 24, 12, (170, 170, 185), 13)

        # bouton "Nouvelle partie" si victoire
        if self.winner:
            arcade.draw_lrbt_rectangle_filled(
                w / 2 - 140, w / 2 + 140, h / 2 - 130, h / 2 - 80, (30, 34, 48, 235)
            )
            arcade.draw_lrbt_rectangle_outline(
                w / 2 - 140, w / 2 + 140, h / 2 - 130, h / 2 - 80, (255, 215, 110), 2
            )
            arcade.draw_text(
                "Appuyez sur R pour rejouer", w / 2, h / 2 - 105,
                (255, 215, 110), 16, anchor_x="center", anchor_y="center"
            )


# ----------------------------------------------------------------------
# POINT D'ENTRÉE
# ----------------------------------------------------------------------

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=True)
    view = FanorontelView()
    window.show_view(view)
    arcade.run()


if __name__ == "__main__":
    main()
"""