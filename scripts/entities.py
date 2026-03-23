import math
import random
import pygame
from scripts.particle import Particle
from scripts.spark import Spark

class PhysicsEntity:
    def __init__(self, game, e_type, pos, size, anim_paths=None):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        
        self.action = ''
        self.flip = False
        
        self.anim_offset = (-3, -5) 
        
        self.anim_paths = anim_paths or {'idle': f'{e_type}/idle', 'run': f'{e_type}/run'}
        self.set_action('idle')
        
        self.last_movement = [0, 0]
    
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        if action != self.action:
            self.action = action
            
            anim_key = self.anim_paths.get(action, self.anim_paths.get('idle', ''))
            if anim_key in self.game.assets:
                self.animation = self.game.assets[anim_key].copy()
            else:
                print(f"ПОПЕРЕДЖЕННЯ: Анімацію '{anim_key}' не знайдено!")
        
    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x
        
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y
                
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True
            
        self.last_movement = movement
        
        self.velocity[1] = min(5, self.velocity[1] + 0.1)
        
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0
            
        if hasattr(self, 'animation'):
            self.animation.update()
        
    def render(self, surf, offset=(0, 0)):
        if hasattr(self, 'animation'):
            surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))
        

class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size, anim_paths=None, can_walk=True, can_shoot=True, speed=1.0, shoot_cooldown_max=60, vision_range=250):
        super().__init__(game, 'enemy', pos, size, anim_paths)
        
        self.vision_range = vision_range
        self.can_walk = can_walk
        self.can_shoot = can_shoot
        self.speed = speed  
        self.shoot_cooldown_max = shoot_cooldown_max 
        self.walking = 0
        self.shoot_cooldown = 0
        
    def update(self, tilemap, movement=(0, 0)):
        if tilemap.check_kill_zones(self.rect()):
            if self.game.sfx: self.game.sfx['hit'].play()
            for i in range(30):
                angle = random.random() * math.pi * 2
                speed = random.random() * 5
                self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                self.game.particles.append(Particle(self.game, 'particle/particle', self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
            return True
            
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
        if self.can_walk:
            if self.walking:
                if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                    if (self.collisions['right'] or self.collisions['left']):
                        self.flip = not self.flip
                    else:
                        movement = (movement[0] - self.speed if self.flip else self.speed, movement[1])
                else:
                    self.flip = not self.flip
                self.walking = max(0, self.walking - 1)
            elif random.random() < 0.01:
                self.walking = random.randint(30, 120)
        
        if self.can_shoot:
            # Оголошуємо змінну ОДРАЗУ, щоб захиститися від UnboundLocalError
            proj_img = self.anim_paths.get('projectile_img', 'projectile.png')
            
            dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
            
            if (abs(dis[1]) < 16) and (abs(dis[0]) < self.vision_range):
                if tilemap.check_line_of_sight(self.rect().center, self.game.player.rect().center):
                    if self.shoot_cooldown == 0: 
                        
                        if (self.flip and dis[0] < 0):
                            if self.game.sfx: self.game.sfx['shoot'].play()
                            self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -1.5, 0, 'enemy', proj_img])
                            for i in range(4):
                                self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random()))
                            self.shoot_cooldown = self.shoot_cooldown_max 
                            self.walking = 0 
                            
                        elif (not self.flip and dis[0] > 0):
                            if self.game.sfx: self.game.sfx['shoot'].play()
                            self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 1.5, 0, 'enemy', proj_img])
                            for i in range(4):
                                self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))
                            self.shoot_cooldown = self.shoot_cooldown_max 
                            self.walking = 0
        
        super().update(tilemap, movement=movement)
        
        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')
            
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(16, self.game.screenshake)
                if self.game.sfx: self.game.sfx['hit'].play()
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle/particle', self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random()))
                return True
            
    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)
        
        if self.can_shoot:
            weapon_key = self.anim_paths.get('weapon_img', 'gun.png')
            weapon_img = self.game.get_image(weapon_key, 'gun.png')
            
            if weapon_img:
                if self.flip:
                    surf.blit(pygame.transform.flip(weapon_img, True, False), (self.rect().centerx - 4 - weapon_img.get_width() - offset[0], self.rect().centery - offset[1]))
                else:
                    surf.blit(weapon_img, (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]))

class Player(PhysicsEntity):
    def __init__(self, game, pos, size, anim_paths=None):
        super().__init__(game, 'player', pos, size, anim_paths)
        self.air_time = 0
        self.jumps = 1
        self.wall_slide = False
        self.dashing = 0
        
        self.speed = 1.0
        self.jump_height = 3.0
        
        self.can_jump = True 
        self.can_wall_jump = True 
        self.can_shoot = False
        self.can_dash = True
        self.shoot_cooldown = 0
        self.shoot_cooldown_max = 60
    
    def update(self, tilemap, movement=(0, 0)):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
        if tilemap.check_kill_zones(self.rect()):
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)
                if self.game.sfx: self.game.sfx['hit'].play()
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle/particle', self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
            self.game.dead += 1
            
        movement = (movement[0] * self.speed, movement[1])
        
        super().update(tilemap, movement=movement)
        
        self.air_time += 1
        
        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 1
            
        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4 and self.can_wall_jump:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')
        
        if not self.wall_slide:
            if abs(self.dashing) > 50: 
                self.set_action('slide')
            elif self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')
        
        dash_p_type = self.anim_paths.get('slide', 'particle/particle')
        
        if abs(self.dashing) in {60, 50}:
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(self.game, dash_p_type, self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(Particle(self.game, dash_p_type, self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
                
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)
            
    def shoot(self):
        if self.can_shoot and self.shoot_cooldown == 0:
            proj_img = self.anim_paths.get('projectile_img', 'projectile.png')
            
            if self.game.sfx: self.game.sfx['shoot'].play()
            if self.flip:
                self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -1.5, 0, 'player', proj_img])
                for i in range(4):
                    self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random()))
            else:
                self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 1.5, 0, 'player', proj_img])
                for i in range(4):
                    self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))
            self.shoot_cooldown = self.shoot_cooldown_max 
            return True
        return False
    
    def render(self, surf, offset=(0, 0)):
        if abs(self.dashing) <= 50:
            super().render(surf, offset=offset)
            
            if self.can_shoot:
                weapon_key = self.anim_paths.get('weapon_img', 'gun.png')
                weapon_img = self.game.get_image(weapon_key, 'gun.png')
                
                if weapon_img:
                    if self.flip:
                        surf.blit(pygame.transform.flip(weapon_img, True, False), (self.rect().centerx - 4 - weapon_img.get_width() - offset[0], self.rect().centery - offset[1]))
                    else:
                        surf.blit(weapon_img, (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]))
            
    def jump(self):
        if not self.can_jump: 
            return False
            
        if self.wall_slide and self.can_wall_jump:
            jump_force_y = -float(self.jump_height) * 0.8 
            jump_force_x = float(self.jump_height) * 1.1 
            
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = jump_force_x
                self.velocity[1] = jump_force_y
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -jump_force_x
                self.velocity[1] = jump_force_y
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
                
        elif self.jumps:
            self.velocity[1] = -float(self.jump_height) 
            self.jumps -= 1
            self.air_time = 5
            return True
    
    def dash(self):
        if not self.can_dash: 
            return False
            
        if not self.dashing:
            if self.game.sfx: self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60