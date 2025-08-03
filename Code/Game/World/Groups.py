from Settings.Settings import *

class AllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.offset = pygame.Vector2()

    def draw(self, surface, target_position):
        # calcula offset de cámara - CORREGIDO: usar dimensiones de la superficie
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        
        self.offset.x = -(target_position[0] - screen_width/2)
        self.offset.y = -(target_position[1] - screen_height/2)

        # separa capas si lo necesitas
        ground_sprites = [s for s in self if hasattr(s, "ground")]
        object_sprites = [s for s in self if not hasattr(s, "ground")]

        for layer in (ground_sprites, object_sprites):
            for sprite in sorted(layer, key=lambda s: s.rect.centery + getattr(s, "sorting_offset_y", 0)):
                surface.blit(sprite.image, sprite.rect.topleft + self.offset)