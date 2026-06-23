# Fanoron-Telo

Jeu de stratégie malgache traditionnel **Fanoron-Telo**, développé en Python avec la bibliothèque [Arcade](https://api.arcade.academy/) pour le rendu graphique, et un moteur de jeu basé sur des bitboards pour la logique et l'intelligence artificielle (algorithme Alpha-Bêta).

Projet universitaire réalisé dans le cadre du module d'algorithmique avancée, par l'équipe « six-clown ».

---

## Table des matières

- [Présentation](#présentation)
- [Aperçu de l'état actuel du projet](#aperçu-de-létat-actuel-du-projet)
- [Structure du dépôt](#structure-du-dépôt)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Lancement du jeu](#lancement-du-jeu)
- [Règles du jeu](#règles-du-jeu)
- [Commandes en jeu](#commandes-en-jeu)
- [Architecture technique](#architecture-technique)
- [Équipe du projet](#équipe-du-projet)
- [Pistes d'amélioration](#pistes-damélioration)

---

## Présentation

Le Fanoron-Telo se joue sur un plateau de **3×3 intersections** (9 cases) reliées par des lignes horizontales, verticales et diagonales. Chaque joueur dispose de **3 pions**. Le but est d'aligner ses 3 pions sur une ligne du plateau.

Dans cette implémentation :
- Le joueur 1 (**Rouge**) commence avec ses pions sur la rangée du haut (`NO`, `N`, `NE`).
- Le joueur 2 (**Bleu**, contrôlé par l'IA) commence avec ses pions sur la rangée du bas (`SO`, `S`, `SE`).
- Les joueurs déplacent à tour de rôle un pion vers une intersection adjacente libre.
- La partie est gagnée par le premier joueur dont les 3 pions sont alignés **et ont chacun bougé au moins une fois** depuis le début de la partie.

## Aperçu de l'état actuel du projet

Le dépôt contient à ce jour une implémentation fonctionnelle du jeu en mode **Humain (Rouge) vs IA (Bleu)**, avec rendu graphique 3D stylisé et animations. Pour que la documentation reste fidèle au code réellement présent dans le dépôt, voici l'état précis des fonctionnalités :

| Fonctionnalité | État dans `main` |
|---|---|
| Plateau 3×3 avec rendu graphique (Arcade) | Implémenté (`fanorontelo.py`) |
| Déplacement de pions avec validation d'adjacence | Implémenté |
| Détection de victoire (alignement + pions ayant bougé) | Implémenté |
| Mode Humain (Rouge) vs IA (Bleu) | Implémenté |
| IA Alpha-Bêta avec move ordering | Implémenté (`alphabeta.py`, profondeur fixée à 6) |
| Plusieurs niveaux de difficulté IA | Pas encore implémenté dans `fanorontelo.py` (profondeur fixe, équivalente à un niveau Difficile) |
| Phase de placement initiale des pions | Pas encore implémentée dans `fanorontelo.py` (placement de départ fixe) |
| Mode Humain vs Humain / IA vs IA | Pas encore implémenté |
| Détection d'égalité | Pas encore implémentée explicitement |
| Annulation de coup (Undo/Redo) | Pas encore implémenté |
| Module `plateau.py` (moteur alternatif avec phase de placement) | Présent dans le dépôt mais non utilisé par `fanorontelo.py` actuellement |

Cette section sera mise à jour à chaque évolution notable du code, afin que le README reflète l'état réel du dépôt plutôt que le seul cahier des charges théorique.

## Structure du dépôt

```
Fanoron_telo/
├── fanorontelo.py     # Point d'entrée : moteur de jeu (bitboards), rendu Arcade, boucle de jeu
├── alphabeta.py        # Module IA : évaluation heuristique + algorithme Alpha-Bêta
├── plateau.py          # Moteur alternatif avec phases Placement/Mouvement (non encore intégré)
├── .gitignore
└── README.md
```

## Prérequis

- **Python 3.10** ou version ultérieure
- **pip** (gestionnaire de paquets Python)
- La bibliothèque **[Arcade](https://pypi.org/project/arcade/)** pour le rendu graphique

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/Tsitohainiavo/Fanoron_telo.git
cd Fanoron_telo
```

### 2. Créer un environnement virtuel (recommandé)

```bash
python -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows
```

### 3. Installer les dépendances

```bash
pip install arcade
```

> Le dépôt ne contient pas encore de fichier `requirements.txt`. Il est recommandé d'en ajouter un avec le contenu suivant pour fiabiliser l'installation :
> ```
> arcade>=3.0
> ```

## Lancement du jeu

Depuis la racine du dépôt :

```bash
python fanorontelo.py
```

Une fenêtre de **1000×760** pixels s'ouvre avec le plateau 3D du Fanoron-Telo.

## Règles du jeu

1. Le joueur **Rouge** (humain) commence.
2. Cliquez sur un de vos pions pour le sélectionner (les destinations valides s'illuminent en vert).
3. Cliquez sur une intersection valide pour y déplacer le pion sélectionné.
4. L'IA (**Bleu**) joue automatiquement après votre coup.
5. La partie se termine dès qu'un joueur aligne ses 3 pions sur une ligne du plateau, à condition que chacun de ces pions ait déjà bougé au moins une fois.

## Commandes en jeu

| Touche / Action | Effet |
|---|---|
| Clic gauche sur un pion | Sélectionner le pion |
| Clic gauche sur une case en surbrillance | Déplacer le pion sélectionné |
| `R` | Recommencer la partie |
| `Échap` | Quitter le jeu |

## Architecture technique

- **`fanorontelo.py`**
  - `FanoronteloEngine` : représentation du plateau via deux bitboards (un par joueur, 9 bits), gestion du tour, validation des déplacements, détection d'alignement.
  - `FanoronteloView` : vue Arcade gérant le rendu 3D, les animations de déplacement (`FlyAnimation`), les entrées clavier/souris et l'appel à l'IA.
- **`alphabeta.py`**
  - `evaluer_position()` : fonction d'évaluation heuristique (victoire/défaite immédiate, contrôle du centre, mobilité, progression des pions ayant bougé).
  - `alpha_beta()` : recherche Alpha-Bêta récursive avec tri des coups (move ordering) priorisant la case centrale.
- **`plateau.py`**
  - Classe `FanoronTelo` : moteur alternatif modélisant explicitement les deux phases du jeu traditionnel (Phase 1 : placement des 3 pions, Phase 2 : déplacement). Non importé actuellement par `fanorontelo.py` — à intégrer ou à retirer selon la direction retenue par l'équipe.

## Équipe du projet

| Rôle | Responsabilité |
|---|---|
| Lead IA & Algorithmes | Minimax / Alpha-Bêta, niveaux de difficulté |
| Architecte Backend & logique de jeu | Modélisation du plateau, règles, cycle de vie de la partie |
| UI/UX Designer & Frontend | Interface graphique, états visuels, menus |
| Intégrateur Front-Back & Bonus | Connexion UI ↔ logique/IA, Undo/Redo, animations |
| Lead DevOps & Benchmarking | Build, déploiement, scripts de benchmark IA vs IA |
| Rédacteur technique & QA | Documentation, tests, rapport de bugs |

## Pistes d'amélioration

- Ajouter un `requirements.txt` et un script de packaging.
- Implémenter la phase de placement initiale (en s'appuyant sur `plateau.py` ou en l'intégrant à `fanorontelo.py`).
- Ajouter les modes Humain vs Humain et IA vs IA.
- Ajouter la sélection du niveau de difficulté (profondeur variable au lieu de la valeur fixe `profondeur=6`).
- Ajouter la détection explicite d'une situation d'égalité.
- Ajouter les fonctionnalités Undo/Redo.
- Mettre en place une suite de tests automatisés (voir le Plan de tests du projet).
