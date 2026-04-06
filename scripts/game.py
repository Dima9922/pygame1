import os
import sys
import math
import random
import json
import pygame

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Enemy, NPC, Collectible
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark

class Game:
    def __init__(self, assets, v_width, v_height):
        self.assets = assets.copy() 
        self.tile_properties = {}
        
        self.is_menu_mode = False
        self.is_paused = False 
        
        self.is_dialogue_active = False 
        self.dialogue_lines = []
        self.dialogue_index = 0
        self.active_npc = None
        
        # --- ІНВЕНТАР ТА ЗБЕРЕЖЕННЯ ---
        self.inventory = {'coin': 0, 'key': 0}
        self.level_start_inventory = {'coin': 0, 'key': 0} 
        
        self.ui_elements = []
        pygame.font.init()
        self.font = pygame.font.SysFont('arial', 14, bold=True)
        
        if os.path.exists('data/images/tiles'):
            for folder in os.listdir('data/images/tiles'):
                prop_path = f'data/images/tiles/{folder}/properties.json'
                if os.path.exists(prop_path):
                    with open(prop_path, 'r', encoding='utf-8') as f:
                        self.tile_properties[folder] = json.load(f)
                else:
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
        
        self.assets.update({
            'clouds': load_images('clouds'),
        })
        
        try:
            part_imgs = load_images('particles/particle')
            if part_imgs:
                self.assets['particle/particle'] = Animation(part_imgs, img_dur = 6, loop = False)
        except: pass
        
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
        
        self.loaded_sounds = {}
        try:
            self.ambience = pygame.mixer.Sound('data/sfx/ambience.wav')
            self.ambience.set_volume(0.2)
            self.ambience.play(-1)
        except: pass
        
        self.clouds = Clouds(self.assets['clouds'], count = 16)
        self.player = Player(self, (50, 50), (8, 15), anim_paths={'idle': 'player/idle'})
        self.tilemap = Tilemap(self, tile_size = 16)
        
        os.makedirs('data/maps', exist_ok=True)
        
        self.level_list = []
        map_objects = []
        
        for f_name in sorted([f for f in os.listdir('data/maps') if f.endswith('.json')]):
            try:
                with open(os.path.join('data/maps', f_name), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not data.get('ignore_in_progression', False):
                        map_objects.append({
                            'name': f_name,
                            'order': data.get('level_order', 999) 
                        })
            except: pass
            
        map_objects.sort(key=lambda x: (x['order'], x['name']))
        self.level_list = [x['name'] for x in map_objects]
        
        self.current_level_idx = 0
        self.current_map_name = None
        
        if os.path.exists('data/maps/current_play.txt'):
            with open('data/maps/current_play.txt', 'r') as f:
                self.current_map_name = f.read().strip()
                
        self.screenshake = 0
        self.level_complete = False
        
        if self.current_map_name:
            if self.current_map_name in self.level_list:
                self.current_level_idx = self.level_list.index(self.current_map_name)
            self.load_level(f"data/maps/{self.current_map_name}")
        elif self.level_list:
            self.current_map_name = self.level_list[0]
            self.load_level(f"data/maps/{self.current_map_name}")

    def resize_display(self, new_w, new_h):
        self.display = pygame.Surface((new_w, new_h), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((new_w, new_h))
        
        if not self.is_menu_mode and getattr(self.tilemap, 'bg_path', None):
            try:
                folder, variant = self.tilemap.bg_path.split('/')
                if folder in self.assets and int(variant) < len(self.assets[folder]):
                    self.bg_image = pygame.transform.scale(self.assets[folder][int(variant)], (new_w, new_h))
            except: pass

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
        if not key or not pygame.mixer.get_init(): return
        vol_percent = 60
        if entity_type and entity_type in self.tile_properties:
            vol_percent = self.tile_properties[entity_type].get('sfx_volumes', {}).get(key, 60)
            
        if key not in self.loaded_sounds:
            path = f"data/sfx/{key}" if not key.startswith("data/") else key
            if os.path.exists(path):
                try: self.loaded_sounds[key] = pygame.mixer.Sound(path)
                except: self.loaded_sounds[key] = None
            else: self.loaded_sounds[key] = None

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
        map_name = os.path.basename(map_path)
        if hasattr(self, 'level_list') and map_name in self.level_list:
            self.current_level_idx = self.level_list.index(map_name)
            self.current_map_name = map_name

        self.is_menu_mode = False
        self.is_paused = False 
        self.is_dialogue_active = False 
        self.ui_elements = []
        self.enemies = []
        self.npcs = [] 
        self.collectibles = []
        self.projectiles = []
        self.particles = []
        self.sparks = []
        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30
        self.bg_image = None
        
        try:
            with open(map_path, 'r', encoding='utf-8') as f:
                map_data = json.load(f)
                
                if map_data.get('is_menu', False):
                    self.is_menu_mode = True
                    self.ui_elements = map_data.get('ui_elements', [])
                    bg_path = map_data.get('bg_path')
                    if bg_path:
                        folder, variant = bg_path.split('/')
                        if folder in self.assets and int(variant) < len(self.assets[folder]):
                            self.bg_image = pygame.transform.scale(self.assets[folder][int(variant)], (640, 360))
                    pygame.mixer.music.stop() 
                    return 
        except FileNotFoundError: pass

        try: self.tilemap.load(map_path)
        except (FileNotFoundError, KeyError): pass
            
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
            
        if getattr(self.tilemap, 'bg_path', None):
            try:
                folder, variant = self.tilemap.bg_path.split('/')
                if folder in self.assets and int(variant) < len(self.assets[folder]):
                    self.bg_image = pygame.transform.scale(self.assets[folder][int(variant)], self.display.get_size())
            except: pass
            
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
                'die': props.get('anim_die', 'particle/particle'),
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
            elif preset == "Friendly NPC":
                self.npcs.append(NPC(
                    self, spawner['pos'], (8, 15),
                    anim_paths=anim_paths,
                    spawner_type=folder,
                    can_walk=props.get('can_walk', False),
                    speed=props.get('walk_speed', 0.5),
                    dialogue_text=props.get('dialogue_text', 'Привіт!;Як справи?'),
                    dialogue_sound=props.get('dialogue_sound', 'talk.wav')
                ))
            elif preset == "Collectible":
                self.collectibles.append(Collectible(
                    self, spawner['pos'], (16, 16),
                    anim_paths=anim_paths, # <--- ФІКС ТУТ (прибрали ['idle'])
                    c_type=props.get('col_type', 'coin'),
                    value=props.get('col_value', 1),
                    spawner_type=folder
                ))

    def update(self, events, mpos_virtual=(0,0)):
        if self.is_menu_mode:
            scale = min(self.display.get_width() / 640, self.display.get_height() / 360)
            offset_x = (self.display.get_width() - int(640 * scale)) // 2
            offset_y = (self.display.get_height() - int(360 * scale)) // 2
            
            if scale > 0:
                cmx = (mpos_virtual[0] - offset_x) / scale
                cmy = (mpos_virtual[1] - offset_y) / scale
            else:
                cmx, cmy = 0, 0
            
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for el in reversed(self.ui_elements):
                        if el['type'] in self.assets and el['variant'] < len(self.assets[el['type']]):
                            img = self.assets[el['type']][el['variant']]
                            rect = pygame.Rect(el['pos'][0], el['pos'][1], img.get_width(), img.get_height())
                            if rect.collidepoint((cmx, cmy)):
                                action = el.get('action', 'load_map')
                                if action == 'load_map':
                                    target = el.get('target', '1.json')
                                    with open('data/maps/current_play.txt', 'w') as f: f.write(target)
                                    
                                    # ОБНУЛЯЄМО МОНЕТИ ПРИ НОВІЙ ГРІ
                                    self.inventory = {'coin': 0, 'key': 0}
                                    self.level_start_inventory = {'coin': 0, 'key': 0}
                                    
                                    self.load_level(f"data/maps/{target}")
                                    return 
                                elif action == 'quit_game':
                                    import sys
                                    if 'PySide6' in sys.modules:
                                        from PySide6.QtWidgets import QApplication
                                        if QApplication.instance():
                                            QApplication.instance().quit()
                                            return
                                    pygame.quit()
                                    sys.exit()
                                elif action == 'open_url':
                                    import webbrowser
                                    webbrowser.open(el.get('target', 'http://google.com'))
                                    break 
            return

        if self.is_dialogue_active:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key in [pygame.K_e, pygame.K_RETURN, pygame.K_SPACE]:
                    self.dialogue_index += 1
                    if self.dialogue_index >= len(self.dialogue_lines):
                        self.is_dialogue_active = False 
                        self.active_npc = None
                    else:
                        if self.active_npc:
                            self.play_sound(self.active_npc.dialogue_sound, 'talk.wav')
            return 

        self.screenshake = max(0, self.screenshake - 1)
        if not self.dead and not getattr(self, 'level_complete', False):
            if hasattr(self.tilemap, 'check_level_exits') and self.tilemap.check_level_exits(self.player.rect()):
                self.level_complete = True
        
        if getattr(self, 'level_complete', False):
            self.transition += 1
            if self.transition > 30:
                self.level_start_inventory = self.inventory.copy()
                if self.level_list:
                    self.current_level_idx = (self.current_level_idx + 1) % len(self.level_list)
                    self.current_map_name = self.level_list[self.current_level_idx]
                    self.load_level(f"data/maps/{self.current_map_name}")
                self.level_complete = False
        elif self.dead:
            self.dead += 1
            if self.dead >= 10:
                self.transition = min(30, self.transition + 1)
            if self.dead > 40:
                if self.current_map_name:
                    self.inventory = self.level_start_inventory.copy()
                    self.load_level(f"data/maps/{self.current_map_name}")
        else:
            if self.transition < 0:
                self.transition += 1
        
        self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
        self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
        
        self.clouds.update()
        
        for c in self.collectibles.copy():
            c.update()
            if not self.dead and self.player.rect().colliderect(c.rect()):
                if c.type == 'coin': self.inventory['coin'] += c.value
                elif c.type == 'key': self.inventory['key'] += c.value
                
                self.play_sound(self.tile_properties.get(c.spawner_type, {}).get('sfx_hit', 'hit.wav'), 'hit.wav')
                self.collectibles.remove(c)
                
                for i in range(5):
                    self.sparks.append(Spark(c.rect().center, random.random() * math.pi * 2, 1 + random.random()))

        for npc in self.npcs:
            npc.update(self.tilemap, (0, 0))
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
                elif proj_type == 'player':
                    for enemy in self.enemies.copy():
                        if enemy.rect().collidepoint(projectile[0]):
                            if projectile in self.projectiles: self.projectiles.remove(projectile)
                            if enemy in self.enemies: self.enemies.remove(enemy)
                            self.play_sound(enemy.anim_paths.get('sfx_hit', 'hit.wav'), 'hit.wav', getattr(enemy, 'spawner_type', None))
                            self.screenshake = max(16, self.screenshake)
                            
                            death_fx = enemy.anim_paths.get('die', 'particle/particle')
                            fx_key = death_fx if death_fx in self.assets else None 
                            
                            for i in range(30):
                                angle = random.random() * math.pi * 2
                                speed = random.random() * 5
                                self.sparks.append(Spark(enemy.rect().center, angle, 2 + random.random()))
                                if fx_key:
                                    self.particles.append(Particle(self, fx_key, enemy.rect().center, velocity = [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame = 'random'))
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
                
                if event.key in [pygame.K_e, 1059]: 
                    for npc in self.npcs:
                        if npc.interactable:
                            self.is_dialogue_active = True
                            raw_lines = npc.dialogue_text.split(';')
                            self.dialogue_lines = [line.strip() for line in raw_lines if line.strip()]
                            if not self.dialogue_lines:
                                self.dialogue_lines = ["..."]
                                
                            self.dialogue_index = 0
                            self.active_npc = npc
                            self.movement = [False, False] 
                            self.play_sound(npc.dialogue_sound, 'talk.wav')
                            break
                            
            if event.type == pygame.KEYUP:
                if event.key in [pygame.K_LEFT, pygame.K_a]: self.movement[0] = False
                if event.key in [pygame.K_RIGHT, pygame.K_d]: self.movement[1] = False

    def draw(self, surface, mpos_virtual=(0,0)):
        self.display.fill((0, 0, 0, 0))
        
        if self.is_menu_mode:
            menu_surf = pygame.Surface((640, 360))
            if getattr(self, 'bg_image', None):
                menu_surf.blit(self.bg_image, (0, 0))
            else:
                menu_surf.fill((25, 25, 35)) 
            
            scale = min(self.display.get_width() / 640, self.display.get_height() / 360)
            offset_x = (self.display.get_width() - int(640 * scale)) // 2
            offset_y = (self.display.get_height() - int(360 * scale)) // 2
            
            if scale > 0:
                cmx = (mpos_virtual[0] - offset_x) / scale
                cmy = (mpos_virtual[1] - offset_y) / scale
            else:
                cmx, cmy = 0, 0
            
            for el in self.ui_elements:
                if el['type'] in self.assets and el['variant'] < len(self.assets[el['type']]):
                    img = self.assets[el['type']][el['variant']]
                    rect = pygame.Rect(el['pos'][0], el['pos'][1], img.get_width(), img.get_height())
                    
                    if rect.collidepoint((cmx, cmy)):
                        pygame.draw.rect(menu_surf, (255, 204, 0), rect.inflate(4, 4), 2, border_radius=4)
                    
                    menu_surf.blit(img, (el['pos'][0], el['pos'][1]))
                    
                    text = el.get('text', '')
                    if text:
                        text_surf = self.font.render(text, True, (255, 255, 255))
                        shadow_surf = self.font.render(text, True, (0, 0, 0))
                        text_rect = text_surf.get_rect(center=(el['pos'][0] + img.get_width()/2, el['pos'][1] + img.get_height()/2))
                        menu_surf.blit(shadow_surf, (text_rect.x + 1, text_rect.y + 1))
                        menu_surf.blit(text_surf, text_rect)
            
            scaled_w, scaled_h = int(640 * scale), int(360 * scale)
            if scaled_w > 0 and scaled_h > 0:
                scaled_menu = pygame.transform.scale(menu_surf, (scaled_w, scaled_h))
                self.display_2.fill((5, 5, 8))
                self.display_2.blit(scaled_menu, (offset_x, offset_y))
                surface.blit(self.display_2, (0, 0))
            return

        if getattr(self, 'bg_image', None): self.display_2.blit(self.bg_image, (0, 0))
        else: self.display_2.fill((30, 30, 50)) 
        
        render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
        self.clouds.render(self.display_2, offset = render_scroll)
        self.tilemap.render(self.display, offset = render_scroll)
        
        for c in self.collectibles: c.render(self.display, offset = render_scroll)
        
        for npc in self.npcs: npc.render(self.display, offset = render_scroll)
        for enemy in self.enemies: enemy.render(self.display, offset = render_scroll)
        if not self.dead: self.player.render(self.display, offset = render_scroll)
        for spark in self.sparks: spark.render(self.display, offset = render_scroll)
        for particle in self.particles: particle.render(self.display, offset = render_scroll)
        
        for projectile in self.projectiles:
            img_key = projectile[4] if len(projectile) > 4 else 'projectile.png'
            img = self.get_image(img_key, 'projectile.png')
            if img:
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
            
        display_mask = pygame.mask.from_surface(self.display)
        display_sillhouette = display_mask.to_surface(setcolor = (0, 0, 0, 180), unsetcolor = (0, 0, 0, 0))
        for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]: 
            self.display_2.blit(display_sillhouette, offset)
            
        if getattr(self, 'transition', 0):
            transition_surf = pygame.Surface(self.display.get_size())
            pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
            transition_surf.set_colorkey((255, 255, 255))
            self.display.blit(transition_surf, (0, 0))
            
        self.display_2.blit(self.display, (0, 0))
        
        screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
        surface.blit(self.display_2, screenshake_offset)

        # === ДИНАМІЧНИЙ ІНВЕНТАР З ІКОНКАМИ ===
        win_w, win_h = surface.get_size()
        scale_x = win_w / 640
        ui_font_size = max(16, int(18 * scale_x))
        ui_font = pygame.font.SysFont('arial', ui_font_size, bold=True)
        
        base_x, base_y = max(10, int(10*scale_x)), max(10, int(10*scale_x))
        current_x = base_x
        
        for item_type, amount in self.inventory.items():
            icon = None
            
            # Шукаємо налаштування для цього типу предмета
            for spawner_name, props in self.tile_properties.items():
                if props.get('preset') == 'Collectible' and props.get('col_type') == item_type:
                    # 1. ПРІОРИТЕТ: Беремо іконку з нового поля UI Icon
                    ui_path = props.get('ui_icon', '')
                    if ui_path and ui_path in self.assets:
                        asset = self.assets[ui_path]
                        icon = asset.images[0] if hasattr(asset, 'images') else asset
                    
                    # 2. ФОЛБЕК: Якщо поле порожнє, беремо анімацію спокою
                    if icon is None:
                        anim_path = props.get('anim_idle')
                        if anim_path in self.assets:
                            asset = self.assets[anim_path]
                            icon = asset.images[0] if hasattr(asset, 'images') else asset
                            
                    # 3. КРАЙНІЙ ВИПАДОК: Беремо картинку самого спавнера
                    if icon is None and spawner_name in self.assets:
                        asset = self.assets[spawner_name]
                        icon = asset[0] if isinstance(asset, list) else asset
                    break
                    
            # Малюємо, якщо знайшли хоча б якусь іконку
            if icon is not None and (amount > 0 or item_type == 'coin'):
                icon_w = int(icon.get_width() * scale_x * 1.5)
                icon_h = int(icon.get_height() * scale_x * 1.5)
                scaled_icon = pygame.transform.scale(icon, (icon_w, icon_h))
                surface.blit(scaled_icon, (current_x, base_y))
                
                text_x = current_x + icon_w + int(5 * scale_x)
                text_surf = ui_font.render(f" x {amount}", True, (255, 255, 255))
                shadow = ui_font.render(f" x {amount}", True, (0, 0, 0))
                
                surface.blit(shadow, (text_x + 2, base_y + 2))
                surface.blit(text_surf, (text_x, base_y))
                current_x = text_x + text_surf.get_width() + int(20 * scale_x)

        if self.is_paused:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))
            
            pause_ui_elements = []
            if os.path.exists('data/maps/pause.json'):
                try:
                    with open('data/maps/pause.json', 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get('is_menu', False): pause_ui_elements = data.get('ui_elements', [])
                except: pass
            
            big_font_size = max(18, int(18 * scale_x)) 
            big_font = pygame.font.SysFont('arial', big_font_size, bold=True)
            
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for el in reversed(pause_ui_elements):
                        scale_y = win_h / 360
                        folder = el['type']
                        var = el['variant']
                        if folder in self.assets and var < len(self.assets[folder]):
                            orig_img = self.assets[folder][var]
                            orig_w, orig_h = orig_img.get_size()
                            ex, ey = el['pos']
                            final_x, final_y = ex * scale_x, ey * scale_y
                            final_w, final_h = orig_w * scale_x, orig_h * scale_y
                            rect = pygame.Rect(final_x, final_y, final_w, final_h)
                            if rect.collidepoint(mpos_virtual):
                                action = el.get('action', 'resume_game')
                                if action == 'resume_game': 
                                    self.is_paused = False
                                    break
                                elif action == 'load_map':
                                    target = el.get('target', 'menu.json')
                                    with open('data/maps/current_play.txt', 'w') as f: f.write(target)
                                    self.load_level(f"data/maps/{target}")
                                    self.is_paused = False
                                    break
                                elif action == 'quit_game':
                                    import sys
                                    if 'PySide6' in sys.modules:
                                        from PySide6.QtWidgets import QApplication
                                        if QApplication.instance():
                                            QApplication.instance().quit()
                                            return
                                    pygame.quit()
                                    sys.exit()

            for el in pause_ui_elements:
                scale_y = win_h / 360
                folder = el['type']
                var = el['variant']
                ex, ey = el['pos']
                if folder in self.assets and var < len(self.assets[folder]):
                    orig_img = self.assets[folder][var]
                    orig_w, orig_h = orig_img.get_size()
                    final_x, final_y = ex * scale_x, ey * scale_y
                    final_w, final_h = int(orig_w * scale_x), int(orig_h * scale_y)
                    scaled_btn_img = pygame.transform.scale(orig_img, (final_w, final_h))
                    rect = pygame.Rect(final_x, final_y, final_w, final_h)
                    if rect.collidepoint(mpos_virtual):
                        pygame.draw.rect(surface, (255, 204, 0), rect.inflate(4*scale_x, 4*scale_y), max(2, int(2*scale_x)), border_radius=int(4*scale_x))
                    surface.blit(scaled_btn_img, (final_x, final_y))
                    text = el.get('text', '')
                    if text:
                        text_surf = big_font.render(text, True, (255, 255, 255))
                        shadow_surf = big_font.render(text, True, (0, 0, 0))
                        text_rect = text_surf.get_rect(center=(final_x + final_w/2, final_y + final_h/2))
                        surface.blit(shadow_surf, (text_rect.x + max(1, int(1*scale_x)), text_rect.y + max(1, int(1*scale_y))))
                        surface.blit(text_surf, text_rect)

        if self.is_dialogue_active and self.dialogue_index < len(self.dialogue_lines):
            scale_y = win_h / 360
            
            box_w = int(500 * scale_x)
            box_h = int(100 * scale_y)
            box_x = (win_w - box_w) // 2
            box_y = win_h - box_h - int(30 * scale_y)
            
            pygame.draw.rect(surface, (25, 25, 35), (box_x, box_y, box_w, box_h), border_radius=int(8*scale_x))
            pygame.draw.rect(surface, (255, 204, 0), (box_x, box_y, box_w, box_h), max(2, int(2*scale_x)), border_radius=int(8*scale_x))
            
            big_font_size = max(18, int(18 * scale_x))
            big_font = pygame.font.SysFont('arial', big_font_size, bold=True)
            
            current_line = self.dialogue_lines[self.dialogue_index]
            
            text_surf = big_font.render(current_line, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(box_x + box_w//2, box_y + box_h//2))
            surface.blit(text_surf, text_rect)
            
            small_font = pygame.font.SysFont('arial', max(12, int(12 * scale_x)))
            hint_surf = small_font.render("[E] Далі", True, (150, 150, 150))
            surface.blit(hint_surf, (box_x + box_w - hint_surf.get_width() - 10, box_y + box_h - hint_surf.get_height() - 5))