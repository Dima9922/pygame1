import os
import pygame

BASE_IMG_PATH = 'data/images/'
valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')

def load_image(path):
    # Спочатку перевіряємо, чи шлях вже повний (починається з data/)
    if path.startswith('data/'):
        full_path = path
    else:
        full_path = BASE_IMG_PATH + path
        
    # Якщо файлу немає, просто тихо повертаємо None (без спаму в консоль)
    if not os.path.exists(full_path):
        return None
        
    try:
        img = pygame.image.load(full_path).convert()
        img.set_colorkey((0, 0, 0))
        return img
    except Exception:
        # Тихо ігноруємо биті файли
        return None

def load_images(path):
    images = []
    full_path = BASE_IMG_PATH + path
    if not os.path.exists(full_path):
        return images
        
    files = [f for f in sorted(os.listdir(full_path)) if f.lower().endswith(valid_extensions)]
    for img_name in files:
        img = load_image(path + '/' + img_name)
        if img is not None:
            images.append(img)
    return images
    
class Animation:
    def __init__(self, images, img_dur=5, loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0
    
    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)
    
    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True
    
    def img(self):
        if not self.images: # Захист: якщо список пустий
            return None
            
        idx = int(self.frame / self.img_duration)
        idx = min(max(idx, 0), len(self.images) - 1) # Захист: не виходимо за межі
        
        return self.images[idx]