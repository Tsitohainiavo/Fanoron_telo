"""
MODULE IA - FANORONTELO TELO
Algorithme Alpha-Bêta compatible avec le plateau de benchmark.
"""

from math import inf


def _normalize_player(joueur):
    return 1 if joueur in (1, True) else -1


def evaluer_position(engine, joueur_max):
    """Fonction d'évaluation heuristique du plateau."""
    joueur_max = _normalize_player(joueur_max)
    bb_max = engine.bitboard_p1 if joueur_max == 1 else engine.bitboard_p2
    bb_min = engine.bitboard_p2 if joueur_max == 1 else engine.bitboard_p1

    if engine.verifier_alignement(bb_max):
        return 10000
    if engine.verifier_alignement(bb_min):
        return -10000

    score = 0
    occupied = engine.get_occupied()

    if (bb_max & (1 << 4)) != 0:
        score += 30
    if (bb_min & (1 << 4)) != 0:
        score -= 30

    mouvements_max = 0
    mouvements_min = 0
    if engine.phase == 2:
        for src in range(9):
            if (bb_max & (1 << src)) != 0:
                mouvements_max += bin(engine.ADJACENCY_MASKS[src] & ~occupied).count("1")
            if (bb_min & (1 << src)) != 0:
                mouvements_min += bin(engine.ADJACENCY_MASKS[src] & ~occupied).count("1")
    else:
        score += (engine.pions_places_p1 - engine.pions_places_p2) * 2

    score += (mouvements_max - mouvements_min) * 10
    return score


def get_successeurs_avec_coups(engine):
    """Retourne une liste de tuples (coup, instance_enfant) pour l'Alpha-Bêta."""
    successeurs = []
    occupied = engine.get_occupied()

    if engine.phase == 1:
        for position in range(9):
            mask = 1 << position
            if (occupied & mask) == 0:
                enfant = engine.copier()
                enfant.play_placement(position)
                enfant.tour = -1 if enfant.tour == 1 else 1
                successeurs.append(((position,), enfant))
        return successeurs

    bb_actuel = engine.bitboard_p1 if engine.tour == 1 else engine.bitboard_p2
    for src in range(9):
        if (bb_actuel & (1 << src)) != 0:
            destinations_possibles = engine.ADJACENCY_MASKS[src] & ~occupied
            for dst in range(9):
                if (destinations_possibles & (1 << dst)) != 0:
                    enfant = engine.copier()
                    enfant.play_mouvement(src, dst)
                    enfant.tour = -1 if enfant.tour == 1 else 1
                    successeurs.append(((src, dst), enfant))
    return successeurs


def alpha_beta(engine, profondeur, alpha, beta, joueur_max):
    """Algorithme Alpha-Bêta. Retourne (meilleur_score, meilleur_coup)."""
    joueur_max = _normalize_player(joueur_max)
    joueur_courant = _normalize_player(engine.tour)

    if engine.verifier_alignement(engine.bitboard_p1) or engine.verifier_alignement(engine.bitboard_p2):
        return evaluer_position(engine, joueur_max), None

    if profondeur == 0:
        return evaluer_position(engine, joueur_max), None

    successeurs = get_successeurs_avec_coups(engine)
    if not successeurs:
        return evaluer_position(engine, joueur_max), None

    successeurs.sort(
        key=lambda item: (
            100 if (len(item[0]) == 1 and item[0][0] == 4) or (len(item[0]) == 2 and item[0][1] == 4) else 0
        ),
        reverse=True,
    )

    meilleur_coup = None
    if joueur_courant == joueur_max:
        max_eval = -inf
        for coup, enfant in successeurs:
            evaluation, _ = alpha_beta(enfant, profondeur - 1, alpha, beta, joueur_max)
            if evaluation > max_eval:
                max_eval = evaluation
                meilleur_coup = coup
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break
        return max_eval, meilleur_coup

    min_eval = inf
    for coup, enfant in successeurs:
        evaluation, _ = alpha_beta(enfant, profondeur - 1, alpha, beta, joueur_max)
        if evaluation < min_eval:
            min_eval = evaluation
            meilleur_coup = coup
        beta = min(beta, evaluation)
        if beta <= alpha:
            break
    return min_eval, meilleur_coup


__all__ = ["alpha_beta", "evaluer_position", "get_successeurs_avec_coups"]