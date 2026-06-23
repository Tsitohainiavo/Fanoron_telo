import json
import time
from pathlib import Path

from alphabeta import alpha_beta
from plateau import Plateau


NUM_PARTIES = 100
DIFFICULTY_DEPTH = 4
MEDIUM_DEPTH = 2
RESULTS_FILE = Path(__file__).with_name("benchmark_results.json")


class BenchmarkIA:
    def __init__(self, name, depth, joueur):
        self.name = name
        self.depth = depth
        self.joueur = joueur

    def choisir_coup(self, plateau):
        start = time.perf_counter()
        _, coup = alpha_beta(plateau, self.depth, -10**9, 10**9, self.joueur)
        elapsed = time.perf_counter() - start
        if coup is None:
            return None, elapsed
        plateau.jouer_coup(*coup)
        return coup, elapsed


def jouer_partie(starting_player):
    plateau = Plateau()
    ia_difficile = BenchmarkIA("difficile", DIFFICULTY_DEPTH, plateau.JOUEUR_1)
    ia_moyenne = BenchmarkIA("moyenne", MEDIUM_DEPTH, plateau.JOUEUR_2)

    if starting_player == "moyenne":
        plateau.tour = plateau.JOUEUR_2

    temps_difficile = []
    temps_moyenne = []

    while True:
        statut = plateau.determiner_statut()
        if statut != "EN_COURS":
            break

        if plateau.tour == ia_difficile.joueur:
            _, elapsed = ia_difficile.choisir_coup(plateau)
            temps_difficile.append(elapsed)
        else:
            _, elapsed = ia_moyenne.choisir_coup(plateau)
            temps_moyenne.append(elapsed)

    if plateau.verifier_alignement(plateau.bitboard_p1):
        return "difficile", temps_difficile, temps_moyenne
    if plateau.verifier_alignement(plateau.bitboard_p2):
        return "moyenne", temps_difficile, temps_moyenne
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

    if NUM_PARTIES:
        results["taux_victoire_difficile"] = round(results["victoires_difficile"] / NUM_PARTIES * 100, 2)

    if difficult_times:
        results["temps_reponse_moyen_difficile"] = round(sum(difficult_times) / len(difficult_times), 6)
    if medium_times:
        results["temps_reponse_moyen_moyenne"] = round(sum(medium_times) / len(medium_times), 6)

    RESULTS_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
