from Settings.Settings import *
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
    
class AssetManager:
    _sprite_sheets = {}
    _images = {}

    @classmethod
    def load_spritesheet(cls, key, path, frame_width, frame_height):
        if key not in cls._sprite_sheets:
            image = pygame.image.load(path).convert_alpha()
            cls._sprite_sheets[key] = SpriteSheet(image, frame_width, frame_height)

    @classmethod
    def get_spritesheet(cls, key):
        return cls._sprite_sheets[key]

    @classmethod
    def load_image(cls, key, filepath):
        if key not in cls._images:
            cls._images[key] = pygame.image.load(filepath).convert_alpha()
        return cls._images[key]

    @classmethod
    def get_image(cls, key):
        return cls._images.get(key)