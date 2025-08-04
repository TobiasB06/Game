import pygame
from typing import List, Optional
from enum import Enum
import logging
from pathlib import Path

from ResourceManager import ResourceManager
from Characters.Player import Player
from Characters.Inventory import Character, Item
from Characters.Party import Party
from UI.UI_Inventory import UI_Inventory
from UI.Components.Dialog import DialogManager
from Game.World.Map import Map, FadeTransition
from Game.World.Groups import AllSprites
from DebugMenu import DebugMenu

logger = logging.getLogger(__name__)

class GameState(Enum):
    PLAYING = "playing"
    PAUSED = "paused"
    INVENTORY_OPEN = "inventory_open"
    DIALOG_ACTIVE = "dialog_active"
    TRANSITIONING = "transitioning"
    DEBUG_MENU = "debug_menu"

class GameStateManager:
    """Gestiona los estados del juego"""
    
    def __init__(self):
        self.current_state = GameState.PLAYING
        self.state_stack = []
        self.state_changed = False
    
    def push_state(self, new_state: GameState):
        """Añade un nuevo estado encima del actual"""
        self.state_stack.append(self.current_state)
        self.current_state = new_state
        self.state_changed = True
        logger.debug(f"State pushed: {new_state}")
    
    def pop_state(self):
        """Vuelve al estado anterior"""
        if self.state_stack:
            self.current_state = self.state_stack.pop()
            self.state_changed = True
            logger.debug(f"State popped: {self.current_state}")
    
    def set_state(self, new_state: GameState):
        """Cambia directamente al estado especificado"""
        self.current_state = new_state
        self.state_changed = True
        logger.debug(f"State set: {new_state}")
    
    def is_state(self, state: GameState) -> bool:
        """Verifica si el estado actual es el especificado"""
        return self.current_state == state
    
    def can_move_player(self) -> bool:
        """Determina si el jugador puede moverse en el estado actual"""
        blocked_states = {
            GameState.INVENTORY_OPEN, 
            GameState.DIALOG_ACTIVE, 
            GameState.DEBUG_MENU,
            GameState.PAUSED
        }
        return self.current_state not in blocked_states

