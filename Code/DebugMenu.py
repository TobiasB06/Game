import pygame
from enum import Enum
from Characters.Inventory import Item, Character
from Characters.ItemManager import item_manager

import logging
logger = logging.getLogger(__name__)
class DebugCategory(Enum):
    MAIN = "main"
    PARTY = "party"
    ITEMS = "items"
    VISUALS = "visuals"
    PLAYER = "player"

class DebugMenu:
    def __init__(self, font, game_scene):
        self.font = font
        self.game_scene = game_scene
        self.visible = False
        self.current_category = DebugCategory.MAIN
        self.selected_index = 0
        from CircularDebugSprite import DebugCircleManager
        game_scene.circle_manager = DebugCircleManager(game_scene)
        # Estados de debug
        self.show_hitboxes = False
        self.show_interaction_zones = False
        self.noclip_mode = False
        self.god_mode = False
        
        # Configuracion de menu
        self.menu_width = 280
        self.menu_height = 200
        self.menu_x = 20
        self.menu_y = 20
        
        # Opciones por categoría
        self.menu_options = {
            DebugCategory.MAIN: [
                ("Party Management", lambda: self.change_category(DebugCategory.PARTY)),
                ("Item Management", lambda: self.change_category(DebugCategory.ITEMS)),
                ("Visual Debug", lambda: self.change_category(DebugCategory.VISUALS)),
                ("Player Debug", lambda: self.change_category(DebugCategory.PLAYER)),
                ("Close Debug", self.toggle_visibility)
            ],
            DebugCategory.PARTY: [
                ("Add Koral", lambda: self.add_party_member("koral")),
                ("Add Vel", lambda: self.add_party_member("vel")),
                ("Remove Last Member", self.remove_last_party_member),
                ("Heal All Party", self.heal_all_party),
                ("Damage All Party", self.damage_all_party),
                ("← Back", lambda: self.change_category(DebugCategory.MAIN))
            ],
            DebugCategory.ITEMS: [
                ("Add All Weapons", self.add_all_weapons),
                ("Add All Armors", self.add_all_armors),
                ("Clear Inventory", self.clear_current_inventory),
                ("Give Legendary Items", self.give_legendary_items),
                ("Remove All Equipment", self.remove_all_equipment),
                ("← Back", lambda: self.change_category(DebugCategory.MAIN))
            ],
            DebugCategory.VISUALS: [
                (f"Hitboxes: {'ON' if self.show_hitboxes else 'OFF'}", self.toggle_hitboxes),
                (f"Interaction Zones: {'ON' if self.show_interaction_zones else 'OFF'}", self.toggle_interaction_zones),
                ("Add Moving Circle", self.add_moving_circle),
                ("Add Follower Circle", self.add_follower_circle),
                ("Toggle Circle Trails", self.toggle_circle_trails),
                ("Remove All Circles", self.remove_all_circles),
                ("Show Party Info", self.show_party_info),
                ("Show Item Counts", self.show_item_counts),
                ("← Back", lambda: self.change_category(DebugCategory.MAIN))
            ],
            DebugCategory.PLAYER: [
                (f"Noclip: {'ON' if self.noclip_mode else 'OFF'}", self.toggle_noclip),
                (f"God Mode: {'ON' if self.god_mode else 'OFF'}", self.toggle_god_mode),
                ("Teleport to Start", self.teleport_to_start),
                ("Max Stats", self.max_player_stats),
                ("Reset Player", self.reset_player),
                ("← Back", lambda: self.change_category(DebugCategory.MAIN))
            ]
        }

    def add_moving_circle(self):
        """Añade un círculo que se mueve automáticamente"""
        if hasattr(self.game_scene, 'circle_manager'):
            self.game_scene.circle_manager.add_moving_circle("circular", 40)
            print("[DEBUG] Moving circle added")

    def add_follower_circle(self):
        """Añade un círculo que sigue al jugador"""
        if hasattr(self.game_scene, 'circle_manager') and hasattr(self.game_scene, 'player'):
            self.game_scene.circle_manager.add_follower_circle(self.game_scene.player, delay_frames=20)
            print("[DEBUG] Follower circle added")

    def toggle_circle_trails(self):
        """Activa/desactiva los trails de los círculos"""
        if hasattr(self.game_scene, 'circle_manager'):
            self.game_scene.circle_manager.toggle_trails()
            print(f"[DEBUG] Circle trails: {'ON' if self.game_scene.circle_manager.show_trails else 'OFF'}")

    def remove_all_circles(self):
        """Remueve todos los círculos de debug"""
        if hasattr(self.game_scene, 'circle_manager'):
            self.game_scene.circle_manager.remove_all_circles()
            print("[DEBUG] All debug circles removed")
    def toggle_visibility(self):
        from GameSystems import GameState
        self.visible = not self.visible
        if self.visible:
            # Al abrir: reset de categoría y cambio de estado
            self.current_category = DebugCategory.MAIN
            self.selected_index = 0
            self.game_scene.state_manager.set_state(GameState.DEBUG_MENU)
        else:
            # Al cerrar: volvemos a jugar
            self.game_scene.state_manager.set_state(GameState.PLAYING)

    def change_category(self, category):
        self.current_category = category
        self.selected_index = 0
        # Actualizar opciones dinámicas
        self.update_dynamic_options()

    def update_dynamic_options(self):
        """Actualiza opciones que cambian segun el estado"""
        if self.current_category == DebugCategory.VISUALS:
            self.menu_options[DebugCategory.VISUALS][0] = (
                f"Hitboxes: {'ON' if self.show_hitboxes else 'OFF'}", 
                self.toggle_hitboxes
            )
            self.menu_options[DebugCategory.VISUALS][1] = (
                f"Interaction Zones: {'ON' if self.show_interaction_zones else 'OFF'}", 
                self.toggle_interaction_zones
            )
        elif self.current_category == DebugCategory.PLAYER:
            self.menu_options[DebugCategory.PLAYER][0] = (
                f"Noclip: {'ON' if self.noclip_mode else 'OFF'}", 
                self.toggle_noclip
            )
            self.menu_options[DebugCategory.PLAYER][1] = (
                f"God Mode: {'ON' if self.god_mode else 'OFF'}", 
                self.toggle_god_mode
            )

    def handle_input(self, event):
        if not self.visible:
            return False

        if event.type == pygame.KEYDOWN:
            current_options = self.menu_options[self.current_category]
            
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(current_options)
                self.update_dynamic_options()
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(current_options)
                self.update_dynamic_options()
            elif event.key == pygame.K_RETURN:
                if self.selected_index < len(current_options):
                    current_options[self.selected_index][1]()
            elif event.key == pygame.K_ESCAPE or event.key == pygame.K_F1:
                self.toggle_visibility()
                
        return True  # Indica que el evento fue manejado

    # === FUNCIONES DE PARTY ===
    def add_party_member(self, member_name):
        try:
            self.game_scene.add_party_member(member_name)
            print(f"[DEBUG] {member_name.capitalize()} agregado al grupo")
        except Exception as e:
            print(f"[DEBUG] Error agregando {member_name}: {e}")

    def remove_last_party_member(self):
        if len(self.game_scene.characters) > 1:  # No remover a Ely
            removed = self.game_scene.remove_party_member(len(self.game_scene.characters) - 1)
            print(f"[DEBUG] Miembro removido del grupo")
        else:
            print("[DEBUG] No se puede remover a Ely (líder del grupo)")

    def heal_all_party(self):
        for char in self.game_scene.characters:
            char.current_hp = char.get_max_hp()
            char.hp_color = char._calculate_hp_color()
        print("[DEBUG] Todos los miembros curados")

    def damage_all_party(self):
        for char in self.game_scene.characters:
            char.take_damage(30)
        print("[DEBUG] Todos los miembros dañados")

    # === FUNCIONES DE ITEMS ===
    def add_all_weapons(self):
        current_char = self.get_current_character()
        if not current_char:
            return
            
        weapons = item_manager.get_items_by_type("weapon")
        for weapon in weapons:
            current_char.inventory.add(weapon, 1)
        print(f"[DEBUG] {len(weapons)} armas agregadas al inventario")

    def add_all_armors(self):
        current_char = self.get_current_character()
        if not current_char:
            return
            
        armors = item_manager.get_items_by_type("armor")
        for armor in armors:
            current_char.inventory.add(armor, 1)
        print(f"[DEBUG] {len(armors)} armaduras agregadas al inventario")

    def clear_current_inventory(self):
        current_char = self.get_current_character()
        if not current_char:
            return
            
        current_char.inventory._items.clear()
        print("[DEBUG] Inventario limpiado")

    def give_legendary_items(self):
        current_char = self.get_current_character()
        if not current_char:
            return
            
        # Items legendarios (IDs específicos)
        legendary_sword = item_manager.get_item(9)  # Espada legendaria
        divine_armor = item_manager.get_item(10)    # Armadura divina
        
        if legendary_sword:
            current_char.inventory.add(legendary_sword, 1)
        if divine_armor:
            current_char.inventory.add(divine_armor, 1)
            
        print("[DEBUG] Items legendarios otorgados")

    def remove_all_equipment(self):
        current_char = self.get_current_character()
        if not current_char:
            return
            
        # Devolver equipment al inventario antes de remover
        if current_char.equipment.weapon:
            current_char.inventory.add(current_char.equipment.weapon)
            current_char.equipment.unequip_weapon()
            
        for armor in current_char.equipment.armors[:]:  # Copia la lista
            current_char.inventory.add(armor)
            current_char.equipment.unequip_armor(armor)
            
        print("[DEBUG] Todo el equipamiento removido")

    # === FUNCIONES VISUALES ===
    def toggle_hitboxes(self):
        self.show_hitboxes = not self.show_hitboxes
        print(f"[DEBUG] Hitboxes: {'ON' if self.show_hitboxes else 'OFF'}")

    def toggle_interaction_zones(self):
        self.show_interaction_zones = not self.show_interaction_zones
        print(f"[DEBUG] Zonas de interaccion: {'ON' if self.show_interaction_zones else 'OFF'}")

    def show_party_info(self):
        print("\n=== PARTY INFO ===")
        for i, char in enumerate(self.game_scene.characters):
            char_info = self.game_scene.inventory_ui.get_character_info(i)
            stats = char.total_stats()
            print(f"{char_info['name']}: HP {char.current_hp}/{char.get_max_hp()}, "
                  f"ATK {stats.get('attack', 0)}, DEF {stats.get('defense', 0)}")
        print("==================")

    def show_item_counts(self):
        current_char = self.get_current_character()
        if not current_char:
            return
            
        print("\n=== INVENTORY ===")
        items = current_char.inventory.get_item_objects()
        if not items:
            print("Inventario vacío")
        else:
            for item in items:
                qty = current_char.inventory.quantity(item)
                print(f"{item.name}: {qty}")
        print("=================")

    def toggle_sprites_outline(self):
        # Esta funcion se implementaría en el sistema de render
        print("[DEBUG] Outline de sprites (no implementado aun)")

    # === FUNCIONES DE PLAYER ===
    def toggle_noclip(self):
        self.noclip_mode = not self.noclip_mode
        # Aplicar el modo noclip al jugador
        if hasattr(self.game_scene, 'player'):
            self.game_scene.player.noclip = self.noclip_mode
        print(f"[DEBUG] Noclip: {'ON' if self.noclip_mode else 'OFF'}")

    def toggle_god_mode(self):
        self.god_mode = not self.god_mode
        if self.god_mode:
            self.heal_all_party()
        print(f"[DEBUG] God Mode: {'ON' if self.god_mode else 'OFF'}")

    def teleport_to_start(self):
        if hasattr(self.game_scene, 'player') and hasattr(self.game_scene, 'map'):
            start_pos = self.game_scene.map.return_start_point()
            self.game_scene.player.pos.x, self.game_scene.player.pos.y = start_pos
            self.game_scene.player.hitbox_rect.center = start_pos
            self.game_scene.player.rect.midbottom = self.game_scene.player.hitbox_rect.midbottom
            print(f"[DEBUG] Jugador teletransportado a {start_pos}")

    def max_player_stats(self):
        for char in self.game_scene.characters:
            char.base_stats.update({
                "attack": 99,
                "defense": 99,
                "max_hp": 999,
            })
            char.current_hp = char.get_max_hp()
            char.hp_color = char._calculate_hp_color()
        print("[DEBUG] Stats maximizados")

    def reset_player(self):
        for char in self.game_scene.characters:
            char.base_stats = {"attack": 5, "defense": 5, "max_hp": 120}
            char.current_hp = 100
            char.hp_color = char._calculate_hp_color()
        print("[DEBUG] Stats reseteados")

    # === UTILIDADES ===
    def get_current_character(self):
        if hasattr(self.game_scene, 'inventory_ui'):
            return self.game_scene.inventory_ui.get_current_character()
        elif hasattr(self.game_scene, 'characters') and self.game_scene.characters:
            return self.game_scene.characters[0]
        return None

    def draw(self, surface):
        if not self.visible:
            return

        # Fondo del menu
        menu_rect = pygame.Rect(self.menu_x, self.menu_y, self.menu_width, self.menu_height)
        pygame.draw.rect(surface, (20, 20, 20), menu_rect)
        pygame.draw.rect(surface, (100, 100, 100), menu_rect, 2)

        # Título
        category_name = self.current_category.value.replace('_', ' ').title()
        title_text = f"DEBUG MENU - {category_name}"
        title_surf = self.font.render(title_text, True, (255, 255, 0))
        surface.blit(title_surf, (self.menu_x + 5, self.menu_y + 5))

        # Opciones del menu
        current_options = self.menu_options[self.current_category]
        y_offset = 30
        
        for i, (text, _) in enumerate(current_options):
            color = (255, 255, 255)
            if i == self.selected_index:
                # Highlight para opcion seleccionada
                highlight_rect = pygame.Rect(
                    self.menu_x + 2, 
                    self.menu_y + y_offset - 2, 
                    self.menu_width - 4, 
                    self.font.get_height() + 2
                )
                pygame.draw.rect(surface, (50, 50, 150), highlight_rect)
                color = (255, 255, 0)

            option_surf = self.font.render(text, True, color)
            surface.blit(option_surf, (self.menu_x + 5, self.menu_y + y_offset))
            y_offset += self.font.get_height() + 3

        # Instrucciones
        instructions = "↑↓: Navigate | ENTER: Select | F1/ESC: Close"
        inst_surf = pygame.font.Font(None, 12).render(instructions, True, (150, 150, 150))
        surface.blit(inst_surf, (self.menu_x + 5, self.menu_y + self.menu_height - 15))

    def draw_debug_visuals(self, surface, camera_offset):
        """Dibuja elementos de debug visual"""
        if not self.visible:
            return

        # Dibujar hitboxes de colision
        if self.show_hitboxes and hasattr(self.game_scene, 'collision'):
            for sprite in self.game_scene.collision:
                screen_rect = sprite.rect.move(camera_offset)
                pygame.draw.rect(surface, (255, 0, 0), screen_rect, 1)

        # Dibujar zonas de interaccion
        if self.show_interaction_zones and hasattr(self.game_scene, 'interactable_group'):
            for zone in self.game_scene.interactable_group:
                screen_rect = zone.rect.move(camera_offset)
                pygame.draw.rect(surface, (0, 255, 0), screen_rect, 1)
                
                # Mostrar texto de la zona
                if hasattr(zone, 'text') and zone.text:
                    text_surf = pygame.font.Font(None, 12).render(zone.text[:20], True, (0, 255, 0))
                    surface.blit(text_surf, (screen_rect.x, screen_rect.y - 15))

        # Informacion de FPS y posicion del jugador
        if hasattr(self.game_scene, 'player'):
            player_pos = self.game_scene.player.pos
            pos_text = f"Pos: ({int(player_pos.x)}, {int(player_pos.y)})"
            pos_surf = pygame.font.Font(None, 16).render(pos_text, True, (255, 255, 255))
            surface.blit(pos_surf, (surface.get_width() - 150, 10))

    def update(self, dt):
        """Actualiza el debug menu"""
        if self.god_mode:
            # Mantener HP al máximo en god mode
            for char in self.game_scene.characters:
                if char.current_hp < char.get_max_hp():
                    char.current_hp = char.get_max_hp()
                    char.hp_color = char._calculate_hp_color()