from Settings.Settings import *
import math

class AllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.offset = pygame.Vector2()
        # NUEVO: Variables para suavizado de cámara
        self.camera_smooth = False  # Cambiar a True para suavizado
        self.smooth_factor = 0.1    # Factor de suavizado (0.1 = muy suave, 1.0 = sin suavizado)
        self.target_offset = pygame.Vector2()

    def draw(self, surface, target_position):
        """Renderiza todos los sprites con offset de cámara sin temblequeo"""
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        
        # Calcular offset objetivo (con redondeo para evitar sub-píxeles)
        target_x = round(-(target_position[0] - screen_width/2))
        target_y = round(-(target_position[1] - screen_height/2))
        self.target_offset.x = target_x
        self.target_offset.y = target_y
        
        if self.camera_smooth:
            # Interpolación suave de cámara (opcional)
            self.offset.x += (self.target_offset.x - self.offset.x) * self.smooth_factor
            self.offset.y += (self.target_offset.y - self.offset.y) * self.smooth_factor
            # Redondear después de la interpolación
            final_offset = (round(self.offset.x), round(self.offset.y))
        else:
            # Sin suavizado - usar directamente los valores redondeados
            self.offset = self.target_offset.copy()
            final_offset = (int(self.offset.x), int(self.offset.y))

        # Separar capas manteniendo el orden de renderizado
        ground_sprites = [s for s in self if hasattr(s, "ground")]
        object_sprites = [s for s in self if not hasattr(s, "ground")]

        # Renderizar cada capa con posiciones enteras
        for layer in (ground_sprites, object_sprites):
            for sprite in sorted(layer, key=lambda s: s.rect.centery + getattr(s, "sorting_offset_y", 0)):
                # CLAVE: Asegurar que las posiciones finales sean enteros
                render_pos = (
                    round(sprite.rect.topleft[0] + final_offset[0]),
                    round(sprite.rect.topleft[1] + final_offset[1])
                )
                surface.blit(sprite.image, render_pos)

    def set_camera_smooth(self, enabled: bool, smooth_factor: float = 0.1):
        """Configura el suavizado de cámara"""
        self.camera_smooth = enabled
        self.smooth_factor = smooth_factor
        if not enabled:
            # Si se desactiva el suavizado, sincronizar offsets
            self.offset = self.target_offset.copy()

    def get_camera_offset(self):
        """Obtiene el offset actual de la cámara (útil para debug)"""
        return (int(self.offset.x), int(self.offset.y))