"""Moteur de jeu Fanorontelo (bitboards) et animation de déplacement."""

import math
from constants import (
    NODE_IDS, NODE_TO_BIT, ADJACENCY_MASKS, WINNING_MASKS,
    INITIAL_P1_BITBOARD, INITIAL_P2_BITBOARD, FLY_DURATION, FLY_HEIGHT
)

class FanoronteloEngine:
    """Gère l'état du plateau et les règles en bitboard."""

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
        """Vérifie si le joueur a aligné 3 pions ayant tous bougé."""
        if (bb_joueur & moved_joueur) != bb_joueur:
            return False
        for masque in WINNING_MASKS:
            if (bb_joueur & masque) == masque:
                return True
        return False

    def valider_et_deplacer(self, bit_src, bit_dst):
        """Valide et exécute un déplacement. Retourne True si OK."""
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
        """Retourne une copie profonde de l'état."""
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
    """Animation d'un pion volant de src_pos à dst_pos."""

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
        return p * p * (3 - 2 * p)  # easing

    @property
    def current_pos(self):
        p = self.progress
        x = self.src[0] + (self.dst[0] - self.src[0]) * p
        y = self.src[1] + (self.dst[1] - self.src[1]) * p
        arc = math.sin(p * math.pi) * FLY_HEIGHT
        return x, y + arc

    @property
    def shadow_alpha(self):
        p = self.progress
        return int(90 * (1 - math.sin(p * math.pi) * 0.7))


def project(pos, cx, cy, scale, tilt=0.62):
    """Projette une position logique en coordonnées écran."""
    x, y = pos
    return cx + x * scale, cy + y * scale * tilt