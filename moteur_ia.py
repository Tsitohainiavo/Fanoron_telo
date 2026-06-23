
import random

NODE_IDS = ["NO", "N", "NE", "O", "C", "E", "SO", "S", "SE"]

def evaluer_plateau(engine):
    """
    Attribue un score à l'état actuel du plateau du point de vue du Joueur 1 (Rouge).
    """
    if engine.verifier_alignement_et_mouvement(engine.bitboard_p1, engine.moved_once_p1):
        return 1000
    if engine.verifier_alignement_et_mouvement(engine.bitboard_p2, engine.moved_once_p2):
        return -1000

    score = 0
    # Contrôle du centre (bit index 4 = 'C')
    if (engine.bitboard_p1 & (1 << 4)): 
        score += 15
    if (engine.bitboard_p2 & (1 << 4)): 
        score -= 15

    # Mobilité (Nombre de mouvements légaux disponibles)
    copie_p1 = engine.copier()
    copie_p1.tour = 1
    score += len(copie_p1.get_successeurs()) * 2

    copie_p2 = engine.copier()
    copie_p2.tour = 2
    score -= len(copie_p2.get_successeurs()) * 2

    return score

def minimax(engine, profondeur, maximisant):
    """
    Explore l'arbre des possibilités et retourne (meilleur_score, meilleur_état_enfant)
    """
    if profondeur == 0 or \
       engine.verifier_alignement_et_mouvement(engine.bitboard_p1, engine.moved_once_p1) or \
       engine.verifier_alignement_et_mouvement(engine.bitboard_p2, engine.moved_once_p2):
        return evaluer_plateau(engine), None

    successeurs = engine.get_successeurs()
    if not successeurs:
        return 0, None

    meilleur_enfant = None

    if maximisant:
        valeur_max = -float('inf')
        for enfant in successeurs:
            # CORRECTION : On extrait le score, l'élément suivant est un objet Engine, pas une action textuelle
            score, _ = minimax(enfant, profondeur - 1, False)
            if score > valeur_max:
                valeur_max = score
                meilleur_enfant = enfant
        return valeur_max, meilleur_enfant
    else:
        valeur_min = float('inf')
        for enfant in successeurs:
            # CORRECTION : Même chose ici
            score, _ = minimax(enfant, profondeur - 1, True)
            if score < valeur_min:
                valeur_min = score
                meilleur_enfant = enfant
        return valeur_min, meilleur_enfant

def obtenir_coup_ia(engine, niveau="moyen"):
    """
    Sélecteur de stratégie. Retourne un objet FanoronteloEngine.
    """
    successeurs = engine.get_successeurs()
    if not successeurs:
        return None

    if niveau == "facile":
        return random.choice(successeurs)

    elif niveau == "moyen":
        maximisant = (engine.tour == 1)
        _, meilleur_enfant = minimax(engine, profondeur=3, maximisant=maximisant)
        
        if meilleur_enfant is None:
            meilleur_enfant = random.choice(successeurs)
        return meilleur_enfant
