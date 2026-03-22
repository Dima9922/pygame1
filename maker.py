import sys
import os
import pygame
import pygame_gui
from scripts.utils import load_images
from scripts.gui import EditorGUI
from scripts.editor import Editor 
from scripts.game import Game 

class NumiEngine:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Numi Engine")
        
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.clock = pygame.time.Clock()
        
        # Підключаємо твій фірмовий шрифт
        self.font = pygame.font.Font('data/fonts/Caveat/static/Caveat-Bold.ttf', 18)
        self.ui_manager = pygame_gui.UIManager((self.screen_width, self.screen_height))
        
        self.config = {
            "bg_color": (45, 45, 45)
        }

        # --- ІНТЕРФЕЙС З ОКРЕМОГО ФАЙЛУ ---
        self.gui = EditorGUI(self.ui_manager, self.screen_width, self.screen_height)

        # --- НАЛАШТУВАННЯ В'ЮПОРТА (Ідеальний математичний прорахунок) ---
        self.zoom = 2
        self.virtual_width = (self.screen_width - 250) // self.zoom
        self.virtual_height = (self.screen_height - 240) // self.zoom
        
        self.scene_width = self.virtual_width * self.zoom
        self.scene_height = self.virtual_height * self.zoom
        
        self.scene_rect = pygame.Rect(250, 40, self.scene_width, self.scene_height)
        self.display = pygame.Surface((self.virtual_width, self.virtual_height))

        # --- ДИНАМІЧНЕ ЗАВАНТАЖЕННЯ АСЕТІВ ---
        self.tiles_base_path = 'data/images/tiles'
        self.folder_names = sorted(os.listdir(self.tiles_base_path))
        
        self.assets = {}
        for folder in self.folder_names:
            self.assets[folder] = load_images('tiles/' + folder)
            
        # --- СТАН ПРОВІДНИКА ---
        self.browser_mode = "folders" 
        self.current_folder = None    
        self.tile_variant = 0         
        self.browser_rects = []       

        # --- СИСТЕМА РЕЖИМІВ (State Machine) ---
        self.engine_mode = "EDITOR" # Може бути "EDITOR" або "PLAY"
        
        # Запускаємо ядро редактора одразу
        self.editor_core = Editor(self.assets)
        self.game_core = None

    def run(self):
        while True:
            time_delta = self.clock.tick(60) / 1000.0 
            events = pygame.event.get()
            
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
                self.ui_manager.process_events(event)
                
                # --- ОБРОБКА UI КНОПОК ---
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.gui.btn_save:
                        self.editor_core.tilemap.save('map.json') 
                        print("Карту збережено в map.json!")
                        
                    elif event.ui_element == self.gui.btn_back:
                        self.browser_mode = "folders"
                        self.current_folder = None
                        self.gui.set_browser_title("PROJECT ASSETS")
                        self.gui.hide_back_btn()
                        
                    # Перемикання між Редактором і Грою
                    elif event.ui_element == self.gui.btn_play:
                        if self.engine_mode == "EDITOR":
                            # ЗАПУСКАЄМО ГРУ
                            self.engine_mode = "PLAY"
                            self.gui.btn_play.set_text("■ STOP")
                            self.editor_core.tilemap.save('map.json') # Автозбереження перед грою
                            self.game_core = Game(self.assets, self.virtual_width, self.virtual_height) # Створюємо нову гру
                            print("Режим: ГРА")
                        else:
                            # ПОВЕРТАЄМОСЯ В РЕДАКТОР
                            self.engine_mode = "EDITOR"
                            self.gui.btn_play.set_text("▶ PLAY")
                            self.game_core = None # Видаляємо гру з пам'яті
                            print("Режим: РЕДАКТОР")
                        
                # --- ОБРОБКА МИШКИ ДЛЯ ПРОВІДНИКА (Тільки в Редакторі) ---
                if self.engine_mode == "EDITOR":
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for item in self.browser_rects:
                            if item['rect'].collidepoint(event.pos):
                                if item['type'] == 'folder':
                                    self.current_folder = item['name']
                                    self.browser_mode = "files"
                                    self.tile_variant = 0 
                                    new_title = "PROJECT ASSETS > " + self.current_folder.upper()
                                    self.gui.set_browser_title(new_title)
                                    self.gui.show_back_btn()
                                elif item['type'] == 'file':
                                    self.tile_variant = item['index']
                                
            self.ui_manager.update(time_delta)
            
            # --- ЛОГІКА МИШКИ ДЛЯ В'ЮПОРТА ---
            mpos = pygame.mouse.get_pos()
            is_hovering_map = self.scene_rect.collidepoint(mpos)
            mpos_virtual = ((mpos[0] - self.scene_rect.x) / self.zoom, (mpos[1] - self.scene_rect.y) / self.zoom)
            
            # --- ОНОВЛЕННЯ ЯДРА (Залежно від режиму) ---
            if self.engine_mode == "EDITOR":
                self.editor_core.update(events, mpos_virtual, self.current_folder, self.tile_variant, is_hovering_map)
            elif self.engine_mode == "PLAY":
                self.game_core.update(events)

            # --- ВІДМАЛЬОВКА ФОНІВ ---
            self.screen.fill(self.config["bg_color"]) 
            self.display.fill((0, 0, 0)) 
            
            # --- ВІДМАЛЬОВКА ЯДРА (Залежно від режиму) ---
            if self.engine_mode == "EDITOR":
                self.editor_core.draw(self.display, mpos_virtual, self.current_folder, self.tile_variant, is_hovering_map)
            elif self.engine_mode == "PLAY":
                self.game_core.draw(self.display)
            
            # Збільшуємо і ліпимо В'юпорт
            scaled_display = pygame.transform.scale(self.display, (self.scene_width, self.scene_height))
            self.screen.blit(scaled_display, (self.scene_rect.x, self.scene_rect.y))
            
            # Малюємо UI поверх усього
            self.ui_manager.draw_ui(self.screen)
            
            # --- ВІДМАЛЬОВКА ПРОВІДНИКА (Тільки в Редакторі) ---
            self.browser_rects.clear()
            if self.engine_mode == "EDITOR":
                y_offset = 560
                
                if self.browser_mode == "folders":
                    x_offset = 270
                    for folder_name in self.folder_names:
                        folder_rect = pygame.Rect(x_offset, y_offset, 60, 50)
                        pygame.draw.rect(self.screen, (220, 190, 70), folder_rect, border_radius = 5)
                        text_surf = self.font.render(folder_name, True, (200, 200, 200))
                        self.screen.blit(text_surf, (x_offset, y_offset + 55))
                        self.browser_rects.append({'rect': folder_rect, 'type': 'folder', 'name': folder_name})
                        x_offset += 80 
                        
                elif self.browser_mode == "files" and self.current_folder:
                    x_offset = 370 
                    images_to_draw = self.assets[self.current_folder]
                    for index, img in enumerate(images_to_draw):
                        scaled_img = pygame.transform.scale(img, (img.get_width() * 3, img.get_height() * 3))
                        img_rect = scaled_img.get_rect(topleft = (x_offset, y_offset))
                        
                        self.screen.blit(scaled_img, img_rect)
                        
                        if index == self.tile_variant:
                            pygame.draw.rect(self.screen, (255, 0, 0), img_rect, 2)
                            
                        self.browser_rects.append({'rect': img_rect, 'type': 'file', 'index': index})
                        x_offset += 60 
            
            pygame.display.update()

if __name__ == "__main__":
    NumiEngine().run()