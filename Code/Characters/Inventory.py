from typing import Dict, Optional

class Item:
    def __init__(self, item_id: int, name: str, item_type: str, stats: Dict[str, int]):
        self.id = item_id
        self.name = name
        self.type = item_type  # "weapon" or "armor" or "consumable"
        self.stats = stats

class Inventory:
    def __init__(self):
        self._items: Dict[int, int] = {}  # item_id -> quantity

    def add(self, item: Item, quantity: int = 1):
        self._items[item.id] = self._items.get(item.id, 0) + quantity
    
    def get_items(self):
        """Devuelve el diccionario interno item_id -> quantity"""
        return self._items
    
    def get_item_objects(self):
        """Devuelve una lista de objetos Item que están en el inventario"""
        from Characters.ItemManager import item_manager
        items = []
        for item_id, quantity in self._items.items():
            item_obj = item_manager.get_item(item_id)
            if item_obj:
                items.append(item_obj)
        return items
    
    def remove(self, item: Item, quantity: int = 1):
        if item.id not in self._items:
            return False
        self._items[item.id] -= quantity
        if self._items[item.id] <= 0:
            del self._items[item.id]
        return True

    def quantity(self, item: Item) -> int:
        return self._items.get(item.id, 0)

class Equipment:
    def __init__(self):
        self.weapon: Optional[Item] = None
        self.armors: list[Item] = []  # max 2 armor pieces

    def equip(self, item: Item) -> bool:
        if item.type == "weapon":
            self.weapon = item
            return True
        if item.type == "armor":
            if len(self.armors) < 2:
                self.armors.append(item)
                return True
        return False

    def unequip_weapon(self):
        self.weapon = None

    def unequip_armor(self, item: Item):
        if item in self.armors:
            self.armors.remove(item)
            
class InventoryModel:
    def __init__(self, characters_list):
        self.characters_list = characters_list
        self.selected_character = 0
        self.selected_equipment = 0
        self.selected_inventory_item = 0
        self.selected_skill = 0

    def get_current_character(self):
        if 0 <= self.selected_character < len(self.characters_list):
            return self.characters_list[self.selected_character]
        return None

    def cycle_character(self, direction):
        if not self.characters_list:
            return
        self.selected_character = (self.selected_character + direction) % len(self.characters_list)

    def get_equipment_items(self):
        character = self.get_current_character()
        if not character:
            return []

        return [
            character.equipment.weapon,
            character.equipment.armors[0] if len(character.equipment.armors) > 0 else None,
            character.equipment.armors[1] if len(character.equipment.armors) > 1 else None
        ]

    def get_available_items_for_slot(self, character=None, slot_index=None):
        """Obtiene los items disponibles para un slot específico"""
        if character is None:
            character = self.get_current_character()
        if character is None:
            return []
            
        if slot_index is None:
            slot_index = self.selected_equipment

        # Obtener objetos Item del inventario
        inventory_items = character.inventory.get_item_objects()
        
        if slot_index == 0:  # Weapon
            return [item for item in inventory_items if item.type == "weapon"]
        elif slot_index == 1 or slot_index == 2:  # Armor1 o Armor2
            return [item for item in inventory_items if item.type == "armor"]
        else:
            return []

    def _find_item_by_id(self, item_id):
        character = self.get_current_character()
        if not character:
            return None

        if character.equipment.weapon and character.equipment.weapon.id == item_id:
            return character.equipment.weapon

        for armor in character.equipment.armors:
            if armor.id == item_id:
                return armor

        return self._get_item_from_global_registry(item_id)

    def _get_item_from_global_registry(self, item_id):
        from Characters.ItemManager import item_manager
        return item_manager.get_item(item_id)

    def equip_selected_item(self):
        character = self.get_current_character()
        available_items = self.get_available_items_for_slot()

        if not character or self.selected_inventory_item >= len(available_items):
            return

        item = available_items[self.selected_inventory_item]

        if self.selected_equipment == 0:  # Weapon slot
            if character.equipment.weapon:
                character.inventory.add(character.equipment.weapon)
                character.equipment.unequip_weapon()
            character.equipment.equip(item)
        else:  # Armor slots
            armor_index = self.selected_equipment - 1
            if armor_index < len(character.equipment.armors):
                character.inventory.add(character.equipment.armors[armor_index])
                character.equipment.unequip_armor(character.equipment.armors[armor_index])
            character.equipment.equip(item)

        character.inventory.remove(item)

class Character:
    def __init__(self,attack,defense,max_hp,will):
        self.inventory = Inventory()
        self.equipment = Equipment()
        self.sprite_key = None
        self.base_stats = {"attack": attack, "defense": defense, "max_hp": max_hp, "hp": max_hp, "will": will}
        self.current_hp = max_hp # vida actual independiente de los stats
        self.hp_color = self._calculate_hp_color()  # color actual de la barra de vida

    def _calculate_hp_color(self):
        hp = self.current_hp  # Usar current_hp en lugar de base_stats["hp"]
        max_hp = self.get_max_hp()
        ratio = hp / max_hp if max_hp > 0 else 0

        if ratio > 0.6:
            return (0, 200, 0)  # Verde
        elif ratio > 0.3:
            return (255, 200, 0)  # Amarillo
        else:
            return (255, 50, 50)  # Rojo
        
    def total_stats(self) -> Dict[str, int]:
        stats = self.base_stats.copy()
        # weapon bonus
        if self.equipment.weapon:
            for k, v in self.equipment.weapon.stats.items():
                stats[k] = stats.get(k, 0) + v
        # armor bonuses
        for armor in self.equipment.armors:
            for k, v in armor.stats.items():
                stats[k] = stats.get(k, 0) + v
        return stats
    
    def update_hp(self, value):  # value puede ser negativo (daño) o positivo (cura)
        self.current_hp = max(0, min(self.current_hp + value, self.get_max_hp()))
        self.hp_color = self._calculate_hp_color()

    def set_hp(self, value):  # por si queres setear directo
        self.current_hp = max(0, min(value, self.get_max_hp()))
        self.hp_color = self._calculate_hp_color()
        
    def get_max_hp(self) -> int:
        return self.total_stats().get("max_hp", 100)

    def heal(self, amount: int):
        self.current_hp = min(self.current_hp + amount, self.get_max_hp())
        self.hp_color = self._calculate_hp_color()

    def take_damage(self, amount: int):
        self.current_hp = max(self.current_hp - amount, 0)
        self.hp_color = self._calculate_hp_color()

    
# Example usage:
if __name__ == "__main__":
    # define some items
    sword = Item(1, "Espada maestra", "weapon", {"attack": 3})
    helmet = Item(2, "Armadura berserker", "armor", {"defense": 2})
    shield = Item(3, "Armadura Holografica", "armor", {"defense": 3})
    boots = Item(4, "Armadura de papel", "armor", {"defense": 1})

    # create character
    hero = Character()
    hero.inventory.add(sword)
    hero.inventory.add(helmet)
    hero.inventory.add(shield)
    hero.inventory.add(boots)

    # equip weapon and two armors
    hero.equipment.equip(sword)
    hero.equipment.equip(helmet)
    hero.equipment.equip(shield)
    # trying to equip a third armor fails
    print("Equip Boots success?", hero.equipment.equip(boots))  # False

    print("Stats:", hero.total_stats())