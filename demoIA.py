# Module pour les démonstrations IA vs IA en mode batch (statistiques)

def jouer_partie_ia(level1, level2, afficher=True):
    """
    Joue une partie entre deux IA de niveaux donnés.
    Retourne (gagnant, coups) où gagnant est 1 ou 2, ou 0 pour nul.
    """
    from fanorontelo import FanoronteloEngine
    import ia_utils

    engine = FanoronteloEngine()
    engine.reset()
    coups = 0

    while True:
        player = engine.tour
        level = level1 if player == 1 else level2
        src, dst = ia_utils.get_ai_move(engine, level, player)
        if src is None or dst is None:
            return 0, coups

        success = engine.valider_et_deplacer(src, dst)
        if not success:
            return 0, coups

        coups += 1
        bb_joueur = engine.bitboard_p1 if player == 1 else engine.bitboard_p2
        moved_joueur = engine.moved_once_p1 if player == 1 else engine.moved_once_p2
        if engine.verifier_alignement_et_mouvement(bb_joueur, moved_joueur):
            return player, coups

        engine.tour = 2 if player == 1 else 1
        if coups > 100:
            return 0, coups