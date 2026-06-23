"""
FANORONTELO TELO 3D (Intégré avec Moteur de Jeu Bitboards)
===================
Jeu de stratégie malgache traditionnel.
"""

import arcade
import math
import time
import alphabeta

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

FLY_DURATION = 0.38
FLY_HEIGHT   = 90

# ----------------------------------------------------------------------
# GÉOMÉTRIE ET CONSTANTES BITBOARD
# ----------------------------------------------------------------------

NODE_IDS = ["NO", "N", "NE", "O", "C", "E", "SO", "S", "SE"]

# Mappage entre le nom textuel du nœud et son index de bit (0 à 8)
NODE_TO_BIT = {name: idx for idx, name in enumerate(NODE_IDS)}

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

# Dictionnaires d'adjacence pour le moteur Bitboard
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

# Placement initial binaire conforme aux règles définies
# Joueur 1 (Rouge) en haut : NO, N, NE (bits 0, 1, 2) -> 0b000000111 = 7
# Joueur 2 (Bleu) en bas : SO, S, SE (bits 6, 7, 8) -> 0b111000000 = 448
INITIAL_P1_BITBOARD = 7
INITIAL_P2_BITBOARD = 448

def project(pos, cx, cy, scale, tilt=0.62):
    x, y = pos
    return cx + x * scale, cy + y * scale * tilt


# ----------------------------------------------------------------------
# MOTEUR DE JEU LOGIQUE (BITBOARD & BACKEND) - RÔLE DÉVELOPPEUR 2
# ----------------------------------------------------------------------

class FanoronteloEngine:
    def __init__(self):
        self.reset()

    def reset(self):
        self.bitboard_p1 = INITIAL_P1_BITBOARD
        self.bitboard_p2 = INITIAL_P2_BITBOARD
        self.tour = 1
        
        # Ensembles de bits ayant bougé au moins une fois
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
        """Vérifie si le joueur aligne ses 3 pions ET qu'ils ont tous bougé."""
        # Dans le placement initial, aucun pion n'a bougé. Donc moved_joueur doit avoir 3 bits à 1
        # pour correspondre exactement aux positions actuelles des pions du joueur.
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

        # 1. Vérifier la possession du pion
        bb_actuel = self.bitboard_p1 if self.tour == 1 else self.bitboard_p2
        if (bb_actuel & mask_src) == 0:
            return False

        # 2. Vérifier que l'arrivée est vide
        if (occupied & mask_dst) != 0:
            return False

        # 3. Vérifier l'adjacence légale
        if (ADJACENCY_MASKS[bit_src] & mask_dst) == 0:
            return False

        # Appliquer le mouvement
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
        """Pour l'IA (Minimax)"""
        copie = FanoronteloEngine()
        copie.bitboard_p1 = self.bitboard_p1
        copie.bitboard_p2 = self.bitboard_p2
        copie.tour = self.tour
        copie.moved_once_p1 = self.moved_once_p1
        copie.moved_once_p2 = self.moved_once_p2
        return copie

    def get_successeurs(self):
        """Génère la liste des états successeurs légaux (Aide précieuse pour le Lead IA)"""
        successeurs = []
        occupied = self.get_occupied()
        bb_actuel = self.bitboard_p1 if self.tour == 1 else self.bitboard_p2

        # Parcourir les 9 positions pour trouver les pions du joueur actuel
        for src in range(9):
            if (bb_actuel & (1 << src)) != 0:
                # Obtenir les destinations valides via le masque d'adjacence bit à bit
                destinations_possibles = ADJACENCY_MASKS[src] & ~occupied
                for dst in range(9):
                    if (destinations_possibles & (1 << dst)) != 0:
                        enfant = self.copier()
                        enfant.valider_et_deplacer(src, dst)
                        # Alterner le joueur dans la copie
                        enfant.tour = 2 if enfant.tour == 1 else 1
                        successeurs.append(enfant)
        return successeurs


