import pygame
from enum import Enum
from typing import List, Optional, Dict
import logging

from Characters.Inventory import InventoryModel, Character

logger = logging.getLogger(__name__)

class MenuState(Enum):
    CHARACTER_SELECT = "character_select"
    EQUIPMENT = "equipment"
    SKILLS = "skills"
    INVENTORY_SELECT = "inventory_select"

class UI_Inventory:
    def __init__(self, rect: pygame.Rect, font: pygame.font.Font, characters_list: List[Character], character_sprites=None):
        self.rect = rect
        self.font = font
        self.party = characters_list if characters_list else []  # Proteccion contra None
        self.visible = False
        
        # Validar que tenemos al menos un personaje
        if not self.party:
            logger.warning("UI_Inventory initialized with empty party")
        
        self.inventory_model = InventoryModel(self.party)
        
        # Estados de navegacion con validacion
        self.current_state = MenuState.CHARACTER_SELECT
        self.selected_character = 0
        self.selected_equipment = 0
        self.selected_skill = 0
        self.selected_inventory_item = 0
        
        # Sprites de personajes (opcional)
        self.character_sprites = character_sprites or {}
        
        # Informacion de personajes con sus nombres reales
        self.character_definitions = [
            {"name": "ELY", "sprite_key": "ely"},
            {"name": "KORAL", "sprite_key": "koral"},
            {"name": "VEL", "sprite_key": "vel"},
        ]
        
        # Configuracion de áreas
        self.setup_areas()
        
        # Validar índices iniciales
        self._validate_selections()
        
    def setup_areas(self):
        """Define las áreas de cada seccion del inventario"""
        # Área de personajes (izquierda superior) - 3 columnas
        self.char_area = pygame.Rect(
            self.rect.x + 2,
            self.rect.y + 15,
            100, 80
        )
        
        # Área de stats (izquierda inferior)
        self.stats_area = pygame.Rect(
            self.rect.x + 2,
            self.char_area.bottom,
            100, 40
        )
        
        # Área de habilidades (izquierda inferior)
        self.skills_area = pygame.Rect(
            self.rect.x + 2,
            self.stats_area.bottom,
            100, 65
        )
        
        # Área de equipamiento (derecha superior)
        self.equipment_area = pygame.Rect(
            self.char_area.right,
            self.rect.y + 15,
            122, 80
        )
        
        # Área de seleccion/inventario (derecha inferior)
        self.selection_area = pygame.Rect(
            self.equipment_area.x,
            self.equipment_area.bottom,
            122, 105
        )

    def _validate_selections(self):
        """Valida y corrige los índices de seleccion"""
        # Validar personaje seleccionado
        if self.party:
            self.selected_character = max(0, min(self.selected_character, len(self.party) - 1))
        else:
            self.selected_character = 0
        
        # Validar equipamiento seleccionado (máximo 3 slots: weapon, armor1, armor2)
        self.selected_equipment = max(0, min(self.selected_equipment, 2))
        
        # Validar skill seleccionado (máximo 3 skills hardcodeados)
        self.selected_skill = max(0, min(self.selected_skill, 2))
        
        # Validar item de inventario
        current_char = self.get_current_character()
        if current_char:
            available_items = self.inventory_model.get_available_items_for_slot(
                current_char, self.selected_equipment
            )
            if available_items:
                self.selected_inventory_item = max(0, min(self.selected_inventory_item, len(available_items) - 1))
            else:
                self.selected_inventory_item = 0

    def get_current_character(self) -> Optional[Character]:
        """Obtiene el personaje actualmente seleccionado con validacion"""
        if not self.party:
            logger.warning("Attempted to get current character from empty party")
            return None
            
        if 0 <= self.selected_character < len(self.party):
            return self.party[self.selected_character]
        
        logger.warning(f"Selected character index {self.selected_character} out of bounds")
        return None
    
    def get_character_info(self, index: int) -> Dict[str, str]:
        """Obtiene la informacion del personaje por índice con validacion"""
        if 0 <= index < len(self.character_definitions):
            return self.character_definitions[index]
        return {"name": f"CHAR{index+1}", "sprite_key": f"char{index+1}"}

    def toggle(self):
        """Alterna la visibilidad del inventario"""
        self.visible = not self.visible
        if self.visible:
            self.current_state = MenuState.CHARACTER_SELECT
            self._validate_selections()
            logger.debug("Inventory UI opened")
        else:
            logger.debug("Inventory UI closed")

    def handle_input(self, event):
        """Maneja input con validacion de estado"""
        if not self.visible:
            return
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.visible = False
                return
                
            # Solo procesar input si tenemos personajes
            if not self.party:
                logger.warning("No characters available for input handling")
                return
                
            if self.current_state == MenuState.CHARACTER_SELECT:
                self._handle_character_input(event)
            elif self.current_state == MenuState.EQUIPMENT:
                self._handle_equipment_input(event)
            elif self.current_state == MenuState.SKILLS:
                self._handle_skills_input(event)
            elif self.current_state == MenuState.INVENTORY_SELECT:
                self._handle_inventory_input(event)

    def _handle_character_input(self, event):
        """Maneja input en modo seleccion de personaje"""
        if not self.party:
            return
            
        if event.key == pygame.K_LEFT:
            self.selected_character = (self.selected_character - 1) % len(self.party)
        elif event.key == pygame.K_RIGHT:
            self.selected_character = (self.selected_character + 1) % len(self.party)
        elif event.key == pygame.K_DOWN:
            self.current_state = MenuState.SKILLS
            self.selected_skill = 0
        elif event.key == pygame.K_s:
            self.current_state = MenuState.EQUIPMENT
            self.selected_equipment = 0
        
        self._validate_selections()

    def _handle_equipment_input(self, event):
        """Maneja input en modo equipamiento"""
        equipment_slots = 3  # weapon, armor1, armor2

        if event.key in (pygame.K_x, pygame.K_BACKSPACE):
            self.current_state = MenuState.CHARACTER_SELECT
            return

        if event.key == pygame.K_RETURN:
            # Verificar que hay items disponibles antes de cambiar estado
            current_char = self.get_current_character()
            if current_char:
                available_items = self.inventory_model.get_available_items_for_slot(
                    current_char, self.selected_equipment
                )
                if available_items:
                    self.current_state = MenuState.INVENTORY_SELECT
                    self.selected_inventory_item = 0
                    self._validate_selections()
                else:
                    logger.debug(f"No items available for slot {self.selected_equipment}")
            return

        if event.key == pygame.K_UP:
            self.selected_equipment = (self.selected_equipment - 1) % equipment_slots
        elif event.key == pygame.K_DOWN:
            self.selected_equipment = (self.selected_equipment + 1) % equipment_slots

    def _handle_skills_input(self, event):
        """Maneja input en modo habilidades"""
        max_skills = 3  # BrokenSoul, Flagger, MechaSaber
        
        if event.key == pygame.K_UP:
            if self.selected_skill == 0:
                self.current_state = MenuState.CHARACTER_SELECT
            else:
                self.selected_skill = (self.selected_skill - 1) % max_skills
        elif event.key == pygame.K_DOWN:
            self.selected_skill = (self.selected_skill + 1) % max_skills

    def _handle_inventory_input(self, event):
        """Maneja input en modo seleccion de inventario"""
        current_char = self.get_current_character()
        if not current_char:
            self.current_state = MenuState.EQUIPMENT
            return
            
        available_items = self.inventory_model.get_available_items_for_slot(
            current_char, self.selected_equipment
        )
        
        if not available_items:
            logger.debug("No available items, returning to equipment menu")
            self.current_state = MenuState.EQUIPMENT
            return

        if event.key in (pygame.K_x, pygame.K_BACKSPACE):
            self.current_state = MenuState.EQUIPMENT
            return

        if event.key == pygame.K_RETURN:
            try:
                self.inventory_model.equip_selected_item()
                logger.debug(f"Item equipped successfully")
                # Opcional: volver al menu de equipamiento
                self.current_state = MenuState.EQUIPMENT
            except Exception as e:
                logger.error(f"Error equipping item: {e}")
            return

        # Navegacion por la lista
        if event.key == pygame.K_UP:
            self.selected_inventory_item = (self.selected_inventory_item - 1) % len(available_items)
        elif event.key == pygame.K_DOWN:
            self.selected_inventory_item = (self.selected_inventory_item + 1) % len(available_items)

    def draw(self, surface):
        """Dibuja la UI del inventario con manejo de errores"""
        if not self.visible:
            return
            
        try:
            # Fondo principal
            pygame.draw.rect(surface, (0, 0, 0), self.rect)
            pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)
            
            # Título
            title = self.font.render("INVENTORY", True, (255, 255, 0))
            surface.blit(title, (self.rect.x + 2, self.rect.y + 2))
            
            self._draw_characters(surface)
            self._draw_stats(surface)
            self._draw_skills(surface)
            self._draw_equipment(surface)
            self._draw_selection_area(surface)
            
        except Exception as e:
            logger.error(f"Error drawing inventory UI: {e}")
            # Dibujar mensaje de error
            error_surf = self.font.render("UI Error", True, (255, 0, 0))
            surface.blit(error_surf, (self.rect.x + 10, self.rect.y + 30))

    def _draw_characters(self, surface):
        """Dibuja la seccion de personajes con validacion"""
        pygame.draw.rect(surface, (0, 0, 0), self.char_area)
        pygame.draw.rect(surface, (255, 255, 255), self.char_area, 1)

        if not self.party:
            no_chars_surf = self.font.render("No party", True, (150, 150, 150))
            surface.blit(no_chars_surf, (self.char_area.x + 5, self.char_area.y + 35))
            return

        col_width = max(1, self.char_area.width // 3)  # Evitar division por 0

        for i, character in enumerate(self.party):
            if i >= 3:  # Solo mostrar máximo 3 personajes
                break
                
            col = i % 3
            x = self.char_area.x + col * col_width

            # Obtener sprite con fallback
            sprite = None
            w, h = 25, 44  # Tamaño por defecto
            
            try:
                if hasattr(character, "sprite_preview") and character.sprite_preview:
                    sprite = character.sprite_preview
                    if hasattr(character, "sprite_preview_sz"):
                        w, h = character.sprite_preview_sz
            except Exception as e:
                logger.warning(f"Error loading sprite for character {i}: {e}")

            # Rect del sprite, centrado horizontalmente
            sprite_rect = pygame.Rect(
                x + max(0, (col_width - w) // 2),
                self.char_area.y + 20,
                w, h
            )

            # Highlight si está seleccionado
            if (self.current_state == MenuState.CHARACTER_SELECT and 
                i == self.selected_character):
                hl = sprite_rect.inflate(3, 3)
                pygame.draw.rect(surface, (11, 142, 182), hl)

            # Dibujar sprite o placeholder
            if sprite:
                surface.blit(sprite, sprite_rect)
            else:
                pygame.draw.rect(surface, (100, 150, 255), sprite_rect)

            # Nombre del personaje
            char_info = self.get_character_info(i)
            name_surf = self.font.render(char_info["name"][:5], True, (255, 255, 255))
            name_x = x + max(0, (col_width - name_surf.get_width()) // 2)
            surface.blit(name_surf, (name_x, self.char_area.y + 5))

            # Barra de vida con validacion
            try:
                max_hp = character.get_max_hp()
                current_hp = max(0, character.current_hp)  # Evitar valores negativos
                
                if max_hp > 0:
                    bar_total_width = 28
                    bar_h = 5
                    bar_x = sprite_rect.centerx + 1 - bar_total_width // 2
                    bar_y = sprite_rect.bottom + 4

                    bar_current_width = int(bar_total_width * (current_hp / max_hp))

                    pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_total_width, bar_h))
                    pygame.draw.rect(surface, getattr(character, 'hp_color', (0, 200, 0)), 
                                   (bar_x, bar_y, bar_current_width, bar_h))
            except Exception as e:
                logger.warning(f"Error drawing HP bar for character {i}: {e}")

    def _draw_stats(self, surface):
        """Dibuja la seccion de estadísticas con validacion"""
        pygame.draw.rect(surface, (0, 0, 0), self.stats_area)
        pygame.draw.rect(surface, (255, 255, 255), self.stats_area, 1)
        
        character = self.get_current_character()
        if not character:
            no_char_surf = self.font.render("No char", True, (150, 150, 150))
            surface.blit(no_char_surf, (self.stats_area.x + 2, self.stats_area.y + 15))
            return
        
        try:
            stats = character.total_stats()
            y_offset = 2
            stat_items = [
                ("ATK", stats.get("attack", 0)), 
                ("DEF", stats.get("defense", 0)),
                ("HP", f"{character.current_hp}/{character.get_max_hp()}")
            ]
            
            for stat_name, value in stat_items:
                stat_text = f"{stat_name}:{value}"
                stat_surf = self.font.render(stat_text, True, (255, 255, 255))
                surface.blit(stat_surf, (self.stats_area.x + 2, self.stats_area.y + y_offset))
                y_offset += 12
                
        except Exception as e:
            logger.error(f"Error drawing stats: {e}")
            error_surf = self.font.render("Stats Error", True, (255, 0, 0))
            surface.blit(error_surf, (self.stats_area.x + 2, self.stats_area.y + 15))

    def _draw_skills(self, surface):
        """Dibuja la seccion de habilidades"""
        pygame.draw.rect(surface, (0, 0, 0), self.skills_area)
        pygame.draw.rect(surface, (255, 255, 255), self.skills_area, 1)
        
        skills = ["BrokenSoul", "Flagger", "MechaSaber"]
        
        for i, skill in enumerate(skills):
            y = self.skills_area.y + 2 + i * 12
            color = (255, 255, 100) if (self.current_state == MenuState.SKILLS and 
                                      i == self.selected_skill) else (200, 200, 200)
            
            skill_surf = self.font.render(skill[:8], True, color)
            surface.blit(skill_surf, (self.skills_area.x + 2, y))

    def _draw_equipment(self, surface):
        """Dibuja la seccion de equipamiento con validacion"""
        pygame.draw.rect(surface, (0, 0, 0), self.equipment_area)
        pygame.draw.rect(surface, (255, 255, 255), self.equipment_area, 1)
        
        character = self.get_current_character()
        if not character:
            no_char_surf = self.font.render("No char", True, (150, 150, 150))
            surface.blit(no_char_surf, (self.equipment_area.x + 2, self.equipment_area.y + 35))
            return
        
        try:
            # Items equipados del personaje actual
            equipment_items = [
                ("Weapon", getattr(character.equipment.weapon, 'name', 'None') if character.equipment.weapon else 'None'),
                ("Armor1", character.equipment.armors[0].name if len(character.equipment.armors) > 0 else 'None'),
                ("Armor2", character.equipment.armors[1].name if len(character.equipment.armors) > 1 else 'None')
            ]
            
            for i, (slot, item_name) in enumerate(equipment_items):
                y = self.equipment_area.y + 2 + i * 18
                
                # Highlight si está en modo equipamiento y seleccionado
                if (self.current_state == MenuState.EQUIPMENT and i == self.selected_equipment):
                    highlight_rect = pygame.Rect(self.equipment_area.x + 1, y, 
                                               self.equipment_area.width - 3, 15)
                    pygame.draw.rect(surface, (11, 142, 182), highlight_rect)
                
                # Icono del slot
                icon_color = (255, 200, 100) if item_name != 'None' else (255, 255, 255)
                icon_rect = pygame.Rect(self.equipment_area.x + 2, y + 2, 10, 10)
                pygame.draw.rect(surface, icon_color, icon_rect)
                
                # Nombre del item (truncado)
                item_display = item_name[:8] if len(item_name) > 8 else item_name
                item_surf = self.font.render(item_display, True, (255, 255, 255))
                surface.blit(item_surf, (self.equipment_area.x + 15, y))
                
        except Exception as e:
            logger.error(f"Error drawing equipment: {e}")
            error_surf = self.font.render("Equip Error", True, (255, 0, 0))
            surface.blit(error_surf, (self.equipment_area.x + 2, self.equipment_area.y + 35))

    def _draw_selection_area(self, surface):
        """Dibuja el área de seleccion con validacion"""
        pygame.draw.rect(surface, (0, 0, 0), self.selection_area)
        pygame.draw.rect(surface, (255, 255, 255), self.selection_area, 1)

        character = self.get_current_character()
        if not character:
            return

        try:
            if self.current_state == MenuState.INVENTORY_SELECT:
                available_items = self.inventory_model.get_available_items_for_slot(
                    character, self.selected_equipment
                )
                
                if not available_items:
                    self.current_state = MenuState.EQUIPMENT
                    return
                
                # Mostrar lista de items disponibles
                y_offset = 2
                items_to_show = available_items[:7]  # Máximo 7 items
                
                for i, item in enumerate(items_to_show):
                    y = self.selection_area.y + y_offset + i * 12
                    
                    # Highlight del item seleccionado
                    if i == self.selected_inventory_item:
                        pygame.draw.rect(surface, (11, 142, 182),
                                       (self.selection_area.x, y,
                                        self.selection_area.width, 11))
                    
                    # Mostrar nombre y cantidad
                    qty = character.inventory.quantity(item)
                    txt = f"{item.name[:6]} x{qty}"
                    surf = self.font.render(txt, True, (255, 255, 255))
                    surface.blit(surf, (self.selection_area.x + 2, y))

            elif self.current_state == MenuState.EQUIPMENT:
                # Mostrar preview de items disponibles
                available_items = self.inventory_model.get_available_items_for_slot(
                    character, self.selected_equipment
                )
                
                y = self.selection_area.y + 5
                if not available_items:
                    no_surf = self.font.render("No items", True, (200, 50, 50))
                    surface.blit(no_surf, (self.selection_area.x + 2, y))
                else:
                    # Mostrar hasta 5 ítems con su cantidad
                    items_to_show = available_items[:5]
                    for item in items_to_show:
                        qty = character.inventory.quantity(item)
                        txt = f"{item.name[:6]} x{qty}"
                        surf = self.font.render(txt, True, (200, 200, 200))
                        surface.blit(surf, (self.selection_area.x + 2, y))
                        y += self.font.get_height() + 2

            else:
                # Mostrar instrucciones para otros estados
                instructions = {
                    MenuState.CHARACTER_SELECT: "←→:Sel ↓:Eq S:Skill",
                    MenuState.SKILLS: "↑↓:Sel ↑:Back ESC:Exit"
                }
                instr = instructions.get(self.current_state, "")
                if instr:
                    inst_surf = self.font.render(instr, True, (200, 200, 100))
                    surface.blit(inst_surf, (self.selection_area.x + 2, self.selection_area.y + 5))
                    
        except Exception as e:
            logger.error(f"Error drawing selection area: {e}")
            error_surf = self.font.render("Select Error", True, (255, 0, 0))
            surface.blit(error_surf, (self.selection_area.x + 2, self.selection_area.y + 35))

    def update_party_reference(self, new_party_list: List[Character]):
        """Actualiza la referencia a la lista del party"""
        self.party = new_party_list if new_party_list else []
        self.inventory_model = InventoryModel(self.party)
        self._validate_selections()
        logger.debug(f"Party reference updated with {len(self.party)} characters")