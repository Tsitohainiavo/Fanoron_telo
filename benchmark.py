
import json
import time
from pathlib import Path
from math import inf

from alphabeta import alpha_beta
from plateau import Plateau

# Configuration du benchmark
NUM_PARTIES = 100
DIFFICULTY_DEPTH = 4
MEDIUM_DEPTH = 2
MAX_TOURS_PAR_PARTIE = 100  # Sécurité vitale pour éviter les boucles infinies en phase 2
RESULTS_FILE = Path(__file__).with_name("benchmark_results.json")


class BenchmarkIA:
    """Classe représentant une IA lors du benchmark."""
    def __init__(self, name: str, depth: int, joueur: int):
        self.name = name
        self.depth = depth
        self.joueur = joueur

    def choisir_coup(self, plateau: Plateau):
        """Sélectionne et joue le meilleur coup selon l'algorithme Alpha-Bêta."""
        start = time.perf_counter()
        
        # Utilisation de -inf et inf pour une approche mathématique plus standard
        _, coup = alpha_beta(plateau, self.depth, -inf, inf, self.joueur)
        
        elapsed = time.perf_counter() - start

        # Si l'IA n'a plus de coups possibles (bloquée)
        if coup is None:
            return None, elapsed

        # Architecture explicite pour l'application du coup selon la phase
        if len(coup) == 1:
            plateau.play_placement(coup[0])
        elif len(coup) == 2:
            plateau.play_mouvement(coup[0], coup[1])
        else:
            # Sécurité de repli si une autre logique est attendue
            plateau.jouer_coup(*coup)

        # ATTENTION : Si tes méthodes play_placement/play_mouvement ne changent pas 
        # le tour automatiquement, décommente la ligne ci-dessous :
        # plateau.tour = -1 if plateau.tour == 1 else 1

        return coup, elapsed


def jouer_partie(starting_player: str):
    """Joue une partie complète entre l'IA difficile et moyenne."""
    plateau = Plateau()
    ia_difficile = BenchmarkIA("difficile", DIFFICULTY_DEPTH, plateau.JOUEUR_1)
    ia_moyenne = BenchmarkIA("moyenne", MEDIUM_DEPTH, plateau.JOUEUR_2)

    if starting_player == "moyenne":
        plateau.tour = plateau.JOUEUR_2
    else:
        plateau.tour = plateau.JOUEUR_1

    temps_difficile = []
    temps_moyenne = []
    compteur_tours = 0

    while compteur_tours < MAX_TOURS_PAR_PARTIE:
        # Vérification préalable du statut
        statut = plateau.determiner_statut()
        if statut != "EN_COURS":
            break

        # Détermination de l'IA qui doit jouer
        joueur_actif = ia_difficile if plateau.tour == ia_difficile.joueur else ia_moyenne
        
        # Exécution du coup
        coup, elapsed = joueur_actif.choisir_coup(plateau)
        
        # Si aucun coup n'est possible, la partie s'arrête
        if coup is None:
            break 

        # Enregistrement des métriques
        if joueur_actif.name == "difficile":
            temps_difficile.append(elapsed)
        else:
            temps_moyenne.append(elapsed)

        compteur_tours += 1

    # Détermination du vainqueur final
    if plateau.verifier_alignement(plateau.bitboard_p1):
        return "difficile", temps_difficile, temps_moyenne
    elif plateau.verifier_alignement(plateau.bitboard_p2):
        return "moyenne", temps_difficile, temps_moyenne
    
    # Si max tours atteint ou aucun alignement
    return "egalite", temps_difficile, temps_moyenne


def main():
    """Point d'entrée principal du script de benchmark."""
    results = {
        "total_parties": NUM_PARTIES,
        "victoires_difficile": 0,
        "victoires_moyenne": 0,
        "egalites": 0,
        "taux_victoire_difficile": 0.0,
        "temps_reponse_moyen_difficile": 0.0,
        "temps_reponse_moyen_moyenne": 0.0,
    }

    difficult_times = []
    medium_times = []

    print(f"Lancement de {NUM_PARTIES} parties de benchmark. Veuillez patienter...")

    for idx in range(NUM_PARTIES):
        starting_player = "difficile" if idx % 2 == 0 else "moyenne"
        winner, diff_times, medium_times_partie = jouer_partie(starting_player)
        
        if winner == "difficile":
            results["victoires_difficile"] += 1
        elif winner == "moyenne":
            results["victoires_moyenne"] += 1
        else:
            results["egalites"] += 1

        difficult_times.extend(diff_times)
        medium_times.extend(medium_times_partie)

    # Calcul final des statistiques de performance
    if NUM_PARTIES > 0:
        results["taux_victoire_difficile"] = round((results["victoires_difficile"] / NUM_PARTIES) * 100, 2)

    if difficult_times:
        results["temps_reponse_moyen_difficile"] = round(sum(difficult_times) / len(difficult_times), 6)
    if medium_times:
        results["temps_reponse_moyen_moyenne"] = round(sum(medium_times) / len(medium_times), 6)

    # Sauvegarde des résultats au format JSON
    RESULTS_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print("\n--- Benchmark Terminé ---")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
