"""
MODULE IA - FANORONTELO TELO
Algorithme Alpha-Bêta avec structures Bitboards et Move Ordering.
"""

# CONSTANTES GÉOMÉTRIQUES
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

def evaluer_position(engine, joueur_max):
    """
    Fonction d'évaluation heuristique du plateau.
    Retourne un score du point de vue de 'joueur_max'.
    """
    joueur_min = 2 if joueur_max == 1 else 1

    bb_max = engine.bitboard_p1 if joueur_max == 1 else engine.bitboard_p2
    bb_min = engine.bitboard_p2 if joueur_max == 1 else engine.bitboard_p1
    
    moved_max = engine.moved_once_p1 if joueur_max == 1 else engine.moved_once_p2
    moved_min = engine.moved_once_p2 if joueur_max == 1 else engine.moved_once_p1

    # 1. Condition de Victoire / Défaite immédiate
    if engine.verifier_alignement_et_mouvement(bb_max, moved_max):
        return 10000
    if engine.verifier_alignement_et_mouvement(bb_min, moved_min):
        return -10000

    score = 0
    occupied = engine.get_occupied()

    # 2. Contrôle stratégique du centre (Intersection 'C' = bit index 4)
    if (bb_max & (1 << 4)) != 0:
        score += 30
    if (bb_min & (1 << 4)) != 0:
        score -= 30

    # 3. Mobilité (Nombre de mouvements légaux disponibles)
    mouvements_max = 0
    mouvements_min = 0
    for src in range(9):
        if (bb_max & (1 << src)) != 0:
            mouvements_max += bin(ADJACENCY_MASKS[src] & ~occupied).count("1")
        if (bb_min & (1 << src)) != 0:
            mouvements_min += bin(ADJACENCY_MASKS[src] & ~occupied).count("1")
    
    score += (mouvements_max - mouvements_min) * 10

    # 4. Progression de la règle de mouvement (Bonus si les pions ont bougé)
    pions_bouges_max = bin(bb_max & moved_max).count("1")
    pions_bouges_min = bin(bb_min & moved_min).count("1")
    score += (pions_bouges_max - pions_bouges_min) * 15

    return score

def get_successeurs_avec_coups(engine):
    """Retourne une liste de tuples (src, dst, instance_enfant) pour l'Alpha-Bêta."""
    successeurs = []
    occupied = engine.get_occupied()
    bb_actuel = engine.bitboard_p1 if engine.tour == 1 else engine.bitboard_p2

    for src in range(9):
        if (bb_actuel & (1 << src)) != 0:
            destinations_possibles = ADJACENCY_MASKS[src] & ~occupied
            for dst in range(9):
                if (destinations_possibles & (1 << dst)) != 0:
                    enfant = engine.copier()
                    enfant.valider_et_deplacer(src, dst)
                    enfant.tour = 2 if engine.tour == 1 else 1
                    successeurs.append((src, dst, enfant))
    return successeurs

def alpha_beta(engine, profondeur, alpha, beta, joueur_max):
    """
    Algorithme Alpha-Bêta optimisé avec Move Ordering.
    Retourne un tuple: (meilleur_score, meilleur_coup_src, meilleur_coup_dst)
    """
    bb_p1_win = engine.verifier_alignement_et_mouvement(engine.bitboard_p1, engine.moved_once_p1)
    bb_p2_win = engine.verifier_alignement_et_mouvement(engine.bitboard_p2, engine.moved_once_p2)
    
    if profondeur == 0 or bb_p1_win or bb_p2_win:
        return evaluer_position(engine, joueur_max), None, None

    successeurs = get_successeurs_avec_coups(engine)
    if not successeurs:
        return evaluer_position(engine, joueur_max), None, None

    # --- OPTIMISATION : MOVE ORDERING ---
    # Priorité sur la case centrale (index 4)
    successeurs.sort(key=lambda item: 100 if item[1] == 4 else 0, reverse=True)

    meilleur_src = None
    meilleur_dst = None

    if engine.tour == joueur_max:
        max_eval = -float('inf')
        for src, dst, enfant in successeurs:
            evaluation, _, _ = alpha_beta(enfant, profondeur - 1, alpha, beta, joueur_max)
            if evaluation > max_eval:
                max_eval = evaluation
                meilleur_src = src
                meilleur_dst = dst
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break  # Coupure Bêta
        return max_eval, meilleur_src, meilleur_dst
    else:
        min_eval = float('inf')
        for src, dst, enfant in successeurs:
            evaluation, _, _ = alpha_beta(enfant, profondeur - 1, alpha, beta, joueur_max)
            if evaluation < min_eval:
                min_eval = evaluation
                meilleur_src = src
                meilleur_dst = dst
            beta = min(beta, evaluation)
            if beta <= alpha:
                break  # Coupure Alpha
        return min_eval, meilleur_src, meilleur_dst