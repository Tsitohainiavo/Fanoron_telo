"""Constantes géométriques, couleurs, skins et palettes pour Fanoron-telo."""

from enum import Enum

# ---------- Dimensions ----------
SCREEN_WIDTH  = 1000
SCREEN_HEIGHT = 760
SCREEN_TITLE  = "Fanoron-telo"

# ---------- Couleurs de fond ----------
COLOR_BG_TOP    = (20,  24,  38)
COLOR_BG_BOTTOM = (10,  12,  20)

# ---------- Plateau ----------
COLOR_BOARD_TOP   = (92,  64,  38)
COLOR_BOARD_SIDE  = (52,  36,  22)
COLOR_BOARD_EDGE  = (140, 102, 58)
COLOR_LINE        = (224, 196, 140)
COLOR_LINE_SHADOW = (40,  28,  16)
COLOR_NODE_IDLE   = (224, 196, 140)
COLOR_NODE_HOVER  = (255, 224, 130)
COLOR_NODE_VALID  = (110, 220, 150)

# ---------- Skins ----------
class PieceSkin(Enum):
    CIRCLE  = "Cercle"
    SQUARE  = "Carré"
    DIAMOND = "Diamant"
    STAR    = "Étoile"
    HEXAGON = "Hexagone"

# ---------- Couleurs joueurs par défaut ----------
PLAYER_COLORS = {
    1: {"base": (224,  86,  86), "light": (255, 150, 130), "dark": (120, 30,  30),  "name": "Rouge"},
    2: {"base": ( 70, 150, 235), "light": (150, 210, 255), "dark": ( 20, 60, 120),  "name": "Bleu"},
}

# ---------- Palettes supplémentaires ----------
COLOR_PALETTES = {
    "Classique": {
        1: {"base": (224, 86, 86), "light": (255, 150, 130), "dark": (120, 30, 30)},
        2: {"base": (70, 150, 235), "light": (150, 210, 255), "dark": (20, 60, 120)},
    },
    "Or & Argent": {
        1: {"base": (218, 165, 32), "light": (255, 215, 0), "dark": (139, 105, 20)},
        2: {"base": (192, 192, 192), "light": (220, 220, 220), "dark": (128, 128, 128)},
    },
    "Vert & Violet": {
        1: {"base": (50, 205, 50), "light": (100, 255, 100), "dark": (0, 100, 0)},
        2: {"base": (138, 43, 226), "light": (180, 100, 255), "dark": (75, 0, 130)},
    },
    "Rose & Cyan": {
        1: {"base": (255, 105, 180), "light": (255, 150, 210), "dark": (200, 50, 120)},
        2: {"base": (0, 255, 255), "light": (100, 255, 255), "dark": (0, 150, 150)},
    },
    "Orange & Noir": {
        1: {"base": (255, 140, 0), "light": (255, 180, 50), "dark": (200, 100, 0)},
        2: {"base": (50, 50, 50), "light": (80, 80, 80), "dark": (20, 20, 20)},
    },
}

# ---------- Tailles ----------
PIECE_RADIUS = 28
NODE_RADIUS  = 16
HOVER_RADIUS = 24

FLY_DURATION = 1
FLY_HEIGHT   = 90

# ---------- Géométrie bitboard ----------
NODE_IDS = ["NO", "N", "NE", "O", "C", "E", "SO", "S", "SE"]
NODE_TO_BIT = {name: idx for idx, name in enumerate(NODE_IDS)}

RAW_POSITIONS = {
    "NO": (-1.0,  1.0), "N":  ( 0.0,  1.0), "NE": ( 1.0,  1.0),
    "O":  (-1.0,  0.0), "C":  ( 0.0,  0.0), "E":  ( 1.0,  0.0),
    "SO": (-1.0, -1.0), "S":  ( 0.0, -1.0), "SE": ( 1.0, -1.0),
}

EDGES = [
    ("NO","N"),  ("N","NE"), ("SO","S"),  ("S","SE"),
    ("NO","O"),  ("O","SO"), ("NE","E"),  ("E","SE"),
    ("N","C"),   ("C","S"),  ("O","C"),   ("C","E"),
    ("NO","C"),  ("C","SE"), ("NE","C"),  ("C","SO"),
]

WINNING_LINES = [
    ("NO","N","NE"), ("SO","S","SE"), ("NO","O","SO"), ("NE","E","SE"),
    ("N","C","S"),  ("O","C","E"),  ("NO","C","SE"), ("NE","C","SO"),
]

# Masques d'adjacence
ADJACENCY_MASKS = {i: 0 for i in range(9)}
for _a, _b in EDGES:
    bit_a = NODE_TO_BIT[_a]
    bit_b = NODE_TO_BIT[_b]
    ADJACENCY_MASKS[bit_a] |= (1 << bit_b)
    ADJACENCY_MASKS[bit_b] |= (1 << bit_a)

# Masques de victoire
WINNING_MASKS = []
for line in WINNING_LINES:
    mask = 0
    for node in line:
        mask |= (1 << NODE_TO_BIT[node])
    WINNING_MASKS.append(mask)

# Positions initiales
INITIAL_P1_BITBOARD = 7       # NO, N, NE
INITIAL_P2_BITBOARD = 448     # SO, S, SE