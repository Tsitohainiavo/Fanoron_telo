# buttons.py
"""Boutons réutilisables pour l'interface du jeu."""

import arcade

class UndoButton:
    def __init__(self, x, y, size=40):
        self.x = x
        self.y = y
        self.size = size
        self.hovered = False
        self.clicked = False

    def draw(self, enabled=True):
        if not enabled:
            bg_color = (60, 60, 70, 150)
            icon_color = (100, 100, 110, 150)
            border_color = (60, 60, 70, 150)
        elif self.clicked:
            bg_color = (70, 80, 100, 220)
            icon_color = (200, 200, 210)
            border_color = (150, 170, 200)
        elif self.hovered:
            bg_color = (60, 70, 90, 220)
            icon_color = (230, 230, 240)
            border_color = (180, 200, 230)
        else:
            bg_color = (40, 45, 60, 200)
            icon_color = (200, 200, 210)
            border_color = (80, 85, 100)

        arcade.draw_circle_filled(self.x, self.y, self.size//2, bg_color)
        arcade.draw_circle_outline(self.x, self.y, self.size//2, border_color, 2)

        arcade.draw_text("⤺", self.x, self.y - 4, icon_color, 18, anchor_x="center", anchor_y="center")
        arcade.draw_text("UNDO", self.x, self.y - self.size//2 - 12, icon_color, 10, anchor_x="center", bold=True)

    def on_mouse_motion(self, x, y):
        self.hovered = (x - self.x)**2 + (y - self.y)**2 <= (self.size//2)**2
        return self.hovered

    def on_mouse_press(self, x, y):
        if (x - self.x)**2 + (y - self.y)**2 <= (self.size//2)**2:
            self.clicked = True
            return True
        return False

    def on_mouse_release(self):
        self.clicked = False


class RedoButton:
    def __init__(self, x, y, size=40):
        self.x = x
        self.y = y
        self.size = size
        self.hovered = False
        self.clicked = False

    def draw(self, enabled=True):
        if not enabled:
            bg_color = (60, 60, 70, 150)
            icon_color = (100, 100, 110, 150)
            border_color = (60, 60, 70, 150)
        elif self.clicked:
            bg_color = (70, 80, 100, 220)
            icon_color = (200, 200, 210)
            border_color = (150, 170, 200)
        elif self.hovered:
            bg_color = (60, 70, 90, 220)
            icon_color = (230, 230, 240)
            border_color = (180, 200, 230)
        else:
            bg_color = (40, 45, 60, 200)
            icon_color = (200, 200, 210)
            border_color = (80, 85, 100)

        arcade.draw_circle_filled(self.x, self.y, self.size//2, bg_color)
        arcade.draw_circle_outline(self.x, self.y, self.size//2, border_color, 2)

        arcade.draw_text("⤻", self.x, self.y - 4, icon_color, 18, anchor_x="center", anchor_y="center")
        arcade.draw_text("REDO", self.x, self.y - self.size//2 - 12, icon_color, 10, anchor_x="center", bold=True)

    def on_mouse_motion(self, x, y):
        self.hovered = (x - self.x)**2 + (y - self.y)**2 <= (self.size//2)**2
        return self.hovered

    def on_mouse_press(self, x, y):
        if (x - self.x)**2 + (y - self.y)**2 <= (self.size//2)**2:
            self.clicked = True
            return True
        return False

    def on_mouse_release(self):
        self.clicked = False


class MenuButton:
    """Bouton 'MENU' pour retourner à l'accueil."""
    def __init__(self, x, y, size=40):
        self.x = x
        self.y = y
        self.size = size
        self.hovered = False
        self.clicked = False

    def draw(self, enabled=True):
        if not enabled:
            bg_color = (60, 60, 70, 150)
            icon_color = (100, 100, 110, 150)
            border_color = (60, 60, 70, 150)
        elif self.clicked:
            bg_color = (70, 80, 100, 220)
            icon_color = (200, 200, 210)
            border_color = (150, 170, 200)
        elif self.hovered:
            bg_color = (60, 70, 90, 220)
            icon_color = (230, 230, 240)
            border_color = (180, 200, 230)
        else:
            bg_color = (40, 45, 60, 200)
            icon_color = (200, 200, 210)
            border_color = (80, 85, 100)

        arcade.draw_circle_filled(self.x, self.y, self.size//2, bg_color)
        arcade.draw_circle_outline(self.x, self.y, self.size//2, border_color, 2)

        arcade.draw_text("⌂", self.x, self.y - 4, icon_color, 20, anchor_x="center", anchor_y="center")
        arcade.draw_text("MENU", self.x, self.y - self.size//2 - 12, icon_color, 10, anchor_x="center", bold=True)

    def on_mouse_motion(self, x, y):
        self.hovered = (x - self.x)**2 + (y - self.y)**2 <= (self.size//2)**2
        return self.hovered

    def on_mouse_press(self, x, y):
        if (x - self.x)**2 + (y - self.y)**2 <= (self.size//2)**2:
            self.clicked = True
            return True
        return False

    def on_mouse_release(self):
        self.clicked = False


class SkinMenuButton:
    """Bouton 'SKIN' pour ouvrir le menu de personnalisation."""
    def __init__(self, x, y, width=80, height=36):
        self.x = x
        self.y = y
        self.w = width
        self.h = height
        self.hovered = False
        self.clicked = False

    def _hit(self, x, y):
        return (abs(x - self.x) <= self.w // 2 and abs(y - self.y) <= self.h // 2)

    def draw(self, active=False):
        if active:
            bg, fg, border = (240, 210, 90, 230), (30, 30, 30), (255, 230, 120)
        elif self.clicked:
            bg, fg, border = (90, 110, 160, 230), (240, 240, 255), (160, 180, 220)
        elif self.hovered:
            bg, fg, border = (70, 90, 140, 220), (230, 235, 255), (150, 170, 210)
        else:
            bg, fg, border = (45, 52, 78, 210), (190, 200, 230), (80, 90, 130)

        left, right = self.x - self.w // 2, self.x + self.w // 2
        bottom, top = self.y - self.h // 2, self.y + self.h // 2

        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, bg)
        arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, border, 2)

        arcade.draw_circle_filled(self.x - 18, self.y + 2, 4, (224, 86,  86))
        arcade.draw_circle_filled(self.x - 8,  self.y + 2, 4, (218, 165, 32))
        arcade.draw_circle_filled(self.x + 2,  self.y + 2, 4, (70, 150, 235))

        arcade.draw_text("SKIN", self.x + 12, self.y, fg, 11, bold=True, anchor_x="center", anchor_y="center")

    def on_mouse_motion(self, x, y):
        self.hovered = self._hit(x, y)
        return self.hovered

    def on_mouse_press(self, x, y):
        if self._hit(x, y):
            self.clicked = True
            return True
        return False

    def on_mouse_release(self):
        self.clicked = False