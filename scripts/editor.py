import os
import json
import pygame
from scripts.tilemap import Tilemap

class Editor:
    def __init__(self, assets):
        self.assets = assets
        self.movement = [False, False, False, False]
        
        # ФІКС: Завантажуємо властивості для Редактора
        self.tile_properties = {}
        if os.path.exists('data/images/tiles'):
            for folder in os.listdir('data/images/tiles'):
                prop_path = f'data/images/tiles/{folder}/properties.json'
                if os.path.exists(prop_path):
                    with open(prop_path, 'r', encoding='utf-8') as f:
                        self.tile_properties[folder] = json.load(f)
                    
        self.tilemap = Tilemap(self, tile_size = 16)
        
        try:
            self.tilemap.load('map.json')
        except FileNotFoundError:
            pass
            
        self.scroll = [0.0, 0.0]
        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ongrid = True
        
    def update(self, events, mpos_virtual, current_type, current_variant, is_hovering):
        self.scroll[0] += (self.movement[1] - self.movement[0]) * 2
        self.scroll[1] += (self.movement[3] - self.movement[2]) * 2
        
        render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
        
        tile_pos = (int((mpos_virtual[0] + render_scroll[0]) // self.tilemap.tile_size), 
                    int((mpos_virtual[1] + render_scroll[1]) // self.tilemap.tile_size))
        
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and is_hovering:
                    self.clicking = True
                    if not self.ongrid and current_type:
                        img = self.assets[current_type][current_variant]
                        pos_x = mpos_virtual[0] + render_scroll[0] - img.get_width() / 2
                        pos_y = mpos_virtual[1] + render_scroll[1] - img.get_height() / 2
                        self.tilemap.offgrid_tiles.append({'type': current_type, 'variant': current_variant, 'pos': [pos_x, pos_y]})
                if event.button == 3 and is_hovering:
                    self.right_clicking = True
                    
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.clicking = False
                if event.button == 3:
                    self.right_clicking = False
                    
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a: self.movement[0] = True
                if event.key == pygame.K_d: self.movement[1] = True
                if event.key == pygame.K_w: self.movement[2] = True
                if event.key == pygame.K_s: self.movement[3] = True
                if event.key == pygame.K_g: self.ongrid = not self.ongrid
                if event.key == pygame.K_t: self.tilemap.autotile()
                if event.key == pygame.K_o: self.tilemap.save('map.json')
                if event.key == pygame.K_LSHIFT: self.shift = True
                
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a: self.movement[0] = False
                if event.key == pygame.K_d: self.movement[1] = False
                if event.key == pygame.K_w: self.movement[2] = False
                if event.key == pygame.K_s: self.movement[3] = False
                if event.key == pygame.K_LSHIFT: self.shift = False

        if self.clicking and self.ongrid and current_type and is_hovering:
            self.tilemap.tilemap[str(tile_pos[0]) + ';' + str(tile_pos[1])] = {'type': current_type, 'variant': current_variant, 'pos': tile_pos}
            
        if self.right_clicking and is_hovering:
            tile_loc = str(tile_pos[0]) + ';' + str(tile_pos[1])
            if tile_loc in self.tilemap.tilemap:
                del self.tilemap.tilemap[tile_loc]
                
            for tile in self.tilemap.offgrid_tiles.copy():
                tile_img = self.assets[tile['type']][tile['variant']]
                tile_r = pygame.Rect(
                    tile['pos'][0] - render_scroll[0], 
                    tile['pos'][1] - render_scroll[1], 
                    tile_img.get_width(), 
                    tile_img.get_height())
                if tile_r.collidepoint(mpos_virtual):
                    self.tilemap.offgrid_tiles.remove(tile)

    def draw(self, surface, mpos_virtual, current_type, current_variant, is_hovering):
        render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
        self.tilemap.render(surface, offset = render_scroll, render_hidden=True)
        
        if current_type and is_hovering and current_type in self.assets and current_variant < len(self.assets[current_type]):
            current_tile_img = self.assets[current_type][current_variant].copy()
            current_tile_img.set_alpha(150)
            
            tile_pos = (int((mpos_virtual[0] + render_scroll[0]) // self.tilemap.tile_size), 
                        int((mpos_virtual[1] + render_scroll[1]) // self.tilemap.tile_size))

            if self.ongrid:
                surface.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - render_scroll[0], tile_pos[1] * self.tilemap.tile_size - render_scroll[1]))
            else:
                surface.blit(current_tile_img, (mpos_virtual[0] - current_tile_img.get_width() / 2, mpos_virtual[1] - current_tile_img.get_height() / 2))