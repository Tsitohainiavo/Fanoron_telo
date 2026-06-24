"""
MODULE IA - FANORONTELO TELO
Algorithme Alpha-Bêta avec structures Bitboards, Move Ordering,
évaluation améliorée et cache de transposition.
"""

import math
import random
from collections import defaultdict

# ----------------------------------------------------------------------
# CONSTANTES GÉOMÉTRIQUES (identiques à celles du moteur)
# ----------------------------------------------------------------------
NODE_IDS = ["NO", "N", "NE", "O", "C", "E", "SO", "S", "SE"]
NODE_TO_BIT = {name: idx for idx, name in enumerate(NODE_IDS)}

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

# ----------------------------------------------------------------------
# CACHE DE TRANSPOSITION
# ----------------------------------------------------------------------
class TranspositionTable:
    """Cache pour éviter de réévaluer les mêmes positions."""
    def __init__(self):
        self.table = {}

    def _key(self, engine):
        """Clé unique de l'état (bitboards + moved + tour)."""
        return (engine.bitboard_p1, engine.bitboard_p2,
                engine.moved_once_p1, engine.moved_once_p2,
                engine.tour)

    def lookup(self, engine, depth, alpha, beta):
        key = self._key(engine)
        if key not in self.table:
            return None
        stored_depth, stored_value, stored_type = self.table[key]
        if stored_depth >= depth:
            if stored_type == 'exact':
                return stored_value
            elif stored_type == 'lowerbound' and stored_value >= beta:
                return stored_value
            elif stored_type == 'upperbound' and stored_value <= alpha:
                return stored_value
        return None

    def store(self, engine, depth, value, flag):
        key = self._key(engine)
        self.table[key] = (depth, value, flag)

# ----------------------------------------------------------------------
# ÉVALUATION AMÉLIORÉE
# ----------------------------------------------------------------------
def evaluer_position(engine, joueur_max):
    """
    Retourne un score du point de vue de 'joueur_max'.
    """
    joueur_min = 2 if joueur_max == 1 else 1

    bb_max = engine.bitboard_p1 if joueur_max == 1 else engine.bitboard_p2
    bb_min = engine.bitboard_p2 if joueur_max == 1 else engine.bitboard_p1
    moved_max = engine.moved_once_p1 if joueur_max == 1 else engine.moved_once_p2
    moved_min = engine.moved_once_p2 if joueur_max == 1 else engine.moved_once_p1

    # 1. Victoire / défaite immédiate
    if engine.verifier_alignement_et_mouvement(bb_max, moved_max):
        return 10000
    if engine.verifier_alignement_et_mouvement(bb_min, moved_min):
        return -10000

    score = 0
    occupied = engine.get_occupied()

    # 2. Contrôle du centre (bit 4) – réduit pour éviter la précipitation
    if (bb_max & (1 << 4)) != 0:
        score += 20            # était 30
    if (bb_min & (1 << 4)) != 0:
        score -= 20

    # 3. Mobilité
    mob_max = 0
    mob_min = 0
    for src in range(9):
        if (bb_max & (1 << src)) != 0:
            mob_max += bin(ADJACENCY_MASKS[src] & ~occupied).count("1")
        if (bb_min & (1 << src)) != 0:
            mob_min += bin(ADJACENCY_MASKS[src] & ~occupied).count("1")
    score += (mob_max - mob_min) * 8     # était 10

    # 4. Progression (pions ayant bougé) – légèrement moins prioritaire
    pions_bouges_max = bin(bb_max & moved_max).count("1")
    pions_bouges_min = bin(bb_min & moved_min).count("1")
    score += (pions_bouges_max - pions_bouges_min) * 12   # était 15

    # 5. Détection de menaces simples
    # Si l'adversaire peut gagner au prochain coup, pénalité forte
    successeurs_min = get_successeurs_avec_coups(engine, joueur=joueur_min)
    for _, _, etat in successeurs_min:
        bb_min2 = etat.bitboard_p2 if joueur_min == 2 else etat.bitboard_p1
        moved_min2 = etat.moved_once_p2 if joueur_min == 2 else etat.moved_once_p1
        if etat.verifier_alignement_et_mouvement(bb_min2, moved_min2):
            score -= 500       # pénalité pour menace immédiate
            break

    return score


