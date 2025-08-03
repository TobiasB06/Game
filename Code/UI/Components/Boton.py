from Settings.Settings import *

class Button:
    def __init__(self, text, pos,FONT, bg_color, text_color, padding=10, action=None, outline=True):
        self.text = text
        self.font = FONT
        self.bg_color = bg_color
        self.text_color = text_color
        self.action = action
        self.padding = padding
        self.outline = outline 

        self.text_surf = self.font.render(self.text, True, self.text_color)
        self.rect = self.text_surf.get_rect(center=pos)
        self.rect.inflate_ip(padding * 2, padding * 2)  
    def draw(self, screen):
        if self.outline:
            pygame.draw.rect(screen, "white", self.rect.inflate(4, 4))  # Dibuja el borde
        pygame.draw.rect(screen, self.bg_color, self.rect)
        screen.blit(self.text_surf, (
            self.rect.x + self.padding,
            self.rect.y + self.padding
        ))

    def update(self):
        pass

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # clic izquierdo
            if self.rect.collidepoint(event.pos):
                if self.action:
                    self.action()
                    print("Button clicked:", self.text)

    def is_hovered(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

