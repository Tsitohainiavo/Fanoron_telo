import math
import moteur_ia
import alphabeta

def get_ai_move(engine, level, player):
    """
    Retourne (src_idx, dst_idx) pour le joueur 'player' (1 ou 2) selon le niveau.
    Retourne (None, None) si aucun mouvement trouvé.
    """
    if engine.tour != player:
        return None, None

    if level == "facile" or level == "moyen":
        prochain_etat = moteur_ia.obtenir_coup_ia(engine, niveau=level)
        if prochain_etat is None:
            return None, None
        bb_actuel = engine.bitboard_p1 if player == 1 else engine.bitboard_p2
        bb_nouveau = prochain_etat.bitboard_p1 if player == 1 else prochain_etat.bitboard_p2
        bit_perdu = bb_actuel & ~bb_nouveau
        bit_gagne = bb_nouveau & ~bb_actuel
        if bit_perdu and bit_gagne:
            src_idx = int(math.log2(bit_perdu))
            dst_idx = int(math.log2(bit_gagne))
            return src_idx, dst_idx
        return None, None

    elif level == "difficile":
        _, src_idx, dst_idx = alphabeta.alpha_beta(
            engine, profondeur=6,
            alpha=-float('inf'), beta=float('inf'),
            joueur_max=player
        )
        return src_idx, dst_idx

    return None, None