
import pygame
import sys
from pathlib import Path

# Configuracion básica
pygame.init()
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

class TestFollower(pygame.sprite.Sprite):
    def __init__(self, start_pos, color, *groups):
        super().__init__(*groups)
        # Crear imagen simple
        self.image = pygame.Surface((25, 44))
        self.image.fill(color)
        
        # Posicion precisa usando Vector2
        self.pos = pygame.Vector2(start_pos)
        self.rect = self.image.get_rect(center=start_pos)
        
        # Variables para seguimiento
        self.target_pos = pygame.Vector2(start_pos)

    def follow_target(self, target_pos, dt):
        self.target_pos = pygame.Vector2(target_pos)
        
        # Movimiento suave hacia el objetivo
        direction = self.target_pos - self.pos
        distance = direction.length()
        
        if distance > 5:  # Solo moverse si está lejos
            speed = 100
            if distance > 0:
                direction = direction.normalize()
                move = direction * speed * dt
                if move.length() > distance:
                    self.pos = self.target_pos
                else:
                    self.pos += move
        
        # Actualizar rect
        self.rect.center = (int(self.pos.x), int(self.pos.y))

class TestPlayer(pygame.sprite.Sprite):
    def __init__(self, start_pos, *groups):
        super().__init__(*groups)
        # Crear imagen simple
        self.image = pygame.Surface((25, 44))
        self.image.fill((100, 150, 255))  # Azul para el player
        
        # Posicion precisa usando Vector2
        self.pos = pygame.Vector2(start_pos)
        self.rect = self.image.get_rect(center=start_pos)
        
        self.speed = 100

    def update(self, dt):
        # Input básico
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)
        
        if keys[pygame.K_LEFT]:
            direction.x = -1
        if keys[pygame.K_RIGHT]:
            direction.x = 1
        if keys[pygame.K_UP]:
            direction.y = -1
        if keys[pygame.K_DOWN]:
            direction.y = 1
            
        # Normalizar diagonal
        if direction.length() > 0:
            direction = direction.normalize()
            
        # Aplicar movimiento
        self.pos += direction * self.speed * dt
        
        # Actualizar rect
        self.rect.center = (int(self.pos.x), int(self.pos.y))

class TestAllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.camera_offset = pygame.Vector2(0, 0)

    def draw_with_camera(self, surface, target_pos):
        # Calcular offset de cámara
        screen_center_x = surface.get_width() // 2
        screen_center_y = surface.get_height() // 2
        
        self.camera_offset.x = screen_center_x - target_pos[0]
        self.camera_offset.y = screen_center_y - target_pos[1]
        
        # Renderizar cada sprite
        for sprite in self:
            # MeTODO 1: Original (con posible problema)
            # render_pos = sprite.rect.topleft + self.camera_offset
            # surface.blit(sprite.image, render_pos)
            
            # MeTODO 2: Usando posicion precisa si existe
            if hasattr(sprite, 'pos'):
                render_x = sprite.pos.x - sprite.image.get_width() // 2 + self.camera_offset.x
                render_y = sprite.pos.y - sprite.image.get_height() // 2 + self.camera_offset.y
                surface.blit(sprite.image, (render_x, render_y))
            else:
                render_pos = sprite.rect.topleft + self.camera_offset
                surface.blit(sprite.image, render_pos)

class TestGame:
    def __init__(self):
        # Crear ventana SIN SCALING
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Test Follower - Sin Scaling")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Crear sprites
        self.all_sprites = TestAllSprites()
        
        # Player en el centro
        start_pos = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        self.player = TestPlayer(start_pos, self.all_sprites)
        
        # Follower un poco atrás
        follower_pos = (start_pos[0] - 50, start_pos[1])
        self.follower = TestFollower(follower_pos, (255, 100, 100), self.all_sprites)
        
        # Historial de posiciones del player
        self.player_history = []
        
        # Font para debug
        self.font = pygame.font.Font(None, 24)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            # Eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            # Update
            self.player.update(dt)
            
            # Guardar posicion del player en historial
            self.player_history.append(self.player.pos.copy())
            if len(self.player_history) > 60:  # ~1 segundo de historial
                self.player_history.pop(0)
            
            # Hacer que el follower siga una posicion pasada
            if len(self.player_history) >= 30:  # Seguir posicion de hace ~0.5 segundos
                target_pos = self.player_history[-30]
                self.follower.follow_target(target_pos, dt)

            # Render
            self.screen.fill((50, 50, 50))
            
            # Dibujar con cámara centrada en el player
            self.all_sprites.draw_with_camera(self.screen, self.player.pos)
            
            # Debug info
            debug_text = [
                f"Player pos: {self.player.pos.x:.1f}, {self.player.pos.y:.1f}",
                f"Follower pos: {self.follower.pos.x:.1f}, {self.follower.pos.y:.1f}",
                f"Player rect: {self.player.rect.center}",
                f"Follower rect: {self.follower.rect.center}",
                f"Historia: {len(self.player_history)} frames",
                "",
                "Controles: Flechas para mover",
                "ESC para salir"
            ]
            
            for i, text in enumerate(debug_text):
                rendered = self.font.render(text, True, (255, 255, 255))
                self.screen.blit(rendered, (10, 10 + i * 25))
            
            pygame.display.flip()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = TestGame()
    game.run()