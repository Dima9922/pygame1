import pygame
import json
import os

class MenuEditor:
    def __init__(self, assets):
        self.assets = assets
        self.canvas_w = 640
        self.canvas_h = 360
        self.canvas_surf = pygame.Surface((self.canvas_w, self.canvas_h)) 
        
        self.ui_elements = [] 
        self.bg_path = None
        
        self.clicking = False
        self.right_clicking = False
        
        self.selected_index = None 
        self.selection_changed = False
        self.last_screen_w = 640
        self.last_screen_h = 360
        
        pygame.font.init()
        self.font = pygame.font.SysFont('arial', 14, bold=True)
        
    def load(self, path):
        self.selected_index = None
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.ui_elements = data.get('ui_elements', [])
                self.bg_path = data.get('bg_path', None)
        else:
            self.ui_elements = []
            self.bg_path = None
            
    def save(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'is_menu': True, 'ui_elements': self.ui_elements, 'bg_path': self.bg_path}, f, indent=4)
            
    def update(self, events, mpos_virtual, current_type, current_variant, is_hovering):
        scale = min(self.last_screen_w / self.canvas_w, self.last_screen_h / self.canvas_h)
        if scale <= 0: return
        
        scaled_w = int(self.canvas_w * scale)
        scaled_h = int(self.canvas_h * scale)
        offset_x = (self.last_screen_w - scaled_w) // 2
        offset_y = (self.last_screen_h - scaled_h) // 2
        
        canvas_mpos_x = (mpos_virtual[0] - offset_x) / scale
        canvas_mpos_y = (mpos_virtual[1] - offset_y) / scale
        canvas_mpos = (canvas_mpos_x, canvas_mpos_y)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and is_hovering:
                    self.clicking = True
                    clicked_on_existing = False
                    
                    for i in range(len(self.ui_elements) - 1, -1, -1):
                        el = self.ui_elements[i]
                        if el['type'] in self.assets and el['variant'] < len(self.assets[el['type']]):
                            img = self.assets[el['type']][el['variant']]
                            rect = pygame.Rect(el['pos'][0], el['pos'][1], img.get_width(), img.get_height())
                            if rect.collidepoint(canvas_mpos):
                                self.selected_index = i
                                self.selection_changed = True
                                clicked_on_existing = True
                                break
                                
                    if not clicked_on_existing and current_type and current_type in self.assets and current_variant < len(self.assets[current_type]):
                        img = self.assets[current_type][current_variant]
                        pos_x = canvas_mpos_x - img.get_width() / 2
                        pos_y = canvas_mpos_y - img.get_height() / 2
                        
                        self.ui_elements.append({
                            'type': current_type, 
                            'variant': current_variant, 
                            'pos': [pos_x, pos_y],
                            'text': 'Button',
                            'action': 'load_map',
                            'target': '1.json'
                        })
                        self.selected_index = len(self.ui_elements) - 1
                        self.selection_changed = True
                        
                    elif not clicked_on_existing and not current_type:
                        if self.selected_index is not None:
                            self.selected_index = None
                            self.selection_changed = True

                if event.button == 3 and is_hovering:
                    self.right_clicking = True
                    
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1: self.clicking = False
                if event.button == 3: self.right_clicking = False

        if self.right_clicking and is_hovering:
            for i in range(len(self.ui_elements) - 1, -1, -1):
                el = self.ui_elements[i]
                if el['type'] in self.assets and el['variant'] < len(self.assets[el['type']]):
                    img = self.assets[el['type']][el['variant']]
                    rect = pygame.Rect(el['pos'][0], el['pos'][1], img.get_width(), img.get_height())
                    if rect.collidepoint(canvas_mpos):
                        self.ui_elements.pop(i)
                        if self.selected_index == i:
                            self.selected_index = None
                            self.selection_changed = True
                        elif self.selected_index is not None and self.selected_index > i:
                            self.selected_index -= 1
                        break

    def draw(self, surface, mpos_virtual, current_type, current_variant, is_hovering):
        self.last_screen_w = surface.get_width()
        self.last_screen_h = surface.get_height()
        
        self.canvas_surf.fill((15, 15, 20))
        if getattr(self, 'bg_path', None):
            try:
                folder, variant = self.bg_path.split('/')
                if folder in self.assets and int(variant) < len(self.assets[folder]):
                    bg_img = self.assets[folder][int(variant)]
                    bg_img = pygame.transform.scale(bg_img, (self.canvas_w, self.canvas_h))
                    self.canvas_surf.blit(bg_img, (0, 0))
            except: pass

        pygame.draw.rect(self.canvas_surf, (255, 204, 0), (0, 0, self.canvas_w, self.canvas_h), 2) 

        for i, element in enumerate(self.ui_elements):
            if element['type'] in self.assets and element['variant'] < len(self.assets[element['type']]):
                img = self.assets[element['type']][element['variant']]
                self.canvas_surf.blit(img, (element['pos'][0], element['pos'][1]))
                
                text = element.get('text', '')
                if text:
                    text_surf = self.font.render(text, True, (255, 255, 255))
                    shadow_surf = self.font.render(text, True, (0, 0, 0))
                    text_rect = text_surf.get_rect(center=(element['pos'][0] + img.get_width()/2, element['pos'][1] + img.get_height()/2))
                    self.canvas_surf.blit(shadow_surf, (text_rect.x + 1, text_rect.y + 1))
                    self.canvas_surf.blit(text_surf, text_rect)
                
                if i == self.selected_index:
                    pygame.draw.rect(self.canvas_surf, (255, 50, 50), (element['pos'][0], element['pos'][1], img.get_width(), img.get_height()), 2)
                else:
                    pygame.draw.rect(self.canvas_surf, (100, 100, 255), (element['pos'][0], element['pos'][1], img.get_width(), img.get_height()), 1)

        if current_type and is_hovering and current_type in self.assets and current_variant < len(self.assets[current_type]):
            img = self.assets[current_type][current_variant].copy()
            img.set_alpha(150)
            
            scale = min(self.last_screen_w / self.canvas_w, self.last_screen_h / self.canvas_h)
            if scale > 0:
                offset_x = (self.last_screen_w - int(self.canvas_w * scale)) // 2
                offset_y = (self.last_screen_h - int(self.canvas_h * scale)) // 2
                canvas_mpos_x = (mpos_virtual[0] - offset_x) / scale
                canvas_mpos_y = (mpos_virtual[1] - offset_y) / scale
                self.canvas_surf.blit(img, (canvas_mpos_x - img.get_width() / 2, canvas_mpos_y - img.get_height() / 2))

        scale = min(self.last_screen_w / self.canvas_w, self.last_screen_h / self.canvas_h)
        if scale > 0:
            scaled_w = int(self.canvas_w * scale)
            scaled_h = int(self.canvas_h * scale)
            scaled_canvas = pygame.transform.scale(self.canvas_surf, (scaled_w, scaled_h))
            offset_x = (self.last_screen_w - scaled_w) // 2
            offset_y = (self.last_screen_h - scaled_h) // 2
            surface.fill((5, 5, 8)) 
            surface.blit(scaled_canvas, (offset_x, offset_y))