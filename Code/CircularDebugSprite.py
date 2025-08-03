# CircularDebugSprite.py - Objeto circular para debug del sistema de followers

import pygame
import math
from Settings.Settings import *

class CircularDebugSprite(pygame.sprite.Sprite):
    """
    Sprite circular simple para debuggear problemas de renderizado y seguimiento
    """
    
    def __init__(self, color=(255, 0, 0), radius=8, *groups):
        super().__init__(*groups)
        
        # Propiedades visuales
        self.radius = radius
        self.color = color
        
        # Crear imagen circular
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        pygame.draw.circle(self.image, (255, 255, 255), (radius, radius), radius, 2)  # Borde blanco
        
        # Posición
        self.rect = self.image.get_rect()
        self.pos = pygame.Vector2(0, 0)
        
        # Para debug de movement
        self.trail_points = []
        self.max_trail_length = 20
        
    def set_position(self, x, y):
        """Actualiza la posición del círculo"""
        self.pos.x = x
        self.pos.y = y
        self.rect.center = (int(x), int(y))
        
        # Agregar punto al trail
        self.trail_points.append(self.pos.copy())
        if len(self.trail_points) > self.max_trail_length:
            self.trail_points.pop(0)
    
    def teleport_to(self, position):
        """Teletransporta el círculo a una posición específica"""
        self.set_position(position[0], position[1])
        self.trail_points.clear()  # Limpiar trail al teletransportar
    
    def draw_trail(self, surface, camera_offset):
        """Dibuja el rastro del movimiento (útil para debug)"""
        if len(self.trail_points) < 2:
            return
            
        for i in range(1, len(self.trail_points)):
            start_pos = self.trail_points[i-1] + camera_offset
            end_pos = self.trail_points[i] + camera_offset
            
            # Alpha basado en la posición en el trail (más reciente = más opaco)
            alpha = int(255 * (i / len(self.trail_points)))
            color = (*self.color, alpha)
            
            # Dibujar línea del trail
            if 0 <= start_pos.x < surface.get_width() and 0 <= start_pos.y < surface.get_height():
                pygame.draw.line(surface, self.color[:3], start_pos, end_pos, 2)

class MovingCircle(CircularDebugSprite):
    """
    Círculo que se mueve en patrones predefinidos
    """
    
    def __init__(self, movement_type="circular", speed=50, *groups):
        # FIX: Pasar argumentos correctamente al constructor padre
        super().__init__((0, 255, 0), 10, *groups)
        
        self.movement_type = movement_type
        self.speed = speed
        
        # Variables para diferentes tipos de movimiento
        self.time = 0
        self.center_pos = pygame.Vector2(160, 120)  # Centro de la pantalla
        self.radius_movement = 30
        
    def update(self, dt):
        """Actualiza el movimiento del círculo"""
        self.time += dt
        
        if self.movement_type == "circular":
            # Movimiento circular
            angle = self.time * self.speed * 0.01
            x = self.center_pos.x + math.cos(angle) * self.radius_movement
            y = self.center_pos.y + math.sin(angle) * self.radius_movement
            self.set_position(x, y)
            
        elif self.movement_type == "horizontal":
            # Movimiento horizontal (ping-pong)
            offset = math.sin(self.time * self.speed * 0.02) * 60
            self.set_position(self.center_pos.x + offset, self.center_pos.y)
            
        elif self.movement_type == "vertical":
            # Movimiento vertical (ping-pong)
            offset = math.sin(self.time * self.speed * 0.02) * 40
            self.set_position(self.center_pos.x, self.center_pos.y + offset)
            
        elif self.movement_type == "figure8":
            # Movimiento en forma de 8
            angle = self.time * self.speed * 0.02
            x = self.center_pos.x + math.sin(angle) * 40
            y = self.center_pos.y + math.sin(angle * 2) * 25
            self.set_position(x, y)

