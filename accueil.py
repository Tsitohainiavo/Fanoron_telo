# accueil.py
"""Écran d'accueil du jeu Fanoron-telo."""

import arcade
import math
from fanorontelo import FanoronteloView, COLOR_BG_TOP, COLOR_BG_BOTTOM, PLAYER_COLORS

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 760
SCREEN_TITLE = "Fanoron-telo - Menu Principal"
DESIGN_HEIGHT = 760
MENU_MID_Y = 310


class Button:
    def __init__(self, x, y, width, height, text, value, group=None, style="normal"):
        self.x = x
        self.base_y = y
        self.width = width
        self.height = height
        self.text = text
        self.value = value
        self.group = group
        self.style = style          # "normal" ou "highlight"
        self.is_hovered = False
        self.is_selected = False

    def draw(self, offset_y=0):
        current_y = self.base_y + offset_y

        # Couleurs de base selon le style
        if self.style == "highlight":
            # Doré similaire au titre, mais statique
            bg_color = (240, 210, 140)      # fond doré chaud
            border_color = (240, 210, 140)      # bordure plus claire
            text_color = (30, 25, 10)           # texte très sombre
            border_thick = 2
        else:
            bg_color = (18, 22, 36, 200)
            border_color = (80, 90, 120)
            text_color = (170, 170, 185)
            border_thick = 1

        # États interactifs
        if self.is_selected:
            bg_color = (40, 60, 110, 240)
            border_color = (255, 215, 110)
            text_color = (255, 215, 110)
            border_thick = 3
        elif self.is_hovered:
            if self.style == "highlight":
                bg_color = (220, 190, 80, 240)   # un peu plus clair au survol
                text_color = (0, 0, 0)
                border_color = (255, 230, 160)
            else:
                bg_color = (30, 36, 56, 220)
                border_color = (150, 210, 255)
                text_color = (255, 255, 255)
            border_thick = 2

        left = self.x - self.width / 2
        right = self.x + self.width / 2
        bottom = current_y - self.height / 2
        top = current_y + self.height / 2

        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, bg_color)
        arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, border_color, border_thick)
        arcade.draw_text(
            self.text, self.x, current_y,
            text_color, 15,
            anchor_x="center", anchor_y="center",
            bold=True   # toujours en gras pour ce bouton distinctif
        )

    def check_hover(self, x, y, offset_y=0):
        current_y = self.base_y + offset_y
        self.is_hovered = (
            self.x - self.width / 2 <= x <= self.x + self.width / 2 and
            current_y - self.height / 2 <= y <= current_y + self.height / 2
        )


