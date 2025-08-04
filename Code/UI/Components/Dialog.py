from Settings.Settings import *
import ast
class DialogBox:
    def __init__(self, text, font, width, screen_height, sound=None, min_height=64, padding=4, speed=3, portrait=None):
        self.text = text
        self.font = font
        self.width = width
        self.min_height = min_height
        self.padding = padding
        self.screen_height = screen_height
        self.sound = sound
        self.portrait = portrait  

        self.canvas_width = 50
        self.canvas_height = 56

        self.box_rect = pygame.Rect(0, screen_height - min_height - 10, width, min_height)
        self.bg_color = (0, 0, 0)
        self.border_color = (255, 255, 255)
        self.text_color = (255, 255, 255)

        self.char_index = 0
        self.speed = speed
        self.timer = 0
        self.finished = False
        self.displayed_text = ""

    def update(self):
        if not self.finished:
            self.timer += 1
            if self.timer >= self.speed and self.char_index < len(self.text):
                self.displayed_text += self.text[self.char_index]
                if self.sound and self.text[self.char_index] not in [' ', '.', ',']:
                    self.sound.play()
                self.char_index += 1
                self.timer = 0
            if self.char_index >= len(self.text):
                self.finished = True

    def draw(self, surface):
    # 1) Offset y fondo inicial (este fondo se va a redibujar más abajo con la altura correcta)
        x_text_offset = self.padding
        if self.portrait:
            x_text_offset += self.canvas_width + self.padding

        # 2) Prepara las palabras, partiendo las muy largas
        max_text_width = self.width - x_text_offset - self.padding
        raw_words = self.displayed_text.split(" ")
        words = []
        for w in raw_words:
            if self.font.size(w)[0] > max_text_width:
                words += self.split_long_word(w, max_text_width)
            else:
                words.append(w)

        # 3) Wrap en líneas
        lines = []
        current = ""
        for w in words:
            test = current + w + " "
            if self.font.size(test)[0] <= max_text_width:
                current = test
            else:
                lines.append(current)
                current = w + " "
        lines.append(current)

        # 4) Ajusta altura del box segun líneas
        line_h = self.font.get_height()
        needed_h = len(lines) * line_h + self.padding * 2
        self.box_rect.height = max(self.min_height, needed_h)

        # 5) Dibuja fondo y borde YA con la altura correcta
        pygame.draw.rect(surface, self.bg_color, self.box_rect)
        pygame.draw.rect(surface, self.border_color, self.box_rect, 2)

        # 6) Si hay retrato, dibujalo
        if self.portrait:
            portrait_rect = pygame.Rect(
                self.box_rect.left + self.padding,
                self.box_rect.top + self.padding,
                self.canvas_width,
                self.canvas_height
            )
            surf_scaled = pygame.transform.scale(self.portrait, (self.canvas_width, self.canvas_height))
            surface.blit(surf_scaled, portrait_rect)
        else:
            portrait_rect = pygame.Rect(
                self.box_rect.left + self.padding,
                self.box_rect.top  + self.padding,
                self.canvas_width,
                self.canvas_height
            )
            asterisco_surf = self.font.render("*", True, self.text_color)
            # centramos el "*" dentro del rect
            ax = portrait_rect.centerx - asterisco_surf.get_width() // 2
            ay = portrait_rect.centery - asterisco_surf.get_height() // 2
            surface.blit(asterisco_surf, (ax, ay))
        # 7) Finalmente, pinta cada línea
        for i, line in enumerate(lines):
            y = self.box_rect.top + self.padding + i * line_h
            surface.blit(self.font.render(line, True, self.text_color),
                        (self.box_rect.left + x_text_offset, y))


    def is_finished(self):
        return self.finished
    def split_long_word(self, word, max_w):
        parts, p = [], ""
        for ch in word:
            if self.font.size(p + ch)[0] <= max_w:
                p += ch
            else:
                parts.append(p)
                p = ch
        if p: parts.append(p)
        return parts

        # luego, en lugar de iterar directamente words:

        
class DialogManager:
    def __init__(self, font, width, screen_height, sound="default", portrait=None):
        self.active = False
        self.texts = []
        self.current_index = 0
        self.dialog_box = None
        self.font = font
        self.width = width
        self.screen_height = screen_height
        self.sound = sound
        self.portrait = portrait

    def get_text(self, texts):
        # Asumimos que texts es un diccionario y el texto está en el primer valor como string lista
        text_list = ast.literal_eval(texts)
        self.texts = text_list
        self.current_index = 0
        self.active = True
        self.dialog_box = DialogBox(self.texts[self.current_index], self.font, self.width, self.screen_height, self.sound, portrait=self.portrait)

    def next_text(self):
        if not self.active:
            return
        self.current_index += 1
        if self.current_index < len(self.texts):
            self.dialog_box = DialogBox(self.texts[self.current_index], self.font, self.width, self.screen_height, self.sound, portrait=self.portrait)
        else:
            self.close()

    def update(self):
        if self.active and self.dialog_box:
            self.dialog_box.update()
            if self.dialog_box.is_finished():
                # Podes decidir si automáticamente pasa al siguiente texto o esperar input
                pass

    def draw(self, surface):
        if self.active and self.dialog_box:
            self.dialog_box.draw(surface)

    def close(self):
        self.active = False
        self.texts = []
        self.current_index = 0
        self.dialog_box = None
