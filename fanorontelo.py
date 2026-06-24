# fanorontelo.py
"""Lanceur du jeu Fanoron-telo (factorisé)."""

import arcade
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, COLOR_BG_TOP, COLOR_BG_BOTTOM, PLAYER_COLORS
from game_view import FanoronteloView

def main():
    window = arcade.Window(
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        SCREEN_TITLE,
        resizable=True,
        antialiasing=True
    )
    window.set_minimum_size(600, 500)
    view = FanoronteloView()
    window.show_view(view)
    arcade.run()

if __name__ == "__main__":
    main()