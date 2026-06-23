class FanoronTelo:
    # Constantes d'identification
    JOUEUR_1 = 1   # Représenté par le bitboard P1
    JOUEUR_2 = -1  # Représenté par le bitboard P2
    
    # Masques binaires des 8 lignes alignées gagnantes (9 bits)
    WINNING_MASKS = [
        0x007,  # Ligne 1 (Haut)   : cases 0, 1, 2 (000000111)
        0x038,  # Ligne 2 (Milieu) : cases 3, 4, 5 (000111000)
        0x1C0,  # Ligne 3 (Bas)    : cases 6, 7, 8 (111000000)
        0x124,  # Col 1   (Gauche) : cases 0, 3, 6 (100100100)
        0x092,  # Col 2   (Milieu) : cases 1, 4, 7 (010010010)
        0x049,  # Col 3   (Droite) : cases 2, 5, 8 (001001001)
        0x111,  # Diagonale Principale : 0, 4, 8    (100010001)
        0x054   # Diagonale Secondaire : 2, 4, 6    (001010100)
    ]
    
    # Graphe d'adjacence du Fanoron-telo (Masques de mouvements autorisés)
    ADJACENCY_MASKS = {
        0: 0x01A,  # Lié à 1, 3, 4      (000011010)
        1: 0x01D,  # Lié à 0, 2, 4      (000011101)
        2: 0x032,  # Lié à 1, 4, 5      (000110010)
        3: 0x093,  # Lié à 0, 4, 6      (010010011)
        4: 0x1FF,  # Le centre est lié à absolument tout le monde
        5: 0x1C4,  # Lié à 2, 4, 8      (111000100)
        6: 0x098,  # Lié à 3, 4, 7      (010011000)
        7: 0x158,  # Lié à 6, 4, 8      (101011000)
        8: 0x0D0   # Lié à 5, 4, 7      (011010000)
    }

    def __init__(self):
        self.bitboard_p1 = 0  # Position des 3 pions du Joueur 1
        self.bitboard_p2 = 0  # Position des 3 pions du Joueur 2
        self.tour = self.JOUEUR_1
        self.phase = 1        # Phase 1: Placement, Phase 2: Mouvement
        self.pions_places_p1 = 0
        self.pions_places_p2 = 0

    def get_occupied(self):
        """Retourne le bitboard global des cases occupées."""
        return self.bitboard_p1 | self.bitboard_p2

    def verifier_alignement(self, bitboard_joueur):
        """Vérification instantanée en O(1) grâce au ET binaire."""
        for masque in self.WINNING_MASKS:
            if (bitboard_joueur & masque) == masque:
                return True
        return False

    def play_placement(self, position):
        """Phase 1 : Poser un pion (0 à 8)."""
        mask = 1 << position
        if (self.get_occupied() & mask) != 0:
            return False  # Case occupée
            
        if self.tour == self.JOUEUR_1:
            self.bitboard_p1 |= mask
            self.pions_places_p1 += 1
        else:
            self.bitboard_p2 |= mask
            self.pions_places_p2 += 1
            
        # Vérification du passage automatique en phase 2
        if self.pions_places_p1 == 3 and self.pions_places_p2 == 3:
            self.phase = 2
            
        return True

    def play_mouvement(self, depart, arrivee):
        """Phase 2 : Déplacer un pion d'une case à une autre adjacente libre."""
        mask_dep = 1 << depart
        mask_arr = 1 << arrivee
        
        # 1. Vérifier que la case de départ appartient bien au joueur
        bb_actuel = self.bitboard_p1 if self.tour == self.JOUEUR_1 else self.bitboard_p2
        if (bb_actuel & mask_dep) == 0:
            return False
            
        # 2. Vérifier que la case d'arrivée est libre
        if (self.get_occupied() & mask_arr) != 0:
            return False
            
        # 3. Vérifier que le mouvement suit les lignes autorisées (Adjacence)
        if (self.ADJACENCY_MASKS[depart] & mask_arr) == 0:
            return False
            
        # Appliquer le mouvement
        if self.tour == self.JOUEUR_1:
            self.bitboard_p1 &= ~mask_dep  # On retire le pion de 'depart'
            self.bitboard_p1 |= mask_arr   # On le place sur 'arrivee'
        else:
            self.bitboard_p2 &= ~mask_dep
            self.bitboard_p2 |= mask_arr
            
        return True

    def jouer_coup(self, *args):
        """
        Point d'entrée universel pour le contrôleur ou l'IA.
        Phase 1: args = (position,)
        Phase 2: args = (depart, arrivee)
        """
        succes = False
        if self.phase == 1 and len(args) == 1:
            succes = self.play_placement(args[0])
        elif self.phase == 2 and len(args) == 2:
            succes = self.play_mouvement(args[0], args[1])
            
        if succes:
            # On change de tour uniquement si le coup a été validé
            self.tour = self.JOUEUR_2 if self.tour == self.JOUEUR_1 else self.JOUEUR_1
            return True
        return False

    def determiner_statut(self):
        """Retourne l'état de la partie (En cours, Gagné P1, Gagné P2)."""
        if self.verifier_alignement(self.bitboard_p1):
            return "GAGNE_P1"
        if self.verifier_alignement(self.bitboard_p2):
            return "GAGNE_P2"
        return "EN_COURS"

    def copier(self):
        """Génère une copie rapide pour l'arbre de recherche de l'IA."""
        copie = FanoronTelo()
        copie.bitboard_p1 = self.bitboard_p1
        copie.bitboard_p2 = self.bitboard_p2
        copie.tour = self.tour
        copie.phase = self.phase
        copie.pions_places_p1 = self.pions_places_p1
        copie.pions_places_p2 = self.pions_places_p2
        return copie


class Plateau(FanoronTelo):
    """Alias de compatibilité pour les scripts de benchmark."""
    pass


__all__ = ["FanoronTelo", "Plateau"]