class FollowerDebugCircle(CircularDebugSprite):
    """
    Círculo que sigue al jugador usando la misma lógica que el Follower
    """
    
    def __init__(self, target_sprite, delay_frames=20, *groups):
        # FIX: Pasar argumentos correctamente al constructor padre
        super().__init__((255, 255, 0), 6, *groups)
        
        self.target_sprite = target_sprite
        self.delay_frames = delay_frames
        
        # Historial de posiciones del objetivo
        self.target_history = []
        
        # Posición inicial igual al target
        if hasattr(target_sprite, 'rect'):
            start_pos = target_sprite.rect.center
            self.set_position(start_pos[0], start_pos[1])
    
    def update(self, dt):
        """Actualiza el seguimiento del objetivo"""
        if not self.target_sprite:
            return
            
        # Agregar posición actual del target al historial
        if hasattr(self.target_sprite, 'rect'):
            current_target_pos = pygame.Vector2(self.target_sprite.rect.center)
            self.target_history.append(current_target_pos)
            
            # Mantener solo las posiciones necesarias
            if len(self.target_history) > self.delay_frames + 5:
                self.target_history.pop(0)
            
            # Seguir la posición con delay
            if len(self.target_history) >= self.delay_frames:
                delayed_pos = self.target_history[-self.delay_frames]
                
                # Movimiento suave hacia la posición objetivo
                current_pos = pygame.Vector2(self.pos)
                target_pos = delayed_pos
                
                direction = target_pos - current_pos
                distance = direction.length()
                
                if distance > 1:  # Solo mover si hay distancia significativa
                    # Velocidad adaptativa basada en la distancia
                    speed = min(100, distance * 2)  # Más rápido si está más lejos
                    
                    if distance > 0:
                        direction = direction.normalize()
                        move = direction * speed * dt
                        
                        if move.length() > distance:
                            # Si el movimiento sería mayor que la distancia, ir directo
                            self.set_position(target_pos.x, target_pos.y)
                        else:
                            # Movimiento suave
                            new_pos = current_pos + move
                            self.set_position(new_pos.x, new_pos.y)

class DebugCircleManager:
    """
    Manager para controlar múltiples círculos de debug
    """
    
    def __init__(self, game_scene):
        self.game_scene = game_scene
        self.circles = []
        self.show_trails = True
        
    def add_moving_circle(self, movement_type="circular", speed=50):
        """Añade un círculo con movimiento automático"""
        circle = MovingCircle(movement_type, speed)
        # Añadir al grupo de sprites del mundo
        self.game_scene.world_manager.all_sprites.add(circle)
        self.circles.append(circle)
        return circle
    
    def add_follower_circle(self, target_sprite, delay_frames=20):
        """Añade un círculo que sigue a un sprite"""
        follower = FollowerDebugCircle(target_sprite, delay_frames)
        # Añadir al grupo de sprites del mundo
        self.game_scene.world_manager.all_sprites.add(follower)
        self.circles.append(follower)
        return follower
    
    def remove_all_circles(self):
        """Remueve todos los círculos de debug"""
        for circle in self.circles:
            circle.kill()  # Remueve del grupo de sprites
        self.circles.clear()
    
    def toggle_trails(self):
        """Activa/desactiva los trails de movimiento"""
        self.show_trails = not self.show_trails
    
    def draw_debug_info(self, surface, camera_offset):
        """Dibuja información de debug adicional"""
        if not self.show_trails:
            return
            
        # Dibujar trails de todos los círculos
        for circle in self.circles:
            if hasattr(circle, 'draw_trail'):
                circle.draw_trail(surface, camera_offset)
        
        # Información de debug en pantalla
        font = pygame.font.Font(None, 16)
        info_text = f"Debug Circles: {len(self.circles)} | Trails: {'ON' if self.show_trails else 'OFF'}"
        text_surf = font.render(info_text, True, (255, 255, 255))
        surface.blit(text_surf, (10, surface.get_height() - 25))

# Funciones de utilidad para integrar en el DebugMenu existente
def add_debug_circles_to_debug_menu(debug_menu):
    """
    Añade opciones de círculos de debug al menú existente
    """
    if not hasattr(debug_menu.game_scene, 'circle_manager'):
        debug_menu.game_scene.circle_manager = DebugCircleManager(debug_menu.game_scene)
    
    # Añadir nuevas opciones al menú de debug visual
    new_visual_options = [
        ("Add Moving Circle", lambda: debug_menu.game_scene.circle_manager.add_moving_circle("circular", 30)),
        ("Add Follower Circle", lambda: debug_menu._add_follower_circle()),
        ("Toggle Circle Trails", lambda: debug_menu.game_scene.circle_manager.toggle_trails()),
        ("Remove All Circles", lambda: debug_menu.game_scene.circle_manager.remove_all_circles()),
    ] + debug_menu.menu_options[debug_menu.current_category]
    
    debug_menu.menu_options[debug_menu.current_category] = new_visual_options

# Método helper para añadir al DebugMenu
def _add_follower_circle_to_debug_menu(debug_menu):
    """Añade un círculo follower que sigue al jugador"""
    if hasattr(debug_menu.game_scene, 'player') and hasattr(debug_menu.game_scene, 'circle_manager'):
        debug_menu.game_scene.circle_manager.add_follower_circle(
            debug_menu.game_scene.player, 
            delay_frames=20
        )
        print("[DEBUG] Follower circle added")

# Ejemplo de integración en GameScene
"""
Para usar estos círculos de debug en tu GameScene, añade esto en el método _init_ui():

# Inicializar manager de círculos de debug
self.circle_manager = DebugCircleManager(self)

Y en el método draw(), después del renderizado del mundo:

# Debug circles
if hasattr(self, 'circle_manager'):
    self.circle_manager.draw_debug_info(surface, self.render_system.camera_offset)
"""