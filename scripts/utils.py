import os
import pygame

BASE_IMG_PATH = 'data/images/'
valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')

def load_image(path):
    if not path.lower().endswith(valid_extensions):
        return None
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0, 0, 0))
    return img

def load_images(path):
    images = []
    files = [f for f in sorted(os.listdir(BASE_IMG_PATH + path)) if f.lower().endswith(valid_extensions)]
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
        return self.images[int(self.frame / self.img_duration)]