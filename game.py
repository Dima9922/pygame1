import sys
import pygame
from scripts.entities import PhysicsEntity
from scripts.utils import load_image, load_images
from scripts.tilemap import Tilemap

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("My Pygame Window")
        pygame.display.set_icon(pygame.image.load("data/images/1.png"))
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((1440, 900), pygame.RESIZABLE)
        
        self.display = pygame.Surface((400, 300))

        # background setup and sound
        self.bg_sound = pygame.mixer.Sound("data/sounds/oofoof.mp3")
        self.bg_sound.play()
        # player setup
        self.movement = [False, False, False, False]
        self.player = PhysicsEntity(self, "player", (100, 50), (16, 16))
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image("entities/player.png")}
        
        self.tilemap = Tilemap(self, tile_size=16)
        
    def run(self):
        while True:
            self.tilemap.render(self.display)
            
            self.player.update(self.tilemap, (self.movement[0] - self.movement[1], 0))
            self.player.render(self.display)
 
            # event
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # key presses for movement
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[0] = True
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[1] = True
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.player.velocity[1] = -3
                        
                        
                    """if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_SPACE:
                        self.bg_sound.stop() or self.bg_sound.play()"""
                      
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[0] = False
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[1] = False      
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.movement[2] = False
                    """
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_SPACE:
                        self.bg_sound.stop() or self.bg_sound.play()"""
                      
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            self.display.fill("lightblue")
            pygame.display.update()
            self.clock.tick(60)
Game().run()