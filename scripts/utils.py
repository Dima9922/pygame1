import pygame
import os
base_img_path = "data/images/"

def load_image(path):
    img = pygame.image.load(base_img_path + path).convert()
    img.set_colorkey((0, 0, 0))
    return img

def load_images(path):
    images = []
    for img_name in os.listdir(base_img_path + path):
        images.append(load_image(path + "/" + img_name))
    return images