# ----------------------------------------------------------------------
# ANIMATION DE VOL
# ----------------------------------------------------------------------

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

        self.fly_anim: FlyAnimation | None = None
        self.flying_from: str | None = None
        self.flying_to:   str | None = None

        self.time_elapsed = 0.0
        self.piece_bounce: dict[str, float] = {}

        # Instance de notre moteur binaire
        self.engine = FanoronteloEngine()
        self.reset_game()

    def update_node_positions(self):
        self.node_screen_pos = {
            n: project(RAW_POSITIONS[n], self.board_cx, self.board_cy, self.scale)
            for n in NODE_IDS
        }

    def on_show_view(self):
        arcade.set_background_color((15, 17, 26))

    def reset_game(self):
        self.engine.reset()
        self.selected_node   = None
        self.hovered_node    = None
        self.winner          = None
        self.winning_line    = None
        self.piece_bounce    = {}
        self.fly_anim        = None
        self.flying_from     = None
        self.flying_to       = None
        self.message = f"Déplacez un pion — Joueur {PLAYER_COLORS[1]['name']}"

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
        
        # Récupération ultra-rapide par opérations bit à bit
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

        # Tentative de déplacement binaire si clic sur une case vide connectée
        if occupant is None:
            bit_src = NODE_TO_BIT[self.selected_node]
            if (ADJACENCY_MASKS[bit_src] & (1 << bit_idx)) != 0:
                self._start_fly(self.selected_node, node)

    def _start_fly(self, src, dst):
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

        # On applique le déplacement physique dans notre bitboard
        if self.engine.valider_et_deplacer(bit_src, bit_dst):
            self.piece_bounce[dst] = self.time_elapsed

        self.fly_anim    = None
        self.flying_from = None
        self.flying_to   = None

        # Vérification binaire de l'alignement
        bb_joueur = self.engine.bitboard_p1 if player == 1 else self.engine.bitboard_p2
        moved_joueur = self.engine.moved_once_p1 if player == 1 else self.engine.moved_once_p2
        
        if self.engine.verifier_alignement_et_mouvement(bb_joueur, moved_joueur):
            self.winner = player
            # Retrouver la ligne textuelle pour le tracé de la ligne lumineuse
            for line in WINNING_LINES:
                mask = 0
                for n in line:
                    mask |= (1 << NODE_TO_BIT[n])
                if (bb_joueur & mask) == mask:
                    self.winning_line = line
                    break
            self.message = f"🏆 Joueur {PLAYER_COLORS[player]['name']} a gagné !"
            return

        self.switch_player()

    def switch_player(self):
        self.engine.tour = 2 if self.engine.tour == 1 else 1
        
        if self.winner:
            return

        # Si c'est au tour du Joueur 2 (l'IA en Bleu)
        if self.engine.tour == 2:
            self.message = f"L'IA ({PLAYER_COLORS[2]['name']}) réfléchit..."
            
            # Calcul du meilleur coup (profondeur 6 pour un niveau Difficile imbattable)
            _, src_idx, dst_idx = alphabeta.alpha_beta(
                self.engine, profondeur=6, alpha=-float('inf'), beta=float('inf'), joueur_max=2
            )
            
            # Si un coup valide est trouvé, on lance l'animation de vol
            if src_idx is not None and dst_idx is not None:
                node_src = NODE_IDS[src_idx]
                node_dst = NODE_IDS[dst_idx]
                self._start_fly(node_src, node_dst)
        else:
            self.message = (
                f"Au tour de {PLAYER_COLORS[self.engine.tour]['name']} — "
                "Sélectionnez un pion"
            )

    # ------------------------------------------------------------------
    # ENTRÉES
    # ------------------------------------------------------------------
    def on_mouse_motion(self, x, y, dx, dy):
        if self.fly_anim is None:
            self.hovered_node = self.node_at_pixel(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        # Bloquer le clic si victoire, si un vol est en cours, ou si c'est au tour de l'IA (Joueur 2)
        if self.winner is not None or self.fly_anim is not None or self.engine.tour == 2:
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
        if self.fly_anim and self.flying_from and self.flying_to:
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

    def draw_background(self):
        steps = 40
        h = self.window.height
        for i in range(steps):
            t = i / steps
            color = tuple(
                int(COLOR_BG_BOTTOM[c] + (COLOR_BG_TOP[c] - COLOR_BG_BOTTOM[c]) * t)
                for c in range(3)
            )
            arcade.draw_lrbt_rectangle_filled(0, self.window.width, h * t, h * (t + 1/steps), color)

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

        if selected:
            beat = 0.5 + 0.5*math.sin(self.time_elapsed * 6)
            pulse_r = radius + 10 + beat * 6
            arcade.draw_circle_filled(x, y, pulse_r, (255, 230, 150, int(70 * alpha_factor)))
            arcade.draw_circle_outline(x, y, pulse_r - 4, (255, 220, 120), 3)

        cy = y + bounce

        arcade.draw_circle_filled(x+5, cy-8, radius*0.95, (0, 0, 0, int(90*alpha_factor)))
        arcade.draw_circle_filled(x, cy, radius, (*colors["dark"], int(255*alpha_factor)))
        arcade.draw_circle_filled(x, cy+2, radius*0.92, (*colors["base"], int(255*alpha_factor)))
        arcade.draw_circle_filled(x - radius*0.32, cy + radius*0.38, radius*0.42, (*colors["light"], int(180*alpha_factor)))
        arcade.draw_circle_filled(x - radius*0.45, cy + radius*0.50, radius*0.14, (255, 255, 255, int(200*alpha_factor)))
        arcade.draw_circle_outline(x, cy+2, radius*0.92, (*colors["dark"], int(200*alpha_factor)), 2)

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
        arcade.draw_text("FANORONTELO TELO 3D", 24, h-46, (240,220,170), 24, bold=True)

        if self.winner:
            color = (255, 215, 110)
        else:
            color = PLAYER_COLORS[self.engine.tour]["light"]
        arcade.draw_text(self.message, 24, h-90, color, 16)

        if not self.winner:
            # Compter les bits à 1 dans moved_once via bin().count("1")
            moved_p1 = bin(self.engine.moved_once_p1).count("1")
            moved_p2 = bin(self.engine.moved_once_p2).count("1")
            
            # Affichage correct des statistiques de mouvements des joueurs
            arcade.draw_text(f"Rouge — pions bougés : {moved_p1}/3", 24, h-116, PLAYER_COLORS[1]["light"], 13)
            arcade.draw_text(f"Bleu — pions bougés : {moved_p2}/3", w//2, h-116, PLAYER_COLORS[2]["light"], 13)
        if not self.winner:
            self.draw_piece(w-60, h-32, self.engine.tour, node_id=None)

        arcade.draw_lrbt_rectangle_filled(0, w, 0, 40, (12,14,22,230))
        arcade.draw_text("Clic : sélectionner / déplacer   |   R : recommencer   |   Échap : quitter", 24, 12, (170,170,185), 13)

        arcade.draw_text("Règle : aligner 3 pions, chacun ayant bougé au moins une fois", w - 24, 12, (130, 130, 150), 11, anchor_x="right")

        if self.winner:
            bw, bh = 360, 120
            bx, by = w/2 - bw/2, h/2 - bh/2 - 30
            arcade.draw_lrbt_rectangle_filled(bx, bx+bw, by, by+bh, (20, 22, 36, 240))
            arcade.draw_lrbt_rectangle_outline(bx, bx+bw, by, by+bh, (255,215,110), 3)
            arcade.draw_text(self.message, w/2, by+bh-28, (255, 215, 110), 22, anchor_x="center", bold=True)
            arcade.draw_text("Appuyez sur R pour rejouer", w/2, by+28, (220, 200, 150), 15, anchor_x="center")


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