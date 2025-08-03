import pygame
from UI.Components.Boton import Button
from Settings.Settings import *

class Menu:
    def __init__(self, surface, font, entries):
        self.surface        = surface
        self.font           = font
        self.entries        = entries
        self.buttons        = []
        self.selected_index = 0
        self._build_buttons()

    def _build_buttons(self):
        self.buttons.clear()
        gap = 100
        for i, (text, action) in enumerate(self.entries):
            pos = (40, 100 + i*gap)
            btn = Button(text, pos, self.font,
                         bg_color="black", text_color="white",
                         action=action)
            self.buttons.append(btn)

    def update(self):
        for i, btn in enumerate(self.buttons):
            btn.outline = (i == self.selected_index)
            btn.update()

    def handle_key_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_DOWN:
            self.selected_index = (self.selected_index + 1) % len(self.buttons)
        elif event.key == pygame.K_UP:
            self.selected_index = (self.selected_index - 1) % len(self.buttons)
        elif event.key == pygame.K_RETURN:
            self.buttons[self.selected_index].action()

    def draw(self):
        for btn in self.buttons:
            btn.draw(self.surface)