import os
import pygame
import logging
from pathlib import Path
from os.path import join
from collections import deque

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importaciones directas (eliminamos Imports.py)
from Settings.Settings import *
from ResourceManager import ResourceManager
from GameSystems import GameStateManager, RenderSystem, PartyManager, WorldManager, GameState
from Game.World.Sprites import Follower
from UI.Menu import Menu
from Characters.Player import Player
from UI.Components.Dialog import DialogManager
from UI.UI_Inventory import UI_Inventory
from DebugMenu import DebugMenu
from Game.World.Map import FadeTransition

# Centrar ventana
os.environ["SDL_VIDEO_CENTERED"] = "1"

class Scene:
    """Clase base para escenas del juego"""
    def __init__(self, game):
        self.game = game
    
    def handle_events(self, events): 
        pass
    
    def update(self, dt): 
        pass
    
    def draw(self, surface): 
        pass
    
    def cleanup(self):
        """Limpia recursos de la escena"""
        pass

class MenuScene(Scene):
    """Escena del menú principal"""
    
    def __init__(self, game, font):
        super().__init__(game)
        self.resource_manager = ResourceManager.get_instance()
        
        # Inicializar menús
        self.menus = {
            "main": Menu(game.internal_surf, font, [
                ("Empezar", lambda: self.game.change_scene("juego")),
                ("Ajustes", lambda: self.change_menu("settings")),
                ("Salir", self.game.close_game),
            ]),
            "settings": Menu(game.internal_surf, font, [
                ("Audio", lambda: self.change_menu("audio")),
                ("Video", lambda: self.change_menu("video")),
                ("Volver", lambda: self.change_menu("main")),
            ]),
            "audio": Menu(game.internal_surf, font, [
                ("Vol +", self.game.increase_volume),
                ("Vol -", self.game.decrease_volume),
                ("Volver", lambda: self.change_menu("settings")),
            ]),
            "video": Menu(game.internal_surf, font, [
                ("Resolución", self.game.toggle_resolution),
                ("Fullscreen", self.game.toggle_fullscreen),
                ("Volver", lambda: self.change_menu("settings")),
            ]),
        }
        
        self.current_menu = "main"

    def change_menu(self, name):
        """Cambia el menú actual"""
        if name in self.menus:
            self.current_menu = name
            self.menus[name].selected_index = 0

    def handle_events(self, events):
        menu = self.menus[self.current_menu]
        for event in events:
            menu.handle_key_event(event)
            for btn in menu.buttons:
                btn.handle_event(event)

    def update(self, dt):
        self.menus[self.current_menu].update()

    def draw(self, surface):
        self.menus[self.current_menu].draw()

