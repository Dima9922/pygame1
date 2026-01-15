import pygame
base_img_path = "data/images/"

def load_image(path):
    img = pygame.image.load(base_img_path + path).convert()
    img.set_colorkey((0, 0, 0))
    return img