# ----------------------------------------------------------------------
# GÉNÉRATION DES SUCCESSEURS
# ----------------------------------------------------------------------
def get_successeurs_avec_coups(engine, joueur=None):
    """Retourne une liste de tuples (src, dst, instance_enfant)."""
    if joueur is None:
        joueur = engine.tour
    successeurs = []
    occupied = engine.get_occupied()
    bb_actuel = engine.bitboard_p1 if joueur == 1 else engine.bitboard_p2

    for src in range(9):
        if (bb_actuel & (1 << src)) != 0:
            destinations_possibles = ADJACENCY_MASKS[src] & ~occupied
            for dst in range(9):
                if (destinations_possibles & (1 << dst)) != 0:
                    enfant = engine.copier()
                    enfant.valider_et_deplacer(src, dst)
                    enfant.tour = 2 if joueur == 1 else 1
                    successeurs.append((src, dst, enfant))
    return successeurs


# ----------------------------------------------------------------------
# ALPHA-BÊTA AVEC CACHE
# ----------------------------------------------------------------------
def alpha_beta(engine, profondeur, alpha, beta, joueur_max, trans_table=None):
    """
    Algorithme Alpha-Bêta avec cache de transposition et élagage.
    Retourne (meilleur_score, meilleur_src, meilleur_dst).
    """
    if trans_table is None:
        trans_table = TranspositionTable()

    # Coupure : condition terminale
    bb_p1_win = engine.verifier_alignement_et_mouvement(engine.bitboard_p1, engine.moved_once_p1)
    bb_p2_win = engine.verifier_alignement_et_mouvement(engine.bitboard_p2, engine.moved_once_p2)
    if profondeur == 0 or bb_p1_win or bb_p2_win:
        val = evaluer_position(engine, joueur_max)
        return val, None, None

    # Vérification dans la table de transposition
    cached = trans_table.lookup(engine, profondeur, alpha, beta)
    if cached is not None:
        return cached, None, None   # le coup exact n'est pas stocké dans le cache simple

    successeurs = get_successeurs_avec_coups(engine)
    if not successeurs:
        val = evaluer_position(engine, joueur_max)
        return val, None, None

    # Move ordering : centre en priorité, puis mobilité décroissante
    def score_ordre(item):
        src, dst, enfant = item
        centre = 100 if dst == 4 else 0
        mob = bin(ADJACENCY_MASKS[dst] & ~enfant.get_occupied()).count("1")
        return centre + mob * 2

    successeurs.sort(key=score_ordre, reverse=True)

    meilleur_src = meilleur_dst = None

    if engine.tour == joueur_max:
        max_eval = -float('inf')
        for src, dst, enfant in successeurs:
            evaluation, _, _ = alpha_beta(enfant, profondeur - 1, alpha, beta, joueur_max, trans_table)
            if evaluation > max_eval:
                max_eval = evaluation
                meilleur_src, meilleur_dst = src, dst
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                trans_table.store(engine, profondeur, max_eval, 'lowerbound')
                break
        else:
            trans_table.store(engine, profondeur, max_eval, 'exact')
        return max_eval, meilleur_src, meilleur_dst
    else:
        min_eval = float('inf')
        for src, dst, enfant in successeurs:
            evaluation, _, _ = alpha_beta(enfant, profondeur - 1, alpha, beta, joueur_max, trans_table)
            if evaluation < min_eval:
                min_eval = evaluation
                meilleur_src, meilleur_dst = src, dst
            beta = min(beta, evaluation)
            if beta <= alpha:
                trans_table.store(engine, profondeur, min_eval, 'upperbound')
                break
        else:
            trans_table.store(engine, profondeur, min_eval, 'exact')
        return min_eval, meilleur_src, meilleur_dst