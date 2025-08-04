import pygame
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class SpriteSheet:
    def __init__(self, surface, frame_width, frame_height):
        self.sheet = surface
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.columns = self.sheet.get_width() // frame_width
        self.rows = self.sheet.get_height() // frame_height

    def get_frame(self, col, row):
        x = col * self.frame_width
        y = row * self.frame_height
        return self.sheet.subsurface((x, y, self.frame_width, self.frame_height))

    def get_row(self, row):
        return [self.get_frame(col, row) for col in range(self.columns)]

class ResourceManager:
    """Singleton para gestion centralizada de recursos del juego"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._sprite_sheets: Dict[str, SpriteSheet] = {}
            self._images: Dict[str, pygame.Surface] = {}
            self._sounds: Dict[str, pygame.mixer.Sound] = {}
            self._fonts: Dict[str, pygame.font.Font] = {}
            self._initialized = True
            logger.info("ResourceManager initialized")
    
    @classmethod
    def get_instance(cls):
        """Metodo alternativo para obtener la instancia"""
        return cls()
    
    def preload_all_resources(self, base_dir: Path):
        """Carga todos los recursos necesarios al inicio del juego"""
        try:
            self._preload_fonts(base_dir)
            self._preload_character_sprites(base_dir)
            self._preload_sounds(base_dir)
            logger.info("All resources preloaded successfully")
        except Exception as e:
            logger.error(f"Error preloading resources: {e}")
            raise
    
    def _preload_fonts(self, base_dir: Path):
        """Pre-carga las fuentes del juego"""
        font_path = base_dir / "Code" / "Assets" / "C&C Red Alert [INET].ttf"
        if font_path.exists():
            self._fonts["main_16"] = pygame.font.Font(str(font_path), 16)
            self._fonts["main_12"] = pygame.font.Font(str(font_path), 12)
            logger.debug(f"Loaded fonts from {font_path}")
        else:
            # Fallback a fuente por defecto
            self._fonts["main_16"] = pygame.font.Font(None, 16)
            self._fonts["main_12"] = pygame.font.Font(None, 12)
            logger.warning(f"Font file not found, using default font")
    
    def _preload_character_sprites(self, base_dir: Path):
        """Pre-carga los sprites de personajes"""
        sprites_dir = base_dir / "Sprites"
        character_configs = [
            ("Ely", "Ely/Ely-Walk.png", 25, 44),
            ("Koral", "Koral/Koral-Walk.png", 25, 44),
            ("Vel", "Vel/Vel-Walk.png", 25, 44),
        ]
        
        for char_name, sprite_path, width, height in character_configs:
            full_path = sprites_dir / sprite_path
            if full_path.exists():
                self.load_spritesheet(char_name, full_path, width, height)
                logger.debug(f"Loaded sprite for {char_name}")
            else:
                # Crear sprite placeholder
                placeholder = pygame.Surface((width, height))
                placeholder.fill((100, 100, 100))
                self._sprite_sheets[char_name] = SpriteSheet(placeholder, width, height)
                logger.warning(f"Sprite not found for {char_name}, using placeholder")
    
    def _preload_sounds(self, base_dir: Path):
        """Pre-carga los sonidos del juego"""
        sound_files = [
            ("default", "untitled1.wav"),
        ]
        
        for sound_name, sound_file in sound_files:
            sound_path = base_dir / sound_file
            if sound_path.exists():
                try:
                    self._sounds[sound_name] = pygame.mixer.Sound(str(sound_path))
                    logger.debug(f"Loaded sound: {sound_name}")
                except pygame.error as e:
                    logger.error(f"Error loading sound {sound_name}: {e}")
    
    def load_spritesheet(self, key: str, path: Path, frame_width: int, frame_height: int):
        """Carga una hoja de sprites"""
        if key not in self._sprite_sheets:
            try:
                image = pygame.image.load(str(path)).convert_alpha()
                self._sprite_sheets[key] = SpriteSheet(image, frame_width, frame_height)
                logger.debug(f"Loaded spritesheet: {key}")
            except pygame.error as e:
                logger.error(f"Error loading spritesheet {key}: {e}")
                # Crear placeholder
                placeholder = pygame.Surface((frame_width, frame_height))
                placeholder.fill((255, 0, 255))  # Magenta para debug
                self._sprite_sheets[key] = SpriteSheet(placeholder, frame_width, frame_height)
    
    def get_spritesheet(self, key: str) -> Optional[SpriteSheet]:
        """Obtiene una hoja de sprites"""
        return self._sprite_sheets.get(key)
    
    def load_image(self, key: str, filepath: Path) -> pygame.Surface:
        """Carga una imagen individual"""
        if key not in self._images:
            try:
                self._images[key] = pygame.image.load(str(filepath)).convert_alpha()
                logger.debug(f"Loaded image: {key}")
            except pygame.error as e:
                logger.error(f"Error loading image {key}: {e}")
                # Crear placeholder
                self._images[key] = pygame.Surface((32, 32))
                self._images[key].fill((255, 0, 255))
        return self._images[key]
    
    def get_image(self, key: str) -> Optional[pygame.Surface]:
        """Obtiene una imagen"""
        return self._images.get(key)
    
    def get_sound(self, key: str) -> Optional[pygame.mixer.Sound]:
        """Obtiene un sonido"""
        return self._sounds.get(key)
    
    def get_font(self, key: str) -> Optional[pygame.font.Font]:
        """Obtiene una fuente"""
        return self._fonts.get(key)
    
    def cleanup(self):
        """Limpia todos los recursos cargados"""
        self._sprite_sheets.clear()
        self._images.clear()
        self._sounds.clear()
        self._fonts.clear()
        logger.info("Resources cleaned up")
    
    def get_memory_usage(self) -> Dict[str, int]:
        """Obtiene informacion sobre el uso de memoria"""
        return {
            "sprite_sheets": len(self._sprite_sheets),
            "images": len(self._images),
            "sounds": len(self._sounds),
            "fonts": len(self._fonts),
        }

# Instancia global para compatibilidad con codigo existente
resource_manager = ResourceManager()