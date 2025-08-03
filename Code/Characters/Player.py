# Player.py - Versión mejorada con mejor tracking de estado

from Settings.Settings import *
from ResourceManager import ResourceManager

class Player(pygame.sprite.Sprite):
    def __init__(self, game_scene, pos, sprite_sheet_key, dialog_manager, interactuables, collision_sprites, groups):
        super().__init__(groups)
        # Carga la hoja de sprites
        resource_manager = ResourceManager.get_instance()
        self.sprite_sheet = resource_manager.get_spritesheet(sprite_sheet_key)
        self.load_frames()
        
        self._init_player_properties(pos)
        
        # instancias de otras clases
        self.dialog_manager = dialog_manager
        self.game_scene = game_scene
        
        # grupos de sprites
        self.collision_sprites = collision_sprites
        self.interactables = interactuables
        self.frame_index = 0
        
        # NUEVO: Variables para tracking mejorado
        self.last_pos = pygame.math.Vector2(pos)
        self.is_actually_moving = False
        self.movement_changed = False
        self.input_history = []  # Lista de estados de teclas
        self.input_frame_counter = 0
    def _init_player_properties(self, pos):
        self.state = "down"
        self.image = self.frames[self.state][0]
        self.direction = pygame.math.Vector2(0, 0)
        self.pos = pygame.math.Vector2(pos)
        self.hitbox_rect = pygame.Rect(self.pos.x, self.pos.y + 18, 15, 15)
        self.rect = self.image.get_rect(midbottom=self.hitbox_rect.midbottom)
        self.speed = 60
        self.sprite_speed = 3
        
    def load_frames(self):
        # TO DO: hacer esto mas dinamico
        self.frames = {
            "down": self.sprite_sheet.get_row(0),
            "right": self.sprite_sheet.get_row(1),
            "left": self.sprite_sheet.get_row(2),
            "up": self.sprite_sheet.get_row(3)
        }
        
    def get_interaction_rect(self):
        # 1) Offset a media baldosa
        half = TILE_SIZE // 2
        offset = pygame.math.Vector2()
        w, h = 0, 0
        if self.state == "up":    
            offset.y = -half 
            w, h = 2, 10
        elif self.state == "down":
            offset.y = +half
            w, h = 2, 10
        elif self.state == "left":
            offset.x = -half
            w, h = 10, 2
        elif self.state == "right":
            offset.x = +half
            w, h = 10, 2

        # 2) Punto de interacción
        interaction_pos = self.hitbox_rect.center + offset

        return pygame.Rect(
            interaction_pos.x - w//2,
            interaction_pos.y - h//2,
            w, h
        )
    def get_input_at_frame(self, target_frame):
        """Obtiene el estado de input en un frame específico"""
        for input_state in reversed(self.input_history):
            if input_state['frame'] <= target_frame:
                return input_state['keys']
        
        # Si no encontramos el frame exacto, devolver sin teclas presionadas
        return {'left': False, 'right': False, 'up': False, 'down': False}
    
    def input(self, events):
        """Captura input y lo guarda en el historial"""
        keys = pygame.key.get_pressed()
        
        # NUEVO: Guardar estado de teclas de movimiento
        input_state = {
            'frame': self.input_frame_counter,
            'keys': {
                'left': keys[pygame.K_LEFT],
                'right': keys[pygame.K_RIGHT],
                'up': keys[pygame.K_UP],
                'down': keys[pygame.K_DOWN]
            }
        }
        
        self.input_history.append(input_state)
        
        # Limitar historial (5 segundos a 60 FPS = 300 frames)
        if len(self.input_history) > 300:
            self.input_history.pop(0)
        
        self.input_frame_counter += 1
        
        # Procesar movimiento normalmente
        self.move_player(keys)

        # Resto del input (interacciones, etc.)
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    self.interaction_rect = self.get_interaction_rect()
                    for zone in self.interactables:
                        if zone.rect.colliderect(self.interaction_rect):
                            if hasattr(zone, "next_map") and zone.next_map:
                                self.game_scene.go_next_level(zone.next_map)
                            else:
                                print(f"Interacting with zone: {zone.text}")
                                self.dialog_manager.get_text(zone.text)
                            break
                
                elif event.key == pygame.K_x or event.key == pygame.K_RETURN and self.dialog_manager.active:
                    print("Skip dialogue")
                    self.skip_dialogue()
                    
    def move_player(self, keys):
        old_direction = self.direction.copy()
        
        self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
    
        if self.direction.length_squared() > 0:
            self.direction = self.direction.normalize()
            
        # NUEVO: Detectar cambio de dirección
        self.movement_changed = (old_direction - self.direction).length_squared() > 0.1
            
    def skip_dialogue(self):
        if self.dialog_manager.active and self.dialog_manager.current_index < len(self.dialog_manager.texts) - 1:
            self.dialog_manager.next_text()
        else:
            self.dialog_manager.active = False
            self.dialog_manager.texts.clear()
            self.dialog_manager.current_index = 0
            
    def move(self, dt):
        """Movimiento con actualización correcta de rectángulos"""
        # Guardar posición anterior
        self.last_pos = self.pos.copy()
        
        # Movimiento horizontal
        self.pos.x += self.direction.x * self.speed * dt
        self.hitbox_rect.centerx = round(self.pos.x)  # NUEVO: Redondear
        self.collision("horizontal")

        # Movimiento vertical
        self.pos.y += self.direction.y * self.speed * dt
        self.hitbox_rect.bottom = round(self.pos.y + 18)  # NUEVO: Redondear
        self.collision("vertical")

        # Actualiza la posición del rect del sprite con coordenadas enteras
        self.rect.midbottom = self.hitbox_rect.midbottom
        
        # Sincronizar pos con hitbox_rect para mantener consistencia
        self.pos.x = self.hitbox_rect.centerx
        self.pos.y = self.hitbox_rect.bottom - 18
        
        # Calcular si realmente se movió
        movement_distance = (self.pos - self.last_pos).length()
        self.is_actually_moving = movement_distance > 0.1

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == "horizontal":
                    if self.direction.x > 0:  # Moviendo a la derecha
                        self.hitbox_rect.right = sprite.rect.left
                    elif self.direction.x < 0:  # Moviendo a la izquierda
                        self.hitbox_rect.left = sprite.rect.right
                    self.pos.x = self.hitbox_rect.centerx
                elif direction == "vertical":
                    if self.direction.y > 0:  # Moviendo hacia abajo
                        self.hitbox_rect.bottom = sprite.rect.top
                    elif self.direction.y < 0:  # Moviendo hacia arriba
                        self.hitbox_rect.top = sprite.rect.bottom
                    self.pos.y = self.hitbox_rect.bottom - 18
    
    def animate(self, dt):
        # NUEVO: Usar is_actually_moving en lugar de direction.length_squared()
        moving = self.is_actually_moving and self.direction.length_squared() > 0
        
        if moving:
            if self.direction.x != 0:
                self.state = "right" if self.direction.x > 0 else "left"
            elif self.direction.y != 0:
                self.state = "down" if self.direction.y > 0 else "up"
            self.frame_index += self.sprite_speed * dt
            if self.frame_index >= len(self.frames[self.state]):
                self.frame_index = 0
        else:
            self.frame_index = 0
            
        self.image = self.frames[self.state][int(self.frame_index)]

    def update(self, dt):
        self.move(dt)
        self.animate(dt)