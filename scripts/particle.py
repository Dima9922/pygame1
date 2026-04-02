import random

class Particle:
    def __init__(self, game, p_type, pos, velocity=[0, 0], frame=0):
        self.game = game
        self.type = p_type
        self.pos = list(pos)
        self.velocity = list(velocity)
        
        self.animation = None 
        
        # РОЗУМНИЙ І БЕЗПЕЧНИЙ ПОШУК
        if p_type in self.game.assets:
            self.animation = self.game.assets[p_type].copy()
        elif 'particle/' + p_type in self.game.assets:
            self.animation = self.game.assets['particle/' + p_type].copy()
        elif 'particle/particle' in self.game.assets:
            self.animation = self.game.assets['particle/particle'].copy()
        
        if self.animation:
            # НАЙГОЛОВНІШИЙ ФІКС: Примусово забороняємо зациклення!
            # Тепер будь-який ефект буде грати рівно один раз і зникати.
            self.animation.loop = False 
            
            # Обчислюємо максимальну довжину анімації
            max_frame = max(0, len(self.animation.images) * self.animation.img_duration - 1)
            
            if frame == 'random':
                # Даємо легкий випадковий зсув на старті (від 0 до 7), як було в оригіналі,
                # щоб частинки не пульсували занадто синхронно, але не виходили за межі кадрів.
                self.animation.frame = random.randint(0, min(7, max_frame))
            else:
                self.animation.frame = min(frame, max_frame)
            
    def update(self):
        if not self.animation:
            return True 
            
        kill = False
        # Завдяки loop=False, animation.done нарешті стане True!
        if self.animation.done:
            kill = True
        
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        
        self.animation.update()
        
        return kill
    
    def render(self, surf, offset=(0, 0)):
        if self.animation:
            img = self.animation.img()
            surf.blit(img, (self.pos[0] - offset[0] - img.get_width() // 2, self.pos[1] - offset[1] - img.get_height() // 2))