from Settings.Settings import *
from Game.World.Sprites import Sprite
from pytmx.util_pygame import load_pygame, pytmx
from Game.World.Sprites import collissionSprite, Sprite, ObjectSprite, InteractableZone
class Map():
    def __init__(self,map_path, tile_size=TILE_SIZE,interactuable_sprites=None, allsprites_group=None, collision_group=None):

        self.allsprites_group = allsprites_group
        self.collision_group = collision_group
        self.map_path = map_path
        self.tile_size = tile_size
        self.interactable_group = interactuable_sprites 
        print(f"[DEBUG] Cargando mapa desde: {self.map_path} con tamaño de tile: {self.tile_size}")
        self.load_map()
    
    def load_map(self):
        self.tmx_data = load_pygame(self.map_path)
        
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, surf in layer.tiles():
                    pos = (x * self.tile_size, y * self.tile_size)

                    if layer.name == "Ground":
                        Sprite(pos, surf, self.allsprites_group)
                    
                    elif layer.name == "Decorations":
                        Sprite(pos, surf, self.allsprites_group) 
                    elif layer.name == "Background":
                        Sprite(pos, surf, self.allsprites_group)
                    elif layer.name == "Others":
                        Sprite(pos, surf, self.allsprites_group)
            
            elif isinstance(layer, pytmx.TiledObjectGroup):
                if layer.name == "NPCS":
                    for obj in layer:
                        print("NPC:", obj.name, obj.x, obj.y)
                        if obj.name == "Start_point":
                            self.set_start_point(obj.x, obj.y)
                elif layer.name == "Collisions":
                    for obj in layer:
                        pos = (obj.x, obj.y)
                        surf = pygame.Surface((obj.width, obj.height))
                        collissionSprite(pos, surf, self.collision_group)
                        
                elif layer.name == "Objetos":
                    for obj in layer:
                        ObjectSprite((obj.x, obj.y),obj.image, self.allsprites_group)
                        
                elif layer.name == "Interactuable":
                    for obj in layer:
                        print("Interactuable:", obj.name, obj.x, obj.y)
                        if obj.name == "Dialog":
                            new_sprite = InteractableZone(obj.x, obj.y, obj.width, obj.height, 
                                                        text=obj.properties.get("Text", ""),
                                                        speed=obj.properties.get("speed", 2),
                                                        sound=obj.properties.get("sound", "default"),
                                                        portrait=obj.properties.get("img", None)
                                                        )
                            self.interactable_group.add(new_sprite)
                        elif obj.name == "Next_level":
                            print(f"[DEBUG] Interactable zone for next map: {obj.properties.get('next', '')}")
                            zone = InteractableZone(obj.x, obj.y, obj.width, obj.height,
                                    next_map=obj.properties.get("next", ""))
                            
                            self.interactable_group.add(zone)

    def set_start_point(self, x, y):
        self.start_point = (x, y)

    def return_start_point(self):
        return self.start_point if hasattr(self, 'start_point') else (0, 0)
    
class FadeTransition:
    def __init__(self, size, speed=550):
        self.surf = pygame.Surface(size)
        self.surf.fill((0,0,0))
        self.alpha = 0
        self.active = False
        self.speed = speed
        self.phase = 0     # 0=fade-out, 1=fade-in, 2=done
        self.callback = None

    def start(self, callback=None):
        self.active  = True    
        self.alpha = 0
        self.phase = 0
        self.callback = callback

    def update(self, dt):
        if not self.active:
            return
        if self.phase == 0:
            self.alpha += self.speed * dt
            if self.alpha >= 255:
                self.alpha = 255
                if self.callback: self.callback()
                self.phase = 1
        elif self.phase == 1:
            self.alpha -= self.speed * dt
            if self.alpha <= 0:
                self.alpha = 0
                self.phase = 2
                self.active = False
        self.surf.set_alpha(int(self.alpha))

    def draw(self, surface):
        if not self.active:
            return
        if self.phase in (0,1) and self.alpha > 0:
            surface.blit(self.surf, (0,0))
