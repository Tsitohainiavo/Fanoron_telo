# Fanoron-telo – Projet de Hackathon Algorithmique Avancée

## Section 1 : En-tête Institutionnel et Identification

- **Institut Supérieur Polytechnique de Madagascar**  
  [www.ispm-edu.com](http://www.ispm-edu.com)

- **Nom du groupe de projet** : `SixClown`

**Membres de l’équipe :**

| Nom Complet       | Numéro d'étudiant | Classe | Rôle précis pour ce Hackathon          |
|-------------------|-------------------|--------|----------------------------------------|
| ANDRIAMPARANY     | 03                | ISAIA4 | Lead AI, Optimisation Bitboard         |
|  Tsitohain'Ny Avo |                   |        |                                        |
|-----------------------------------------------------------------------------------------|
| ANDRIAKOTO        | 08                | IGGLIA4| UI/UX Designer, Intégration graphique  |
| Rah-Yowan         |                   |        |                                        |
|-----------------------------------------------------------------------------------------|
| ANDRIANARILALA    | 24                | IGGLIA4| Backend Architect, Moteur de règles    |
| Tsiory Fanantenana|                   |        |                                        |
|-----------------------------------------------------------------------------------------|
| RAHARIVOLOLONA    | 20                | ISAIA4 | Lead DevOps, Tests & Performances      |
|Nomenjanahary      |                   |        |                                        |
|Nathalie           |                   |        |                                        |
|-----------------------------------------------------------------------------------------|
|ANDRIAMANJATO      | 02                | IGGLIA4|                                        |
|Henintsoa          |                   |        |                                        |
|-----------------------------------------------------------------------------------------|
|RAZAFIMAHEFA       | 01                | IGGLIA4|                                        |
|Sariaka            |                   |        |                                        |
|-----------------------------------------------------------------------------------------|


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
  - Niveau Difficile : Minimax + Alpha‑Beta sur profondeur 6 → module `alphabeta.py`
- **Performance** : Mesure du temps de réflexion de l’IA (affiché en millisecondes dans le HUD)

**Lien vers la version hébergée :**  
*Non disponible pour le moment – l’exécutable peut être généré avec PyInstaller et mis en ligne sur itch.io.*

---

## Section 3 : Guide d'Installation Rapide (3 Commandes Max)

```bash
git clone https://github.com/Tsitohainiavo/Fanoron_telo.git
pip install arcade
python accueil.py