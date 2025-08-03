from Characters.Inventory import Item
from typing import Dict, Optional

class ItemManager:
    """Gestor global de items del juego"""
    
    def __init__(self):
        self._items: Dict[int, Item] = {}
        self._initialize_items()
    
    def _initialize_items(self):
        """Inicializa todos los items del juego"""
        # Armas
        self.register_item(Item(1, "Espada maestra", "weapon", {"attack": 3}))
        self.register_item(Item(5, "Bastón mágico", "weapon", {"attack": 2}))
        self.register_item(Item(7, "Daga", "weapon", {"attack": 1}))
        self.register_item(Item(9, "Espada legendaria", "weapon", {"attack": 5}))
        
        # Armaduras
        self.register_item(Item(2, "Armadura berserker", "armor", {"defense": 2}))
        self.register_item(Item(3, "Armadura Holográfica", "armor", {"defense": 3}))
        self.register_item(Item(4, "Armadura de papel", "armor", {"defense": 1}))
        self.register_item(Item(6, "Túnica", "armor", {"defense": 1}))
        self.register_item(Item(8, "Capa", "armor", {"defense": 1}))
        self.register_item(Item(10, "Armadura divina", "armor", {"defense": 4}))
        
        # Consumibles (para futuro uso)
        self.register_item(Item(11, "Poción de vida", "consumable", {"hp": 50}))
        self.register_item(Item(12, "Poción de maná", "consumable", {"mp": 30}))
    
    def register_item(self, item: Item):
        """Registra un item en el manager"""
        self._items[item.id] = item
    
    def get_item(self, item_id: int) -> Optional[Item]:
        """Obtiene un item por su ID"""
        return self._items.get(item_id)
    
    def get_items_by_type(self, item_type: str) -> list[Item]:
        """Obtiene todos los items de un tipo específico"""
        return [item for item in self._items.values() if item.type == item_type]
    
    def get_all_items(self) -> Dict[int, Item]:
        """Obtiene todos los items registrados"""
        return self._items.copy()

# Instancia global del ItemManager
item_manager = ItemManager()