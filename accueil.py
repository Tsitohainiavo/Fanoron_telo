import arcade
import math
from fanorontelo import FanoronteloView, COLOR_BG_TOP, COLOR_BG_BOTTOM, PLAYER_COLORS

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 760
SCREEN_TITLE = "Fanorontelo Telo 3D - Menu Principal"

class Button:
    def __init__(self, x, y, width, height, text, value, group=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.value = value
        self.group = group  # 'mode' ou 'diff'
        self.is_hovered = False
        self.is_selected = False

    def draw(self):
        # Couleur du fond selon l'état du bouton
        if self.is_selected:
            bg_color = (40, 60, 110, 240)
            border_color = (255, 215, 110)
            text_color = (255, 215, 110)
            border_thick = 3
        elif self.is_hovered:
            bg_color = (30, 36, 56, 220)
            border_color = (150, 210, 255)
            text_color = (255, 255, 255)
            border_thick = 2
        else:
            bg_color = (18, 22, 36, 200)
            border_color = (80, 90, 120)
            text_color = (170, 170, 185)
            border_thick = 1

        # Calcul des coordonnées Gauche, Droite, Bas, Haut à partir du centre (x, y)
        left = self.x - self.width / 2
        right = self.x + self.width / 2
        bottom = self.y - self.height / 2
        top = self.y + self.height / 2

        # Dessin du rectangle avec les fonctions lrbt compatibles
        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, bg_color)
        arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, border_color, border_thick)
        
        # Affichage du texte
        arcade.draw_text(self.text, self.x, self.y, text_color, 15, anchor_x="center", anchor_y="center", bold=self.is_selected)
        
    def check_hover(self, x, y):
        self.is_hovered = (self.x - self.width/2 <= x <= self.x + self.width/2 and
                            self.y - self.height/2 <= y <= self.y + self.height/2)

class AccueilView(arcade.View):
    def __init__(self):
        super().__init__()
        self.buttons = []
        self.time_elapsed = 0.0
        self.setup_menu()

    def setup_menu(self):
        cx = SCREEN_WIDTH / 2
        
        # Boutons de Mode de jeu
        self.buttons.append(Button(cx, 440, 380, 50, "Humain vs Humain (Local)", "HvH", "mode"))
        self.buttons.append(Button(cx, 370, 380, 50, "Humain vs Intelligence Artificielle", "HvIA", "mode"))
        
        # Boutons de Difficulté (Actifs si Mode = HvIA)
        self.buttons.append(Button(cx - 130, 250, 110, 46, "Facile", "facile", "diff"))
        self.buttons.append(Button(cx,       250, 110, 46, "Moyen", "moyen", "diff"))
        self.buttons.append(Button(cx + 130, 250, 110, 46, "Difficile", "difficile", "diff"))

        # Bouton Lancer la partie
        self.btn_play = Button(cx, 120, 260, 56, "LANCER LE JEU", "play", None)
        
        # Sélection par défaut
        self.buttons[0].is_selected = True  # HvH coché
        self.buttons[3].is_selected = True  # Facile coché

    def on_show_view(self):
        arcade.set_background_color((15, 17, 26))

    def on_update(self, delta_time):
        self.time_elapsed += delta_time

    def on_draw(self):
        self.clear()
        
        # Fond dégradé identique à l'arène 3D
        h = self.window.height
        steps = 40
        for i in range(steps):
            t = i / steps
            color = tuple(int(COLOR_BG_BOTTOM[c] + (COLOR_BG_TOP[c] - COLOR_BG_BOTTOM[c]) * t) for c in range(3))
            arcade.draw_lrbt_rectangle_filled(0, self.window.width, h * t, h * (t + 1/steps), color)

        # Titre Stylisé
        pulse = 0.5 + 0.5 * math.sin(self.time_elapsed * 3)
        title_color = (240, int(210 + 20 * pulse), 150)
        arcade.draw_text("FANORONTELO TELO 3D", SCREEN_WIDTH/2, 600, title_color, 34, anchor_x="center", bold=True)
        arcade.draw_text("Projet Algorithmique Avancée - ISPM", SCREEN_WIDTH/2, 550, (120, 130, 160), 13, anchor_x="center", italic=True)

        # Titres de sections
        arcade.draw_text("SÉLECTIONNEZ LE MODE DE JEU", SCREEN_WIDTH/2, 500, (200, 200, 220), 14, anchor_x="center", bold=True)
        
        # Vérifier si le mode IA est sélectionné pour griser ou afficher la difficulté
        is_ia = any(b.value == "HvIA" and b.is_selected for b in self.buttons)
        if is_ia:
            arcade.draw_text("NIVEAU DE L'INTELLIGENCE ARTIFICIELLE", SCREEN_WIDTH/2, 310, (200, 200, 220), 14, anchor_x="center", bold=True)

        # Dessiner les boutons
        for btn in self.buttons:
            if btn.group == "diff" and not is_ia:
                continue # Ne pas afficher si Humain vs Humain
            btn.draw()
            
        self.btn_play.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        for btn in self.buttons:
            btn.check_hover(x, y)
        self.btn_play.check_hover(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        # Clic sur les boutons de configuration
        is_ia = any(b.value == "HvIA" and b.is_selected for b in self.buttons)
        
        for btn in self.buttons:
            if btn.group == "diff" and not is_ia:
                continue
            if btn.is_hovered:
                # Désélectionner les autres boutons du même groupe
                for other in self.buttons:
                    if other.group == btn.group:
                        other.is_selected = False
                btn.is_selected = True

        # Clic sur LANCER LE JEU
        if self.btn_play.is_hovered:
            selected_mode = next(b.value for b in self.buttons if b.group == "mode" and b.is_selected)
            selected_diff = next(b.value for b in self.buttons if b.group == "diff" and b.is_selected)
            
            # Transitionner vers la vue principale du jeu avec les paramètres choisis
            game_view = FanoronteloView()
            game_view.configure_game(mode=selected_mode, diff=selected_diff)
            self.window.show_view(game_view)

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    accueil = AccueilView()
    window.show_view(accueil)
    arcade.run()

if __name__ == "__main__":
    main()