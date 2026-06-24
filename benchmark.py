# benchmark.py
"""Benchmark opposant l'IA alpha-bêta (profondeur 4) à l'IA moyenne (profondeur 2)
   sur le moteur FanoronteloEngine (règle des pions ayant tous bougé)."""

import json
import time
from pathlib import Path
from math import inf

from alphabeta import alpha_beta
from engine import FanoronteloEngine  # moteur standard du jeu

# Paramètres du benchmark
NUM_PARTIES = 100
DIFFICULTY_DEPTH = 4
MEDIUM_DEPTH = 2
MAX_TOURS_PAR_PARTIE = 100
RESULTS_FILE = Path(__file__).with_name("benchmark_results.json")


class BenchmarkIA:
    """Représente une IA avec un nom, une profondeur et un numéro de joueur."""
    def __init__(self, name: str, depth: int, joueur: int):
        self.name = name
        self.depth = depth
        self.joueur = joueur

    def choisir_coup(self, engine: FanoronteloEngine):
        """Appelle alpha_beta, applique le coup sur l'engine et retourne le coup + temps écoulé."""
        start = time.perf_counter()
        score, src, dst = alpha_beta(engine, self.depth, -inf, inf, self.joueur)
        elapsed = time.perf_counter() - start

        if src is None or dst is None:
            return None, elapsed

        # Appliquer le mouvement
        engine.valider_et_deplacer(src, dst)
        return (src, dst), elapsed


def jouer_partie(starting_player: str):
    """Joue une partie complète en utilisant FanoronteloEngine."""
    engine = FanoronteloEngine()
    ia_difficile = BenchmarkIA("difficile", DIFFICULTY_DEPTH, 1)  # joueur 1
    ia_moyenne = BenchmarkIA("moyenne", MEDIUM_DEPTH, 2)          # joueur 2

    # Choix du joueur qui commence
    if starting_player == "moyenne":
        engine.tour = 2
    else:
        engine.tour = 1

    temps_difficile = []
    temps_moyenne = []
    nb_tours = 0

    while nb_tours < MAX_TOURS_PAR_PARTIE:
        # Vérification des conditions de victoire (avec la règle "tous ont bougé")
        if engine.verifier_alignement_et_mouvement(engine.bitboard_p1, engine.moved_once_p1):
            return "difficile", temps_difficile, temps_moyenne
        if engine.verifier_alignement_et_mouvement(engine.bitboard_p2, engine.moved_once_p2):
            return "moyenne", temps_difficile, temps_moyenne

        # Déterminer l'IA qui joue
        joueur_actif = ia_difficile if engine.tour == 1 else ia_moyenne
        coup, elapsed = joueur_actif.choisir_coup(engine)
        if coup is None:
            break  # plus aucun mouvement légal

        if joueur_actif.name == "difficile":
            temps_difficile.append(elapsed)
        else:
            temps_moyenne.append(elapsed)

        # Passer au tour suivant
        engine.tour = 2 if engine.tour == 1 else 1
        nb_tours += 1

    # Après la boucle, déterminer le vainqueur final
    if engine.verifier_alignement_et_mouvement(engine.bitboard_p1, engine.moved_once_p1):
        return "difficile", temps_difficile, temps_moyenne
    elif engine.verifier_alignement_et_mouvement(engine.bitboard_p2, engine.moved_once_p2):
        return "moyenne", temps_difficile, temps_moyenne
    else:
        return "egalite", temps_difficile, temps_moyenne


def main():
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
        winner, diff_times, med_times = jouer_partie(starting_player)

        if winner == "difficile":
            results["victoires_difficile"] += 1
        elif winner == "moyenne":
            results["victoires_moyenne"] += 1
        else:
            results["egalites"] += 1

        difficult_times.extend(diff_times)
        medium_times.extend(med_times)

    # Calcul des moyennes
    if NUM_PARTIES > 0:
        results["taux_victoire_difficile"] = round(
            (results["victoires_difficile"] / NUM_PARTIES) * 100, 2
        )
    if difficult_times:
        results["temps_reponse_moyen_difficile"] = round(
            sum(difficult_times) / len(difficult_times), 6
        )
    if medium_times:
        results["temps_reponse_moyen_moyenne"] = round(
            sum(medium_times) / len(medium_times), 6
        )

    # Sauvegarde des résultats
    RESULTS_FILE.write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("\n--- Benchmark Terminé ---")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()