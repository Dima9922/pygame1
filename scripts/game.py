import os
import sys
import math
import random
import json
import pygame

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Enemy
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark

class Game:
    def __init__(self, assets, v_width, v_height):
        self.assets = assets.copy() 
        self.tile_properties = {}
        
        # Завантаження властивостей тайлів
        if os.path.exists('data/images/tiles'):
            for folder in os.listdir('data/images/tiles'):
                prop_path = f'data/images/tiles/{folder}/properties.json'
                if os.path.exists(prop_path):
                    with open(prop_path, 'r', encoding='utf-8') as f:
                        self.tile_properties[folder] = json.load(f)
                else:
                    # Дефолтні налаштування, якщо json відсутній
                    if folder in ['spawners', 'player']:
                        self.tile_properties[folder] = {
                            "type": "Spawner", "preset": "Player", "anim_idle": "player/idle", 
                            "anim_walk": "player/run", "anim_jump": "player/jump", 
                            "anim_dash": "player/slide", "anim_wall_slide": "player/wall_slide",
                            "weapon_img": "gun.png", "projectile_img": "projectile.png",
                            "sfx_volumes": {} 
                        }
                    elif 'decor' in folder or folder == 'clouds':
                        self.tile_properties[folder] = {"type": "Static Blocks", "collision": False, "is_visible": True}
                    else:
                        self.tile_properties[folder] = {"type": "Static Blocks", "collision": True, "is_visible": True}
                
        self.display = pygame.Surface((v_width, v_height), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((v_width, v_height))
        self.movement = [False, False]
        
        # Базові ассети
        self.assets.update({
            'clouds': load_images('clouds'),
            'particle/particle': Animation(load_images('particles/particle'), img_dur = 6, loop = False),
        })
        
        # Динамічне завантаження сутностей
        entities_base_path = 'data/images/entities'
        if os.path.exists(entities_base_path):
            for ent in os.listdir(entities_base_path):
                full_ent_path = os.path.join(entities_base_path, ent)
                if os.path.isdir(full_ent_path):
                    for action in os.listdir(full_ent_path):
                        action_path = os.path.join(full_ent_path, action)
                        if os.path.isdir(action_path):
                            img_dur = 4 if action in ['run', 'walk', 'slide'] else 6
                            rel_path = f'entities/{ent}/{action}'
                            self.assets[f'{ent}/{action}'] = Animation(load_images(rel_path), img_dur=img_dur)
                        elif action.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
                            self.assets[f'{ent}/{action}'] = load_image(f'entities/{ent}/{action}')
        
        # Аудіо система
        self.loaded_sounds = {}
        try:
            self.ambience = pygame.mixer.Sound('data/sfx/ambience.wav')
            self.ambience.set_volume(0.2)
            self.ambience.play(-1)
        except:
            pass
        
        self.clouds = Clouds(self.assets['clouds'], count = 16)
        self.player = Player(self, (50, 50), (8, 15), anim_paths={'idle': 'player/idle'})
        self.tilemap = Tilemap(self, tile_size = 16)
        
        # Система рівнів
        os.makedirs('data/maps', exist_ok=True)
        self.level_list = sorted([f for f in os.listdir('data/maps') if f.endswith('.json')])
        self.current_level_idx = 0
        
        if os.path.exists('data/maps/current_play.txt'):
            with open('data/maps/current_play.txt', 'r') as f:
                start_map = f.read().strip()
                if start_map in self.level_list:
                    self.current_level_idx = self.level_list.index(start_map)
                    
        self.screenshake = 0
        self.level_complete = False
        
        if self.level_list:
            self.load_level(f"data/maps/{self.level_list[self.current_level_idx]}")

    def get_image(self, key, fallback_key):
        if key in self.assets and self.assets[key] is not None:
            return self.assets[key]
        if isinstance(key, str) and key.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
            img = load_image(key)
            if img:
                self.assets[key] = img
                return img
            img = load_image('entities/' + key)
            if img:
                self.assets[key] = img
                return img
        return self.assets.get(fallback_key)

    def play_sound(self, key, fallback_key=None, entity_type=None):
        """Програє звук з індивідуальною гучністю з налаштувань об'єкта"""
        if not key or not pygame.mixer.get_init():
            return
            
        # Отримуємо відсоток гучності з властивостей (дефолт 60%)
        vol_percent = 60
        if entity_type and entity_type in self.tile_properties:
            vol_percent = self.tile_properties[entity_type].get('sfx_volumes', {}).get(key, 60)
            
        if key not in self.loaded_sounds:
            path = f"data/sfx/{key}" if not key.startswith("data/") else key
            if os.path.exists(path):
                try:
                    self.loaded_sounds[key] = pygame.mixer.Sound(path)
                except:
                    self.loaded_sounds[key] = None
            else:
                self.loaded_sounds[key] = None

        sound = self.loaded_sounds.get(key)
        if sound:
            sound.set_volume(vol_percent / 100.0)
            sound.play()
        elif fallback_key and fallback_key in self.loaded_sounds:
            f_sound = self.loaded_sounds[fallback_key]
            if f_sound:
                f_sound.set_volume(vol_percent / 100.0)
                f_sound.play()

    def load_level(self, map_path):
        try:
            self.tilemap.load(map_path)
        except FileNotFoundError:
            pass
            
        pygame.mixer.music.stop()
        level_music = getattr(self.tilemap, 'bg_music', None)
        if level_music:
            path = f"data/sfx/{level_music}"
            if os.path.exists(path):
                try:
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.set_volume(0.5)
                    pygame.mixer.music.play(-1)
                except: pass
        else:
            try:
                pygame.mixer.music.load('data/sounds/oofoof.mp3')
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
            except: pass
            
        self.bg_image = None
        if getattr(self.tilemap, 'bg_path', None):
            folder, variant = self.tilemap.bg_path.split('/')
            if folder in self.assets and int(variant) < len(self.assets[folder]):
                self.bg_image = pygame.transform.scale(self.assets[folder][int(variant)], self.display.get_size())
            
        self.enemies = []
        for spawner in self.tilemap.extract_spawners():
            folder = spawner['type'] 
            props = self.tile_properties.get(folder, {})
            preset = props.get('preset', 'Enemy') 
            
            anim_paths = {
                'idle': props.get('anim_idle', 'enemy/idle'),
                'run': props.get('anim_walk', 'enemy/run'),
                'jump': props.get('anim_jump', 'player/jump'),
                'slide': props.get('anim_dash', 'player/slide'),
                'wall_slide': props.get('anim_wall_slide', 'player/wall_slide'),
                'weapon_img': props.get('weapon_img', 'gun.png'),
                'projectile_img': props.get('projectile_img', 'projectile.png'),
                'sfx_hit': props.get('sfx_hit', 'hit.wav'),
                'sfx_jump': props.get('sfx_jump', 'jump.wav'),
                'sfx_dash': props.get('sfx_dash', 'dash.wav'),
                'sfx_shoot': props.get('sfx_shoot', 'shoot.wav')
            }

            if preset == "Player":
                self.player.pos = list(spawner['pos'])
                self.player.velocity = [0, 0] 
                self.player.dashing = 0
                self.player.air_time = 0
                self.player.spawner_type = folder
                self.dead = 0
                self.player.anim_paths = anim_paths
                self.player.set_action('idle') 
                self.player.speed = props.get('walk_speed', 1.0)
                self.player.jump_height = props.get('jump_height', 3)
                self.player.can_jump = props.get('can_jump', True) 
                self.player.can_wall_jump = props.get('can_wall_jump', True) 
                self.player.can_shoot = props.get('can_shoot', False)
                self.player.can_dash = props.get('can_dash', True)
                self.player.shoot_cooldown_max = props.get('shoot_cooldown', 60)
                
            elif preset == "Enemy":
                self.enemies.append(Enemy(
                    self, spawner['pos'], (8, 15),
                    anim_paths=anim_paths,
                    spawner_type=folder,
                    can_walk=props.get('can_walk', False),
                    can_shoot=props.get('can_shoot', False),
                    speed=props.get('walk_speed', 1.0),
                    shoot_cooldown_max=props.get('shoot_cooldown', 60),
                    vision_range=props.get('vision_range', 15) * 16 
                ))
            
        self.projectiles = []
        self.particles = []
        self.sparks = []
        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30

    def update(self, events):
        self.screenshake = max(0, self.screenshake - 1)
        
        if not self.dead and not getattr(self, 'level_complete', False):
            if hasattr(self.tilemap, 'check_level_exits') and self.tilemap.check_level_exits(self.player.rect()):
                self.level_complete = True
                
        if getattr(self, 'level_complete', False):
            self.transition += 1
            if self.transition > 30:
                if self.level_list:
                    self.current_level_idx = (self.current_level_idx + 1) % len(self.level_list)
                    self.load_level(f"data/maps/{self.level_list[self.current_level_idx]}")
                self.level_complete = False
        elif self.dead:
            self.dead += 1
            if self.dead >= 10:
                self.transition = min(30, self.transition + 1)
            if self.dead > 40:
                if self.level_list:
                    self.load_level(f"data/maps/{self.level_list[self.current_level_idx]}")
        else:
            if self.transition < 0:
                self.transition += 1
        
        self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
        self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
        
        self.clouds.update()
        
        for enemy in self.enemies.copy():
            kill = enemy.update(self.tilemap, (0, 0))
            if kill: self.enemies.remove(enemy)
        
        if not self.dead and not getattr(self, 'level_complete', False):
            self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
        
        for projectile in self.projectiles.copy():
            projectile[0][0] += projectile[1]
            projectile[2] += 1
            if self.tilemap.solid_check(projectile[0]):
                self.projectiles.remove(projectile)
                for i in range(4):
                    self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
            elif projectile[2] > 360:
                self.projectiles.remove(projectile)
            else:
                proj_type = projectile[3] if len(projectile) > 3 else 'enemy'
                if proj_type == 'enemy':
                    if abs(self.player.dashing) < 50:
                        if self.player.rect().collidepoint(projectile[0]):
                            self.projectiles.remove(projectile)
                            self.dead += 1
                            self.play_sound(self.player.anim_paths.get('sfx_hit', 'hit.wav'), 'hit.wav', self.player.spawner_type)
                            self.screenshake = max(16, self.screenshake)
                            for i in range(30):
                                angle = random.random() * math.pi * 2
                                speed = random.random() * 5
                                self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                                self.particles.append(Particle(self, 'particle/particle', self.player.rect().center, velocity = [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame = random.randint(0, 7)))
                
                elif proj_type == 'player':
                    for enemy in self.enemies.copy():
                        if enemy.rect().collidepoint(projectile[0]):
                            if projectile in self.projectiles: self.projectiles.remove(projectile)
                            if enemy in self.enemies: self.enemies.remove(enemy)
                            self.play_sound(enemy.anim_paths.get('sfx_hit', 'hit.wav'), 'hit.wav', enemy.spawner_type)
                            self.screenshake = max(16, self.screenshake)
                            for i in range(30):
                                angle = random.random() * math.pi * 2
                                speed = random.random() * 5
                                self.sparks.append(Spark(enemy.rect().center, angle, 2 + random.random()))
                                self.particles.append(Particle(self, 'particle/particle', enemy.rect().center, velocity = [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame = random.randint(0, 7)))
                            break 
                    
        for spark in self.sparks.copy():
            if spark.update(): self.sparks.remove(spark)
        for particle in self.particles.copy():
            if particle.update(): self.particles.remove(particle)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_LEFT, pygame.K_a]: self.movement[0] = True
                if event.key in [pygame.K_RIGHT, pygame.K_d]: self.movement[1] = True
                if event.key in [pygame.K_UP, pygame.K_w]: self.player.jump()
                if event.key == pygame.K_x: self.player.dash()
                if event.key == pygame.K_SPACE: self.player.shoot()
            if event.type == pygame.KEYUP:
                if event.key in [pygame.K_LEFT, pygame.K_a]: self.movement[0] = False
                if event.key in [pygame.K_RIGHT, pygame.K_d]: self.movement[1] = False

    def draw(self, surface):
        self.display.fill((0, 0, 0, 0))
        if getattr(self, 'bg_image', None): self.display_2.blit(self.bg_image, (0, 0))
        else: self.display_2.fill((30, 30, 50)) 
        
        render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
        self.clouds.render(self.display_2, offset = render_scroll)
        self.tilemap.render(self.display, offset = render_scroll)
        
        for enemy in self.enemies: enemy.render(self.display, offset = render_scroll)
        if not self.dead: self.player.render(self.display, offset = render_scroll)
            
        for projectile in self.projectiles:
            img_key = projectile[4] if len(projectile) > 4 else 'projectile.png'
            img = self.get_image(img_key, 'projectile.png')
            if img:
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
            
        for spark in self.sparks: spark.render(self.display, offset = render_scroll)
        for particle in self.particles: particle.render(self.display, offset = render_scroll)
            
        display_mask = pygame.mask.from_surface(self.display)
        display_sillhouette = display_mask.to_surface(setcolor = (0, 0, 0, 180), unsetcolor = (0, 0, 0, 0))
        for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]: self.display_2.blit(display_sillhouette, offset)
            
        if self.transition:
            transition_surf = pygame.Surface(self.display.get_size())
            pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
            transition_surf.set_colorkey((255, 255, 255))
            self.display.blit(transition_surf, (0, 0))
            
        self.display_2.blit(self.display, (0, 0))
        screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
        surface.blit(self.display_2, screenshake_offset)