class RenderSystem:
    """Sistema de renderizado separado mejorado sin temblequeo"""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.camera_offset = pygame.Vector2(0, 0)
    
    def calculate_camera_offset(self, target_pos: tuple):
        """Calcula el offset de la cámara con redondeo para evitar sub-píxeles"""
        # CLAVE: Redondear inmediatamente para evitar coordenadas fraccionarias
        self.camera_offset.x = round(-(target_pos[0] - self.screen_width // 2))
        self.camera_offset.y = round(-(target_pos[1] - self.screen_height // 2))
    
    def render_world(self, surface: pygame.Surface, all_sprites, player_pos: tuple):
        """Renderiza el mundo del juego sin temblequeo"""
        surface.fill((50, 50, 50))
        
        # Asegurar que player_pos tenga coordenadas enteras para la cámara
        rounded_player_pos = (round(player_pos[0]), round(player_pos[1]))
        
        # El AllSprites.draw ya maneja el redondeo internamente
        all_sprites.draw(surface, rounded_player_pos)
    
    def render_debug_visuals(self, surface: pygame.Surface, debug_menu, 
                           collision_sprites, interactable_sprites, player_rect):
        """Renderiza elementos de debug visual con posiciones enteras"""
        if not debug_menu.visible:
            return
        
        # Obtener offset de cámara redondeado del AllSprites
        if hasattr(debug_menu.game_scene.world_manager, 'all_sprites'):
            camera_offset = debug_menu.game_scene.world_manager.all_sprites.get_camera_offset()
        else:
            self.calculate_camera_offset(player_rect.center)
            camera_offset = (int(self.camera_offset.x), int(self.camera_offset.y))
        
        # Hitboxes de colision
        if debug_menu.show_hitboxes:
            for sprite in collision_sprites:
                screen_rect = sprite.rect.move(camera_offset)
                pygame.draw.rect(surface, (255, 0, 0), screen_rect, 1)
        
        # Zonas de interaccion
        if debug_menu.show_interaction_zones:
            for zone in interactable_sprites:
                screen_rect = zone.rect.move(camera_offset)
                pygame.draw.rect(surface, (0, 255, 0), screen_rect, 1)
        
        # Rect de interaccion del jugador
        if hasattr(debug_menu.game_scene, 'player'):
            interaction_rect = debug_menu.game_scene.player.get_interaction_rect()
            screen_rect = interaction_rect.move(camera_offset)
            pygame.draw.rect(surface, (255, 255, 0), screen_rect, 1)

class PartyManager:
    """Gestiona el sistema de partys"""
    
    def __init__(self):
        self.characters: List[Character] = []
        self.party = Party()
        self._setup_main_character()
    
    def _setup_main_character(self):
        """Configura el personaje principal (Ely)"""
        ely = Character(attack=4,defense=7,max_hp=100,will=4)
        ely.sprite_key = "Ely"
        
        # Pre-cargar sprite preview de Ely
        resource_manager = ResourceManager.get_instance()
        sprite_sheet = resource_manager.get_spritesheet("Ely")
        if sprite_sheet:
            ely.sprite_preview = sprite_sheet.get_frame(0, 0)
            ely.sprite_preview_sz = (sprite_sheet.frame_width, sprite_sheet.frame_height)
        else:
            # Placeholder
            ely.sprite_preview = pygame.Surface((25, 44))
            ely.sprite_preview.fill((100, 150, 255))
            ely.sprite_preview_sz = (25, 44)
        
        # Equipamiento inicial
        from Characters.ItemManager import item_manager
        sword = item_manager.get_item(1)  # Espada maestra
        if sword:
            ely.inventory.add(sword)
            ely.equipment.equip(sword)
        
        self.characters.append(ely)
        self.party.add(ely)
        logger.info("Main character (Ely) created and added to party")
    
    def add_member(self, member_name: str) -> bool:
        """Añade un miembro al grupo"""
        member_configs = {
            "koral": {
                "sprite_key": "Koral",
                "items": [5, 6], 
                "color": (100, 150, 255),
                "stats": [6,4,130,2]
            },
            "vel": {
                "sprite_key": "Vel", 
                "items": [7, 8], 
                "color": (255, 100, 150),
                "stats": [2,5,90,6]
            }
        }
        
        config = member_configs.get(member_name.lower())
        if not config:
            logger.warning(f"Unknown party member: {member_name}")
            return False
        
        # Verificar si ya esta en el grupo
        for char in self.characters:
            if getattr(char, 'sprite_key', '') == config['sprite_key']:
                logger.info(f"{member_name} already in party")
                return False
        
        char_stats = config["stats"]
        
        new_char = Character(attack=char_stats[0],defense=char_stats[1],max_hp=char_stats[2],will=char_stats[3])
        new_char.sprite_key = config['sprite_key']
        
        # Configurar sprite
        resource_manager = ResourceManager.get_instance()
        sprite_sheet = resource_manager.get_spritesheet(config['sprite_key'])
        if sprite_sheet:
            new_char.sprite_preview = sprite_sheet.get_frame(0, 0)
            new_char.sprite_preview_sz = (sprite_sheet.frame_width, sprite_sheet.frame_height)
        else:
            new_char.sprite_preview = pygame.Surface((25, 44))
            new_char.sprite_preview.fill(config['color'])
            new_char.sprite_preview_sz = (25, 44)
        
        # Añadir items iniciales
        from Characters.ItemManager import item_manager
        for item_id in config['items']:
            item = item_manager.get_item(item_id)
            if item:
                new_char.inventory.add(item)
                new_char.equipment.equip(item)
        
        self.characters.append(new_char)
        self.party.add(new_char)
        logger.info(f"{member_name} added to party")
        return True
    
    def remove_member(self, index: int) -> Optional[Character]:
        """Remueve un miembro del grupo (no se puede remover a Ely)"""
        if index <= 0 or index >= len(self.characters):
            logger.warning(f"Cannot remove character at index {index}")
            return None
        
        removed_char = self.characters.pop(index)
        # Tambien remover del objeto Party si es necesario
        logger.info(f"Character removed from party at index {index}")
        return removed_char
    
    def heal_all(self,amount:int):
        """Cura a todos los miembros del grupo"""
        for char in self.characters:
            char.current_hp = char.heal(amount)
            char.hp_color = char._calculate_hp_color()
        logger.debug(f"All party members healed {amount} HP ")
    
    def damage_all(self, amount: int):
        """Daña a todos los miembros del grupo"""
        for char in self.characters:
            char.take_damage(amount)
        logger.debug(f"All party members took {amount} damage")

class WorldManager:
    """Gestiona el mundo del juego, mapas y transiciones"""
    
    def __init__(self, tile_size: int, start_map_path: str):
        self.tile_size = tile_size
        self.current_map: Optional[Map] = None
        self.next_map_obj: Optional[Map] = None
        self.next_map_path: Optional[str] = None
        
        # Grupos de sprites
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.interactable_sprites = pygame.sprite.Group()
        self.npc_sprites = pygame.sprite.Group()
        
        # Sistema de transiciones
        self.fade = FadeTransition((320, 240), speed=550)  # TODO: usar config
        
        # Cargar mapa inicial
        self.load_map(start_map_path)
    
    def load_map(self, map_path: str):
        """Carga un nuevo mapa"""
        try:
            logger.info(f"Loading map: {map_path}")
            
            # Limpiar sprites existentes
            self._clear_sprites()
            
            # Cargar nuevo mapa
            self.current_map = Map(
                map_path, 
                self.tile_size,
                self.interactable_sprites,
                self.all_sprites,
                self.collision_sprites
            )
            
            logger.info(f"Map loaded successfully: {map_path}")
            
        except Exception as e:
            logger.error(f"Error loading map {map_path}: {e}")
            raise
    
    def _clear_sprites(self):
        """Limpia todos los grupos de sprites"""
        self.all_sprites.empty()
        self.collision_sprites.empty() 
        self.interactable_sprites.empty()
        self.npc_sprites.empty()
    
    def start_transition(self, new_map_path: str, callback=None):
        """Inicia una transicion a un nuevo mapa"""
        self.next_map_path = new_map_path
        
        # Pre-cargar el siguiente mapa
        try:
            self.next_map_obj = Map(
                new_map_path,
                self.tile_size,
                pygame.sprite.Group(),  # Grupos temporales
                AllSprites(),
                pygame.sprite.Group()
            )
            
            # Iniciar fade
            def fade_callback():
                self._finish_transition()
                if callback:
                    callback()

            self.fade.start(callback=fade_callback)
            logger.info(f"Started transition to {new_map_path}")
            
        except Exception as e:
            logger.error(f"Error pre-loading map for transition: {e}")
    
    def _finish_transition(self):
        """Completa la transicion de mapa"""
        if self.next_map_obj:
            # Limpiar mapa actual
            self._clear_sprites()
            if self.current_map:
                del self.current_map
            
            # Asignar nuevo mapa
            self.current_map = self.next_map_obj
            self.all_sprites = self.current_map.allsprites_group
            self.interactable_sprites = self.current_map.interactable_group
            self.collision_sprites = self.current_map.collision_group
            
            # Limpiar variables de transicion
            self.next_map_obj = None
            self.next_map_path = None
            
            logger.info("Map transition completed")
    
    def get_start_position(self) -> tuple:
        """Obtiene la posicion de inicio del mapa actual"""
        if self.current_map:
            return self.current_map.return_start_point()
        return (0, 0)
    
    def update(self, dt: float):
        """Actualiza el sistema del mundo"""
        if self.fade.active:
            self.fade.update(dt)    
    def is_transitioning(self) -> bool:
        """Verifica si hay una transicion activa"""
        return self.fade.active
