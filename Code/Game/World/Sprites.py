from Settings.Settings import *

class Sprite(pygame.sprite.Sprite):
    def __init__(self,pos,surf, *groups):
        super().__init__(*groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)
        self.ground = True
        
class ObjectSprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, *groups):
        super().__init__(*groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.sorting_offset_y = -10 

class InteractableZone(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, text=None, speed=2, sound=None, portrait=None,next_map=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.speed = speed
        self.sound = sound
        self.portrait = portrait
        self.next_map = next_map

class collissionSprite(pygame.sprite.Sprite):
    def __init__(self,pos,surf, *groups):
        super().__init__(*groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)
        
class collissionSprite(pygame.sprite.Sprite):
    def __init__(self,pos,surf, *groups):
        super().__init__(*groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)
        
class Follower(pygame.sprite.Sprite):
    def __init__(self, character, game_scene, *groups):
        super().__init__(*groups)
        self.char = character
        self.game_scene = game_scene
        # Cargar animación
        sheet = game_scene.resource_manager.get_spritesheet(self.char.sprite_key)
        if sheet:
            self.frames = {
                "down": sheet.get_row(0),
                "right": sheet.get_row(1), 
                "left": sheet.get_row(2),
                "up": sheet.get_row(3)
            }
            self.current_state = "down"
            self.frame_index = 0
            self.image = self.frames[self.current_state][0]
        else:
            # Placeholder
            self.image = pygame.Surface((25, 44))
            self.image.fill((200, 200, 200))
            self.frames = None
            self.current_state = "down"
            self.frame_index = 0

        # Posición inicial
        if hasattr(game_scene, 'player') and game_scene.player:
            start_pos = game_scene.player.rect.center
        else:
            start_pos = game_scene.world_manager.get_start_position()
        
        self.rect = self.image.get_rect(center=start_pos)
        self.pos = pygame.Vector2(self.rect.center)

    def follow_player_exact(self, player_data, dt):
        if not self.frames:
            return

        target = pygame.Vector2(player_data['position'])
        dir_hist = player_data['direction']

        if dir_hist.x != 0 or dir_hist.y != 0:
            speed = 200
            direction = (target - self.pos)
            distance = direction.length()
            if distance > 0:
                direction = direction.normalize()
                move = direction * speed * dt
                if move.length() > distance:
                    self.pos = target
                else:
                    self.pos += move

            self.rect.center = self.pos.xy

        # Animación
        self.current_state = player_data['state']
        raw = int(player_data['frame_index'])
        self.frame_index = raw % len(self.frames[self.current_state])
        self.image = self.frames[self.current_state][self.frame_index]
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def teleport_to(self, position):
        """Teletransporta el follower instantáneamente"""
        self.pos = pygame.Vector2(position)
        self.rect.center = (self.pos.x, self.pos.y)
        
        # Reset animación
        if self.frames:
            self.current_state = "down"
            self.frame_index = 0
            self.image = self.frames[self.current_state][0]

    def update(self, dt):
        """Método update estándar - no hacer nada aquí"""
        pass# Player.py - Versión mejorada con mejor tracking de estado