class AccueilView(arcade.View):
    def __init__(self):
        super().__init__()
        self.buttons = []
        self.time_elapsed = 0.0
        self.offset_y = 0.0
        self.setup_menu()

    def setup_menu(self):
        cx = SCREEN_WIDTH / 2

        self.btn_mode_hvh = Button(cx, 440, 380, 50, "Humain vs Humain (Local)", "HvH", "mode")
        self.btn_mode_hvia = Button(cx, 370, 380, 50, "Humain vs Intelligence Artificielle", "HvIA", "mode")

        self.btn_diff_facile = Button(cx - 130, 250, 110, 46, "Facile", "facile", "diff")
        self.btn_diff_moyen = Button(cx,       250, 110, 46, "Moyen", "moyen", "diff")
        self.btn_diff_difficile = Button(cx + 130, 250, 110, 46, "Difficile", "difficile", "diff")

        self.btn_play = Button(cx, 150, 260, 56, "LANCER LE JEU", "play", None)
        self.btn_demo = Button(cx, 80, 260, 56, "Demo : IA vs IA", "demo", None, style="highlight")

        self.buttons = [
            self.btn_mode_hvh,
            self.btn_mode_hvia,
            self.btn_diff_facile,
            self.btn_diff_moyen,
            self.btn_diff_difficile,
            self.btn_play,
            self.btn_demo
        ]

        self.btn_mode_hvh.is_selected = True
        self.btn_diff_facile.is_selected = True

    def on_show_view(self):
        arcade.set_background_color((15, 17, 26))
        self.on_resize(self.window.width, self.window.height)

    def on_resize(self, width, height):
        super().on_resize(width, height)
        new_cx = width / 2
        for btn in self.buttons:
            btn.x = new_cx
        self.btn_diff_facile.x = new_cx - 130
        self.btn_diff_moyen.x = new_cx
        self.btn_diff_difficile.x = new_cx + 130

        self.offset_y = (height / 2) - MENU_MID_Y

    def on_update(self, delta_time):
        self.time_elapsed += delta_time

    def on_draw(self):
        self.clear()

        h = self.window.height
        w = self.window.width
        steps = 40
        for i in range(steps):
            t = i / steps
            color = tuple(int(COLOR_BG_BOTTOM[c] + (COLOR_BG_TOP[c] - COLOR_BG_BOTTOM[c]) * t) for c in range(3))
            arcade.draw_lrbt_rectangle_filled(0, w, h * t, h * (t + 1/steps), color)

        pulse = 0.5 + 0.5 * math.sin(self.time_elapsed * 3)
        title_color = (240, int(210 + 20 * pulse), 150)
        title_y = 600 + self.offset_y
        arcade.draw_text("FANORON-TELO", w/2, title_y, title_color, 34, anchor_x="center", bold=True)
        subtitle_y = 550 + self.offset_y
        arcade.draw_text("Projet Algorithmique Avancée - ISPM", w/2, subtitle_y, (120, 130, 160), 13, anchor_x="center", italic=True)

        mode_title_y = 500 + self.offset_y
        arcade.draw_text("SÉLECTIONNEZ LE MODE DE JEU", w/2, mode_title_y, (200, 200, 220), 14, anchor_x="center", bold=True)

        is_ia = any(b.value == "HvIA" and b.is_selected for b in self.buttons if b.group == "mode")
        if is_ia:
            diff_title_y = 310 + self.offset_y
            arcade.draw_text("NIVEAU DE L'INTELLIGENCE ARTIFICIELLE", w/2, diff_title_y, (200, 200, 220), 14, anchor_x="center", bold=True)

        for btn in self.buttons:
            if btn.group == "diff" and not is_ia:
                continue
            btn.draw(offset_y=self.offset_y)

    def on_mouse_motion(self, x, y, dx, dy):
        is_ia = any(b.value == "HvIA" and b.is_selected for b in self.buttons if b.group == "mode")
        for btn in self.buttons:
            if btn.group == "diff" and not is_ia:
                btn.is_hovered = False
                continue
            btn.check_hover(x, y, offset_y=self.offset_y)

    def on_mouse_press(self, x, y, button, modifiers):
        is_ia = any(b.value == "HvIA" and b.is_selected for b in self.buttons if b.group == "mode")

        for btn in self.buttons:
            if btn.group == "diff" and not is_ia:
                continue
            if btn.is_hovered:
                for other in self.buttons:
                    if other.group == btn.group:
                        other.is_selected = False
                btn.is_selected = True
                if btn.group == "mode" and btn.value == "HvH":
                    self.btn_diff_facile.is_selected = True
                    self.btn_diff_moyen.is_selected = False
                    self.btn_diff_difficile.is_selected = False
                break

        if self.btn_play.is_hovered:
            selected_mode = next(b.value for b in self.buttons if b.group == "mode" and b.is_selected)
            selected_diff = next(b.value for b in self.buttons if b.group == "diff" and b.is_selected)
            game_view = FanoronteloView()
            game_view.configure_game(mode=selected_mode, diff=selected_diff)
            self.window.show_view(game_view)

        if self.btn_demo.is_hovered:
            # Lance le match AlphaBeta vs Moyen
            game_view = FanoronteloView()
            game_view.configure_demo_ab_vs_moyen()
            self.window.show_view(game_view)


def main():
    window = arcade.Window(
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        SCREEN_TITLE,
        resizable=True,
        antialiasing=True
    )
    window.set_minimum_size(600, 500)
    accueil = AccueilView()
    window.show_view(accueil)
    arcade.run()


if __name__ == "__main__":
    main()