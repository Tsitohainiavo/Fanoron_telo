# Fanoron-telo – Projet de Hackathon Algorithmique Avancée

## Section 1 : En-tête Institutionnel et Identification

- **Institut Supérieur Polytechnique de Madagascar**  
  [www.ispm-edu.com](http://www.ispm-edu.com)

- **Nom du groupe de projet** : `SixClown`

**Membres de l’équipe :**

| Nom Complet | Numéro d'étudiant | Classe | Rôle précis pour ce Hackathon |
| :--- | :---: | :---: | :--- |
| ANDRIAMPARANY Tsitohain'Ny Avo Fisandratana| 04 | ISAIA4 | Lead DevOps, Optimisation Bitboard, Backend |
| ANDRIAKOTO Rah-Yowan | 08 | IGGLIA4 | UI/UX Designer, Intégration graphique |
| ANDRIANARILALA Tsiory Fanantenana | 24 | IGGLIA4 | Backend Architect, Moteur de règles |
| RAHARIVOLOLONA Nomenjanahary Nathalie | 20 | ISAIA4 | Lead IA, Tests & Performances |
| ANDRIAMANJATO Nomenjanahary Henintsoa | 02 | IGGLIA4 | Rédacteur technique, Contrôle qualité |
| RAZAFIMAHEFA Sariaka | 01 | IGGLIA4 | Benchmarking, Tests fonctionnels |


## Section 2 : Description du Travail Réalisé

**Application développée :**  
Fanoron‑telo – un jeu de plateau traditionnel malgache, programmé en Python avec la bibliothèque Arcade, doté d’une intelligence artificielle paramétrable et d’une interface soignée.

### Fonctionnalités implémentées 

**Priorité 1 :**
- Mode **Humain vs Humain** local.
- Mode **Humain vs IA** avec trois niveaux : Facile, Moyen, Difficile.
- Gestion robuste de toutes les règles : déplacement sur cases adjacentes libres, détection d’alignement, obligation que chaque pion ait bougé au moins une fois.

**Priorité 2 :**
- Mode **IA vs IA (Démo)** automatique, avec ralentissement pour observer les coups.
- IA **Difficile** basée sur l’algorithme **Minimax avec élagage Alpha‑Beta**.
- Distribution exécutable autonome (via PyInstaller).

**Priorité 3 :**
- **Undo / Redo** : annulation et rétablissement des coups (piles d’historique bornées).
- **Personnalisation graphique** : 5 formes de pions (cercle, carré, losange, étoile, hexagone) et 5 palettes de couleurs.
- **Animations fluides** : vol parabolique des pions, effet de rebond, halo de destination, ligne gagnante.
- **Interface responsive** : redimensionnement libre de la fenêtre, centrage automatique des éléments.

### Architecture et pile technologique

- **Langage** : Python 3.11
- **Interface graphique** : [Arcade](https://api.arcade.academy/)
- **Moteur de jeu** : Représentation **bitboard** pour une manipulation ultra‑rapide des positions (9 bits par joueur)
- **IA** :
  - Niveau Facile/Moyen : sélection aléatoire parmi les successeurs légaux - module `moteur_ia.py`
  - Niveau Difficile : Minimax + Alpha‑Beta sur profondeur 6 - module `alphabeta.py`
- **Performance** : Mesure du temps de réflexion de l’IA (affiché en millisecondes dans le HUD)

**Lien vers la version hébergée :**  
*Non disponible pour le moment, en cours d'elaboration *

---

## Section 3 : Guide d'Installation Rapide (3 Commandes Max)

```bash
git clone https://github.com/Tsitohainiavo/Fanoron_telo.git
pip install -r requirements.txt
python accueil.py
```

## Section 4 : Outils d'Aide IA Utilisés

Tout au long du développement, notre équipe a utilisé **Claude et Gemini** comme assistant.Nous les avons utilisés pour nous aider à structurer, à optimiser notre code afin d'avoir des performances optimales. Pour nous documenter vis-à-vis de la bibliothèque arcade, nous avons utilisé claude. 

**Exemples d’utilisation concrète :**
- **Écriture d’algorithmes** : Optimisation de la structure Minimax avec élagage Alpha‑Beta.
- **Débogage** : identification rapide des erreurs liés à l'integration.
- **Génération de l’interface** : aide à la création des classes de boutons (Undo, Redo, Skin), optimisation de l’affichage du HUD.

**Retour d’expérience :**  
L’IA a permis de gagner environ **60 % du temps total**, principalement sur les parties algorithmiques et le débogage. Les suggestions devaient toujours être vérifiées car certaines ne respectaient pas les spécificités d’Arcade (ex. `draw_rectangle_filled` inexistant dans la version utilisée).

---

## Section 5 : Modélisation et Algorithmes de l'IA du Jeu

### Représentation de l'état du plateau

L’état du jeu est stocké dans deux **entiers 9 bits** (bitboards), un pour chaque joueur. Chaque bit correspond à une intersection du plateau 3×3, selon le schéma :

Chaque bit du bitboard correspond à une intersection spécifique du plateau $3 \times 3$ :

* **Bit 0** : NO (Nord-Ouest)
* **Bit 1** : N (Nord)
* **Bit 2** : NE (Nord-Est)
* **Bit 3** : O (Ouest)
* **Bit 4** : C (Centre)
* **Bit 5** : E (Est)
* **Bit 6** : SO (Sud-Ouest)
* **Bit 7** : S (Sud)
* **Bit 8** : SE (Sud-Est)

#### Matrice du plateau

| Colonne Ouest | Colonne Centrale | Colonne Est |
| :---: | :---: | :---: |
| **Bit 0** (NO) | **Bit 1** (N) | **Bit 2** (NE) |
| **Bit 3** (O)  | **Bit 4** (C) | **Bit 5** (E)  |
| **Bit 6** (SO) | **Bit 7** (S) | **Bit 8** (SE) |


Cette représentation permet :
- Vérification instantanée de l’occupation (`occupied = bb_p1 | bb_p2`).
- Calcul des destinations légales via un masque d’adjacence pré‑calculé (`ADJACENCY_MASKS`).
- Détection des alignements gagnants à l’aide de 8 masques (`WINNING_MASKS`).

Un troisième bitboard (`moved_once`) suit les pions ayant déjà été déplacés.

### Minimax et fonction d'évaluation

L’IA difficile utilise un **Minimax avec élagage Alpha‑Beta** sur une profondeur fixe de 6.

**Fonction d’évaluation statique** (simplifiée mais efficace) :
- Si le joueur max gagne : +∞
- Si le joueur min gagne : –∞
- Sinon, score basé sur la proximité d’un alignement : nombre de lignes où le joueur possède déjà 2 pions et où la 3ᵉ case est libre.

Cette heuristique guide l’IA vers des positions favorables sans explosion combinatoire.

### Techniques avancée

- **Bitboards** : Utilisés pour toutes les opérations de mouvement et de victoire.
---

## Section 6 : Analyses de Performances

### Temps de réponse de l’IA

Mesuré avec `time.perf_counter()` lors de chaque appel à l’IA, affiché en millisecondes dans l’interface.

| Niveau de l'IA | Profondeur de recherche | Temps de réponse moyen (ms) | Algorithme et Observation |
| :--- | :---: | :---: | :--- |
| **Facile** | — | < 1 ms | Heuristique simple ou choix quasi-immédiat |
| **Moyen** | — | < 1 ms | Évaluation basique à court terme |
| **Difficile** | 6 | 15 – 50 ms | Algorithme Alpha-Beta optimisé avec bitboard |


### Affrontements IA vs IA (Démo)

Nous avons lancé **20 parties automatiques** IA Difficile contre IA Facile.

- **Taux de victoire de l’IA Difficile** : 100 % (20/20)
- **Taux de victoire de l’IA Difficile contre IA Moyen** : 95 % (19/20, un match nul causé par un blocage mutuel)

Ces résultats confirment que l’IA Difficile exploite bien la profondeur 6 et la fonction d’évaluation pour dominer les niveaux inférieurs.

---

*Projet réalisé dans le cadre du Hackathon Algorithmique Avancée, ISPM – documents autorisés.*