class GameScene(Scene):
    """Escena principal del juego refactorizada"""
    
    def __init__(self, game):
        super().__init__(game)
        logger.info("Initializing GameScene")
        self.player_history = [] 
        try:
            # Inicializar sistemas
            self._init_systems()
            self._init_world()
            self._init_ui()
            
            logger.info("GameScene initialized successfully")
        
        except Exception as e:
            logger.error(f"Error initializing GameScene: {e}")
            # Cleanup en caso de error
            self.cleanup()
            raise
    
    def _init_systems(self):
        """Inicializa los sistemas del juego"""
        try:
            self.resource_manager = ResourceManager.get_instance()
            self.state_manager = GameStateManager()
            self.render_system = RenderSystem(self.game.INT_W, self.game.INT_H)
            self.party_manager = PartyManager()
            
            # Sistema de mundo
            start_map_path = join(MAPS_DIR, "Aula", "Aula-1.tmx")
            self.world_manager = WorldManager(TILE_SIZE, start_map_path)
            
            logger.debug("Game systems initialized")
        
        except Exception as e:
            logger.error(f"Error initializing systems: {e}")
            raise
    
    def _init_world(self):
        """Inicializa el mundo del juego"""
        # Crear jugador
        start_pos = self.world_manager.get_start_position()
        
        # Sistema de diálogos
        default_sound = self.resource_manager.get_sound("default")
        portrait = self.resource_manager.get_image("koral_portrait")

        # Cargar portrait si no existe
        if not portrait:
            portrait_path = SPRITES_DIR / "Koral" / "No-eyes-Koral1.png"
            if portrait_path.exists():
                portrait = self.resource_manager.load_image("koral_portrait", portrait_path)
            else:
                logger.warning("Portrait not found, using placeholder")
                portrait = None

        self.dialog_manager = DialogManager(
            self.game.font, 300, WINDOW_HEIGHT,
            sound=default_sound,
            portrait=portrait
        )
        
        # Verificar que el sprite sheet existe antes de crear el jugador
        sprite_sheet_key = "Ely"  # El ResourceManager usa "Ely" con mayúscula
        sprite_sheet = self.resource_manager.get_spritesheet(sprite_sheet_key)

        if not sprite_sheet:
            logger.warning(f"Sprite sheet '{sprite_sheet_key}' not found, creating placeholder")
            # Crear un placeholder sprite sheet
            placeholder_surface = pygame.Surface((25, 44))
            placeholder_surface.fill((100, 150, 255))  # Color azul para Ely
            from ResourceManager import SpriteSheet
            sprite_sheet = SpriteSheet(placeholder_surface, 25, 44)
            self.resource_manager._sprite_sheets[sprite_sheet_key] = sprite_sheet

        # Crear jugador con manejo de errores
        self.player = Player(
            pos=start_pos,
            game_scene=self,
            sprite_sheet_key=sprite_sheet_key,
            dialog_manager=self.dialog_manager,
            interactuables=self.world_manager.interactable_sprites,
            collision_sprites=self.world_manager.collision_sprites,
            groups=self.world_manager.all_sprites
        )
        self.followers = []
        self._create_followers()
        logger.debug("World initialized")
    # NUEVO MÉTODO en GameScene:
    def _create_followers(self):
            """Crea followers para todos los personajes excepto el primero (player)"""
            # Limpiar followers existentes
            for follower in self.followers:
                follower.kill()  # Remover del grupo de sprites
            self.followers.clear()
            
            # Crear nuevos followers
            for character in self.party_manager.characters[1:]:
                follower = Follower(character, self, self.world_manager.all_sprites)
                
                # Posicionar follower en la posición del jugador inicialmente
                if hasattr(self, 'player') and self.player:
                    follower.teleport_to(self.player.rect.center)
                
                self.followers.append(follower)
            
            logger.debug(f"Created {len(self.followers)} followers")
            
    def _init_ui(self):
        """Inicializa la interfaz de usuario"""
        try:
            # UI del inventario
            inventory_rect = pygame.Rect(
                (self.game.INT_W - 225) // 2,
                (self.game.INT_H - 200) // 2,
                225,
                200
            )
            
            self.inventory_ui = UI_Inventory(
                inventory_rect, 
                self.game.font, 
                self.party_manager.characters
            )
            
            # Menú de debug
            self.debug_menu = DebugMenu(self.game.font_12, self)
            
            logger.debug("UI initialized")
        
        except Exception as e:
            logger.error(f"Error initializing UI: {e}")
            raise
    
    def add_party_member(self, member_name: str):
        """Añade un miembro al grupo"""
        success = self.party_manager.add_member(member_name)
        if success:
            # Actualizar referencia en UI
            self.inventory_ui.update_party_reference(self.party_manager.characters)
            # AGREGAR: Recrear followers
            self._create_followers()
        return success
    
    def remove_party_member(self, index: int):
        """Remueve un miembro del grupo"""
        removed = self.party_manager.remove_member(index)
        if removed:
            # Actualizar referencia en UI
            self.inventory_ui.update_party_reference(self.party_manager.characters)
            # AGREGAR: Recrear followers
            self._create_followers()
        return removed
    
    def go_next_level(self, path: str):
        """Inicia transición a un nuevo nivel"""
        logger.info(f"Starting transition to {path}")
        self.state_manager.set_state(GameState.TRANSITIONING)
        self.world_manager.start_transition(path, self._finish_level_change)
    
    def _finish_level_change(self):
            """Completa el cambio de nivel"""
            # Reposicionar jugador
            self._reposition_player()
            
            # Actualizar referencias del jugador
            self.player.interactables = self.world_manager.interactable_sprites
            self.player.collision_sprites = self.world_manager.collision_sprites
            
            # Añadir jugador al nuevo mundo
            self.world_manager.all_sprites.add(self.player)
            
            # NUEVO: Limpiar el path del jugador y reposicionar followers
            self.player_path.clear()
            self.player_path.append(self.player.rect.center)
            
            # Reposicionar todos los followers en la nueva posición del jugador
            for follower in self.followers:
                follower.teleport_to(self.player.rect.center)
                # Re-añadir al grupo de sprites del nuevo mapa
                self.world_manager.all_sprites.add(follower)
            
            # Volver al estado de juego
            self.state_manager.set_state(GameState.PLAYING)
            logger.info("Level transition completed")
    
    def _reposition_player(self):
        """Reposiciona al jugador en el punto de inicio del nuevo mapa"""
        logger.debug("Repositioning player")
        self.player.state = self._get_opposite_state()
        self.player.image = self.player.frames[self.player.state][0]
        
        start_pos = self.world_manager.get_start_position()
        self.player.hitbox_rect.topleft = start_pos
        self.player.pos.x = self.player.hitbox_rect.centerx
        self.player.pos.y = self.player.hitbox_rect.bottom - 18
        self.player.rect.midbottom = self.player.hitbox_rect.midbottom
    
    def _get_opposite_state(self) -> str:
        """Obtiene el estado opuesto del jugador para transiciones"""
        opposite_states = {
            "up": "down",
            "down": "up", 
            "left": "right",
            "right": "left"
        }
        return opposite_states.get(self.player.state, "down")
    
    @property
    def characters(self):
        """Propiedad para compatibilidad con DebugMenu"""
        return self.party_manager.characters
    
    def handle_events(self, events):
        """Maneja eventos con sistema de estados"""
        for event in events:
            # Debug menu tiene prioridad máxima
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                if not self.debug_menu.visible:
                    self.debug_menu.toggle_visibility()
                    self.state_manager.set_state(GameState.DEBUG_MENU)
                else:
                    self.debug_menu.toggle_visibility()
                    self.state_manager.set_state(GameState.PLAYING)
                continue
            
            # Si debug menu maneja el evento, no procesar más
            if self.state_manager.is_state(GameState.DEBUG_MENU):
                if self.debug_menu.handle_input(event):
                    continue
            
            # Manejo del inventario
            if event.type == pygame.KEYDOWN and event.key == pygame.K_i:
                if self.inventory_ui.visible:
                    self.inventory_ui.toggle()
                    self.state_manager.pop_state()
                else:
                    self.inventory_ui.toggle()
                    self.state_manager.push_state(GameState.INVENTORY_OPEN)
            
            # Inventario maneja su propio input
            if self.state_manager.is_state(GameState.INVENTORY_OPEN):
                self.inventory_ui.handle_input(event)
                continue
            
            # Input del jugador solo si puede moverse
        if self.state_manager.can_move_player():
            self.player.input(events)
    

    def update(self, dt):
        """Actualización simplificada con historial completo del jugador"""
        
        # 1) Debug y transiciones
        self.debug_menu.update(dt)
        self.world_manager.update(dt)

        # 2) Movimiento del jugador
        if self.state_manager.can_move_player():
            self.player.move(dt)      
            self.player.animate(dt)

        # 3) NUEVO: Guardar estado completo del jugador en el historial
        if self.state_manager.can_move_player():
            # Por defecto, tomamos datos actuales
            pos_to_store = self.player.pos.copy()
            dir_to_store = self.player.direction
            frame_to_store = self.player.frame_index
            is_moving= self.player.is_actually_moving

            player_data = {
                'position': pos_to_store,
                'state':    self.player.state,
                'frame_index': frame_to_store,
                'direction':   dir_to_store,
                "moving":is_moving
            }

            if (player_data)["moving"] != 0:
                self.player_history.append(player_data)
            if (player_data)["moving"] == 0  and len(self.player_history) > 20:
                self.player_history[-20]["frame_index"] = 0
                self.player_history[-20]["moving"] = False
                self.player_history[-20]["direction"] = pygame.Vector2()
            if len(self.player_history) > 500:
                self.player_history.pop(0)

        # 4) NUEVO: Actualizar followers con datos exactos del historial
        if self.followers and len(self.player_history) > 20:
            for idx, follower in enumerate(self.followers, start=1):
                if len(self.player_history):
                    hist_idx = len(self.player_history) - 20
                    past_player_data = self.player_history[hist_idx]
           
                    follower.follow_player_exact(past_player_data,dt)


        # 5) Resto del código igual...
        self.dialog_manager.update()
        
        if not self.dialog_manager.active \
        and not self.world_manager.is_transitioning() \
        and not self.inventory_ui.visible:
            for sprite in self.world_manager.all_sprites:
                if not isinstance(sprite, Follower):
                    if hasattr(sprite, 'update'):
                        sprite.update(dt)
                        
    def draw(self, surface):
        """Renderiza la escena"""
        try:
            # Renderizar mundo
            if hasattr(self, 'player'):
                self.render_system.render_world(
                    surface, 
                    self.world_manager.all_sprites, 
                    self.player.rect.center
                )
            else:
                # Si no hay jugador, renderizar desde el centro
                self.render_system.render_world(
                    surface, 
                    self.world_manager.all_sprites, 
                    (self.game.INT_W // 2, self.game.INT_H // 2)
                )
            mapa_actual = getattr(self.world_manager.current_map, 'map_path', '???')
            nombre_mapa = self.game.font.render(f"MAPA: {mapa_actual}", True, (255, 255, 0))
            surface.blit(nombre_mapa, (10, 10))
            # Elementos de debug visual
            if hasattr(self, 'player'):
                self.render_system.render_debug_visuals(
                    surface,
                    self.debug_menu,
                    self.world_manager.collision_sprites,
                    self.world_manager.interactable_sprites,
                    self.player.rect
                )
            
            # UI
            self.inventory_ui.draw(surface)
            if hasattr(self, 'dialog_manager'):
                self.dialog_manager.draw(surface)
            self.debug_menu.draw(surface)
            
            # Transiciones
            if self.world_manager.is_transitioning():
                self.world_manager.fade.draw(surface)
        
        except Exception as e:
            logger.error(f"Error drawing GameScene: {e}")
            # Dibujar un mensaje de error
            error_surf = self.game.font.render("Render Error", True, (255, 0, 0))
            surface.blit(error_surf, (10, 10))
    
    def cleanup(self):
        """Limpia recursos de la escena"""
        logger.info("Cleaning up GameScene")
        try:
            # Limpiar sistemas si es necesario
            if hasattr(self, 'world_manager'):
                del self.world_manager
            if hasattr(self, 'party_manager'):
                del self.party_manager
            if hasattr(self, 'player'):
                del self.player
        except Exception as e:
            logger.error(f"Error during GameScene cleanup: {e}")

class Game:
    """Clase principal del juego"""
    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Deswonder")
        self.INT_W, self.INT_H = 320, 240
        
        # Inicializar ventana
        self._init_window()
        
        # Configurar logging
        self._setup_logging()
        
        # Inicializar recursos
        self._init_resources()
        
        # Inicializar escenas
        self.scene = MenuScene(self, self.font)
        
        # Variables de juego
        self.clock = pygame.time.Clock()
        self.running = True
        
        logger.info("Game initialized successfully")
    
    def _setup_logging(self):
        """Configura el sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _init_resources(self):
        """Inicializa todos los recursos del juego"""
        try:
            resource_manager = ResourceManager.get_instance()
            base_dir = Path(__file__).resolve().parent.parent
            resource_manager.preload_all_resources(base_dir)
            
            # Obtener fuentes preconfiguradas
            self.font = resource_manager.get_font("main_16")
            self.font_12 = resource_manager.get_font("main_12")
            
            if not self.font:
                logger.warning("Using fallback font")
                self.font = pygame.font.Font(None, 16)
                self.font_12 = pygame.font.Font(None, 12)
            
            logger.info("Resources initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing resources: {e}")
            # Fallback a recursos por defecto
            self.font = pygame.font.Font(None, 16)
            self.font_12 = pygame.font.Font(None, 12)
    
    def _init_window(self):
        """Inicializa la ventana del juego"""
        self.internal_surf = pygame.Surface((self.INT_W, self.INT_H))
        
        # Modo ventana borderless con zoom fijo
        self.windowed_scale = 4
        self.windowed_size = (
            self.INT_W * self.windowed_scale,
            self.INT_H * self.windowed_scale
        )
        self.screen = pygame.display.set_mode(self.windowed_size, pygame.SHOWN)
        self.fullscreen = False
        
        # Recalcular escala y offset
        self._recalc_scale(*self.windowed_size)
    
    def _recalc_scale(self, sw, sh):
        """Recalcula la escala y offset para el renderizado"""
        self.scale = min(sw // self.INT_W, sh // self.INT_H) or 1
        self.scaled_size = (self.INT_W * self.scale, self.INT_H * self.scale)
        self.offset = (
            (sw - self.scaled_size[0]) // 2,
            (sh - self.scaled_size[1]) // 2
        )
    
    def change_scene(self, name):
        """Cambia la escena actual con limpieza de recursos"""
        try:
            # Limpiar escena anterior
            if hasattr(self.scene, 'cleanup'):
                self.scene.cleanup()
            
            # Crear nueva escena
            if name == "menu":
                self.scene = MenuScene(self, self.font)
            elif name == "juego":
                self.scene = GameScene(self)
            elif name == "cutscene":
                # TODO: Implementar escena de cutscene
                logger.warning("Cutscene not implemented yet")
            else:
                logger.warning(f"Unknown scene: {name}")
                return
            
            logger.info(f"Scene changed to: {name}")
            
        except Exception as e:
            logger.error(f"Error changing scene to {name}: {e}")
            # Fallback al menú principal
            self.scene = MenuScene(self, self.font)
    
    def toggle_fullscreen(self):
        """Alterna entre fullscreen y ventana"""
        try:
            self.fullscreen = not self.fullscreen
            mode = pygame.FULLSCREEN if self.fullscreen else pygame.NOFRAME
            size = (
                (pygame.display.Info().current_w, pygame.display.Info().current_h)
                if self.fullscreen else self.windowed_size
            )
            self.screen = pygame.display.set_mode(size, mode)
            self._recalc_scale(*size)
            logger.debug(f"Fullscreen toggled: {self.fullscreen}")
        except Exception as e:
            logger.error(f"Error toggling fullscreen: {e}")
    
    # Funciones de configuración (placeholder para implementación futura)
    def toggle_resolution(self):
        """Cambia la resolución interna"""
        logger.info("Resolution toggle - not implemented yet")
    
    def increase_volume(self):
        """Aumenta el volumen"""
        current_volume = pygame.mixer.music.get_volume()
        new_volume = min(1.0, current_volume + 0.1)
        pygame.mixer.music.set_volume(new_volume)
        logger.debug(f"Volume increased to {new_volume}")
    
    def decrease_volume(self):
        """Disminuye el volumen"""
        current_volume = pygame.mixer.music.get_volume()
        new_volume = max(0.0, current_volume - 0.1)
        pygame.mixer.music.set_volume(new_volume)
        logger.debug(f"Volume decreased to {new_volume}")
    
    def close_game(self):
        """Cierra el juego limpiamente"""
        logger.info("Closing game")
        self.running = False
        
        # Limpiar recursos
        try:
            if hasattr(self.scene, 'cleanup'):
                self.scene.cleanup()
            
            resource_manager = ResourceManager.get_instance()
            resource_manager.cleanup()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def run(self):
        """Bucle principal del juego"""
        logger.info("Starting game loop")
        
        try:
            while self.running:
                # Calcular delta time
                dt = self.clock.tick(60) / 1000.0
                
                # Obtener eventos
                events = pygame.event.get()
                
                # Manejar eventos del sistema
                for event in events:
                    if event.type == pygame.QUIT:
                        self.close_game()
                        continue
                    
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_F11:
                            self.toggle_fullscreen()
                            continue
                
                # Actualizar escena actual
                if self.scene:
                    self.scene.handle_events(events)
                    self.scene.update(dt)
                
                # Renderizar
                self.internal_surf.fill((0, 0, 0))
                if self.scene:
                    self.scene.draw(self.internal_surf)
                
                # Escalar y mostrar
                scaled = pygame.transform.scale(self.internal_surf, self.scaled_size)
                self.screen.fill((0, 0, 0))
                self.screen.blit(scaled, self.offset)
                
                # Actualizar pantalla
                pygame.display.flip()
                
        except Exception as e:
            logger.error(f"Error in game loop: {e}")
        finally:
            logger.info("Game loop ended")
            pygame.quit()

if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        pygame.quit()