import sys
import os
import pygame
import pygame_gui

from scripts.utils import load_images
from ui.gui import EditorGUI
from scripts.editor import Editor 
from scripts.game import Game
from scripts.actions import AssetActions

class NumiEngine:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Numi Engine")
        
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        
        self.font = pygame.font.Font('data/fonts/Caveat/static/Caveat-Bold.ttf', 18)
        
        theme_path = 'data/themes/dark_theme.json'
        if not os.path.exists(theme_path): theme_path = None
            
        self.ui_manager = pygame_gui.UIManager((self.screen_width, self.screen_height), theme_path)
        self.gui = EditorGUI(self.ui_manager, self.screen_width, self.screen_height)

        self.zoom = 2
        self.engine_mode = "EDITOR"
        self.update_viewport(self.engine_mode)

        self.tiles_base_path = 'data/images/tiles'
        self.folder_names = sorted(os.listdir(self.tiles_base_path))
        
        self.assets = {}
        for folder in self.folder_names:
            self.assets[folder] = load_images('tiles/' + folder)
            
        self.browser_mode = "folders" 
        self.current_folder = None    
        self.tile_variant = 0         
        self.browser_rects = []       
        self.selected_item = None 

        self.editor_core = Editor(self.assets)
        self.game_core = None
        self.actions = AssetActions(self)

    def update_viewport(self, mode):
        if mode == "EDITOR":
            self.virtual_width = (self.screen_width - 250) // self.zoom
            self.virtual_height = (self.screen_height - 240) // self.zoom
            self.scene_rect = pygame.Rect(250, 40, self.virtual_width * self.zoom, self.virtual_height * self.zoom)
        elif mode == "PLAY":
            self.virtual_width = self.screen_width // self.zoom
            self.virtual_height = (self.screen_height - 40) // self.zoom
            self.scene_rect = pygame.Rect(0, 40, self.virtual_width * self.zoom, self.virtual_height * self.zoom)
            
        self.display = pygame.Surface((self.virtual_width, self.virtual_height))
    
    def run(self):
        while True:
            time_delta = self.clock.tick(60) / 1000.0 
            events = pygame.event.get()
            
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                
                if event.type == pygame.VIDEORESIZE:
                    self.screen_width, self.screen_height = event.size
                    self.ui_manager.set_window_resolution((self.screen_width, self.screen_height))
                    self.gui.rebuild(self.screen_width, self.screen_height)
                    self.update_viewport(self.engine_mode)

                self.ui_manager.process_events(event)
                
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.gui.btn_save:
                        self.editor_core.tilemap.save('map.json')
                    elif event.ui_element == self.gui.btn_back:
                        self.browser_mode = "folders"
                        self.current_folder = None
                        self.gui.set_browser_title("PROJECT ASSETS")
                        self.gui.hide_back_btn()
                    elif event.ui_element == self.gui.btn_play:
                        if self.engine_mode == "EDITOR":
                            self.engine_mode = "PLAY"
                            self.gui.btn_play.set_text("■ STOP")
                            self.gui.hide_panels()
                            self.update_viewport("PLAY")
                            self.game_core = Game(self.assets, self.virtual_width, self.virtual_height)
                        else:
                            self.engine_mode = "EDITOR"
                            self.gui.btn_play.set_text("▶ PLAY")
                            self.gui.show_panels()
                            self.update_viewport("EDITOR")
                            self.game_core = None

                    elif event.ui_element == self.gui.btn_new_folder: self.actions.create_folder()
                    elif event.ui_element == self.gui.btn_add_file: self.actions.import_tile_image()
                    elif event.ui_element == self.gui.btn_delete: self.actions.delete_selected()
                    elif event.ui_element == self.gui.btn_rename: self.actions.rename_selected()
                        
                if self.engine_mode == "EDITOR":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            if not self.gui.context_menu.rect.collidepoint(event.pos):
                                self.gui.context_menu.hide()
                            for item in self.browser_rects:
                                if item['rect'].collidepoint(event.pos):
                                    if item['type'] == 'folder':
                                        self.current_folder = item['name']
                                        self.browser_mode = "files"
                                        self.gui.set_browser_title("ASSETS > " + self.current_folder.upper())
                                        self.gui.show_back_btn()
                                    elif item['type'] == 'file': self.tile_variant = item['index']
                        elif event.button == 3:
                            for item in self.browser_rects:
                                if item['rect'].collidepoint(event.pos):
                                    self.selected_item = item
                                    self.gui.context_menu.set_relative_position(event.pos)
                                    self.gui.context_menu.show()
                                
            self.ui_manager.update(time_delta)
            
            mpos = pygame.mouse.get_pos()
            is_hovering_map = self.scene_rect.collidepoint(mpos)
            mpos_virtual = ((mpos[0] - self.scene_rect.x) / self.zoom, (mpos[1] - self.scene_rect.y) / self.zoom)
            
            if self.engine_mode == "EDITOR":
                self.editor_core.update(events, mpos_virtual, self.current_folder, self.tile_variant, is_hovering_map)
            elif self.engine_mode == "PLAY":
                self.game_core.update(events)

            self.screen.fill((30, 30, 30)) 
            self.display.fill((0, 0, 0))
            
            if self.engine_mode == "EDITOR":
                self.editor_core.draw(self.display, mpos_virtual, self.current_folder, self.tile_variant, is_hovering_map)
            elif self.engine_mode == "PLAY":
                self.game_core.draw(self.display)
            
            scaled_display = pygame.transform.scale(self.display, (self.scene_rect.width, self.scene_rect.height))
            self.screen.blit(scaled_display, (self.scene_rect.x, self.scene_rect.y))
            self.ui_manager.draw_ui(self.screen)
            
            self.browser_rects.clear()
            if self.engine_mode == "EDITOR":
                y_base = self.screen_height - 160
                if self.browser_mode == "folders":
                    x_offset = 270
                    for folder_name in self.folder_names:
                        folder_rect = pygame.Rect(x_offset, y_base, 70, 60)
                        pygame.draw.rect(self.screen, (60, 60, 60), folder_rect, border_radius=10)
                        text_surf = self.font.render(folder_name, True, (220, 220, 220))
                        text_rect = text_surf.get_rect(centerx=folder_rect.centerx, top=folder_rect.bottom + 5)
                        self.screen.blit(text_surf, text_rect)
                        self.browser_rects.append({'rect': folder_rect, 'type': 'folder', 'name': folder_name})
                        x_offset += 90
                elif self.browser_mode == "files" and self.current_folder:
                    x_offset = 270 
                    for index, img in enumerate(self.assets.get(self.current_folder, [])):
                        scaled_img = pygame.transform.scale(img, (img.get_width() * 3, img.get_height() * 3))
                        img_rect = scaled_img.get_rect(topleft=(x_offset, y_base))
                        self.screen.blit(scaled_img, img_rect)
                        if index == self.tile_variant: pygame.draw.rect(self.screen, (0, 120, 215), img_rect, 2)
                        self.browser_rects.append({'rect': img_rect, 'type': 'file', 'index': index})
                        x_offset += 60 
            
            pygame.display.update()

if __name__ == "__main__":
    NumiEngine().run()