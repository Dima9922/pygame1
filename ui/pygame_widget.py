import pygame
import os
import json
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPainter
from scripts.editor import Editor
from scripts.game import Game
from scripts.menu_editor import MenuEditor

class NumiViewport(QWidget):
    def __init__(self, assets, parent=None):
        super().__init__(parent)
        self.assets = assets
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True) 
        
        self.zoom = 2
        self.display = pygame.Surface((640, 360)) 
        
        self.current_tile_group = None
        self.current_tile_variant = 0
        
        self.editor = Editor(self.assets) 
        self.menu_editor = MenuEditor(self.assets) 
        self.game = None
        
        self.pause_ui_elements = []
        
        self.mode = "EDITOR"
        
        self.mpos = (0, 0)
        self.is_hovering = False
        self.mock_events = [] 

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_engine)
        self.timer.start(16)
        
        self.key_mapping = {
            Qt.Key_Up: pygame.K_UP, Qt.Key_Down: pygame.K_DOWN, 
            Qt.Key_Left: pygame.K_LEFT, Qt.Key_Right: pygame.K_RIGHT,
            Qt.Key_Space: pygame.K_SPACE, Qt.Key_Escape: pygame.K_ESCAPE, 
            Qt.Key_Delete: pygame.K_DELETE, Qt.Key_Shift: pygame.K_LSHIFT, 
            Qt.Key_Control: pygame.K_LCTRL,
            Qt.Key_W: pygame.K_w, Qt.Key_A: pygame.K_a,
            Qt.Key_S: pygame.K_s, Qt.Key_D: pygame.K_d, Qt.Key_X: pygame.K_x,
            Qt.Key_E: pygame.K_e, 
            Qt.Key_G: pygame.K_g, Qt.Key_T: pygame.K_t, Qt.Key_O: pygame.K_o,
            1062: pygame.K_w, 1060: pygame.K_a, 
            1030: pygame.K_s, 1042: pygame.K_d, 
            1063: pygame.K_x,                   
            1055: pygame.K_g, 1045: pygame.K_t, 1065: pygame.K_o,
            1059: pygame.K_e  
        }

    def set_current_tile(self, group, variant):
        self.current_tile_group = group
        self.current_tile_variant = variant
        
    def set_mode(self, new_mode):
        if new_mode == "PLAY":
            if self.mode != "PAUSE":
                current_w = max(1, self.width() // self.zoom)
                current_h = max(1, self.height() // self.zoom)
                self.display = pygame.Surface((current_w, current_h))
                self.game = Game(self.assets, current_w, current_h)
                
        elif new_mode == "PAUSE":
            self.pause_ui_elements = []
            
            pause_map_name = 'pause.json'
            if os.path.exists('data/config.json'):
                try:
                    with open('data/config.json', 'r', encoding='utf-8') as f:
                        conf = json.load(f)
                        pause_map_name = conf.get('pause_map', 'pause.json')
                except: pass
                
            pause_path = f'data/maps/{pause_map_name}'
            if os.path.exists(pause_path):
                try:
                    with open(pause_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        is_pause_menu = data.get('is_menu', False)
                        # === ПРИМУСОВИЙ ЧЕК НА МЕНЮ ===
                        if data.get('ui_elements') and len(data['ui_elements']) > 0:
                            is_pause_menu = True
                        # ==============================
                        
                        if is_pause_menu:
                            self.pause_ui_elements = data.get('ui_elements', [])
                except: pass
        
        # === НАЙГОЛОВНІШИЙ ЗАГУБЛЕНИЙ РЯДОК ===
        self.mode = new_mode
        # =======================================
            
    def mouseMoveEvent(self, event):
        self.mpos = (event.position().x(), event.position().y())
        self.is_hovering = True

    def enterEvent(self, event):
        self.setFocus()
        self.is_hovering = True

    def leaveEvent(self, event):
        self.is_hovering = False

    def mousePressEvent(self, event):
        self.setFocus()
        btn = 1 if event.button() == Qt.LeftButton else (3 if event.button() == Qt.RightButton else 2)
        self.mock_events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': btn, 'pos': self.mpos}))

    def mouseReleaseEvent(self, event):
        btn = 1 if event.button() == Qt.LeftButton else (3 if event.button() == Qt.RightButton else 2)
        self.mock_events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'button': btn, 'pos': self.mpos}))

    def wheelEvent(self, event):
        y = 1 if event.angleDelta().y() > 0 else -1
        self.mock_events.append(pygame.event.Event(pygame.MOUSEWHEEL, {'y': y}))

    def _convert_key(self, qt_key):
        if qt_key in self.key_mapping:
            return self.key_mapping[qt_key]
        if Qt.Key_A <= qt_key <= Qt.Key_Z:
            return qt_key + 32 
        return None

    def keyPressEvent(self, event):
        pg_key = self._convert_key(event.key())
        if pg_key:
            self.mock_events.append(pygame.event.Event(pygame.KEYDOWN, {'key': pg_key}))

    def keyReleaseEvent(self, event):
        pg_key = self._convert_key(event.key())
        if pg_key:
            self.mock_events.append(pygame.event.Event(pygame.KEYUP, {'key': pg_key}))
            
    def update_engine(self):
        current_w = max(1, self.width() // self.zoom)
        current_h = max(1, self.height() // self.zoom)
        
        if self.display.get_width() != current_w or self.display.get_height() != current_h:
            self.display = pygame.Surface((current_w, current_h))
            if self.mode == "PLAY" and self.game:
                self.game.resize_display(current_w, current_h)

        if self.mode != "PAUSE":
            self.display.fill((30, 30, 30))
            
        mpos_virtual = (self.mpos[0] / self.zoom, self.mpos[1] / self.zoom)

        if self.mode == "EDITOR":
            self.editor.update(self.mock_events, mpos_virtual, self.current_tile_group, self.current_tile_variant, self.is_hovering)
            self.editor.draw(self.display, mpos_virtual, self.current_tile_group, self.current_tile_variant, self.is_hovering)
            
        elif self.mode == "MENU_EDITOR": 
            self.menu_editor.last_screen_w = self.display.get_width()
            self.menu_editor.last_screen_h = self.display.get_height()
            self.menu_editor.update(self.mock_events, mpos_virtual, self.current_tile_group, self.current_tile_variant, self.is_hovering)
            self.menu_editor.draw(self.display, mpos_virtual, self.current_tile_group, self.current_tile_variant, self.is_hovering)
            
            if getattr(self.menu_editor, 'selection_changed', False):
                self.menu_editor.selection_changed = False
                main_win = self.window()
                if hasattr(main_win, 'on_ui_element_selected'):
                    main_win.on_ui_element_selected()
            
        elif self.mode == "PLAY" and self.game:
            pause_triggered = False
            for event in self.mock_events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.set_mode("PAUSE")
                    pause_triggered = True
                    break
                    
            if not pause_triggered:
                self.game.update(self.mock_events, mpos_virtual)
                self.game.draw(self.display, mpos_virtual)
                
        elif self.mode == "PAUSE" and self.game:
            self.game.draw(self.display, mpos_virtual)
            
            overlay = pygame.Surface(self.display.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.display.blit(overlay, (0, 0))
            
            menu_surf = pygame.Surface((640, 360), pygame.SRCALPHA)
            scale = min(self.display.get_width() / 640, self.display.get_height() / 360)
            
            if scale > 0:
                offset_x = (self.display.get_width() - int(640 * scale)) // 2
                offset_y = (self.display.get_height() - int(360 * scale)) // 2
                cmx = (mpos_virtual[0] - offset_x) / scale
                cmy = (mpos_virtual[1] - offset_y) / scale
                
                for event in self.mock_events:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for el in self.pause_ui_elements:
                            if el['type'] in self.assets and el['variant'] < len(self.assets[el['type']]):
                                img = self.assets[el['type']][el['variant']]
                                rect = pygame.Rect(el['pos'][0], el['pos'][1], img.get_width(), img.get_height())
                                if rect.collidepoint((cmx, cmy)):
                                    action = el.get('action', 'load_map') 
                                    
                                    if action == 'resume_game':
                                        self.set_mode("PLAY")
                                        
                                    elif action == 'load_map':
                                        target = el.get('target', 'menu.json')
                                        with open('data/maps/current_play.txt', 'w') as f:
                                            f.write(target)
                                        self.game.load_level(f"data/maps/{target}")
                                        self.set_mode("PLAY") 
                                        
                                    elif action == 'quit_game':
                                        self.timer.stop()
                                        QApplication.instance().quit()
                                        return
                
                for el in self.pause_ui_elements:
                    if el['type'] in self.assets and el['variant'] < len(self.assets[el['type']]):
                        img = self.assets[el['type']][el['variant']]
                        rect = pygame.Rect(el['pos'][0], el['pos'][1], img.get_width(), img.get_height())
                        
                        if rect.collidepoint((cmx, cmy)):
                            pygame.draw.rect(menu_surf, (255, 204, 0), rect.inflate(4, 4), 2, border_radius=4)
                        
                        menu_surf.blit(img, (el['pos'][0], el['pos'][1]))
                        
                        text = el.get('text', '')
                        if text:
                            pygame.font.init()
                            font = pygame.font.SysFont('arial', 14, bold=True)
                            text_surf = font.render(text, True, (255, 255, 255))
                            shadow_surf = font.render(text, True, (0, 0, 0))
                            text_rect = text_surf.get_rect(center=(el['pos'][0] + img.get_width()/2, el['pos'][1] + img.get_height()/2))
                            menu_surf.blit(shadow_surf, (text_rect.x + 1, text_rect.y + 1))
                            menu_surf.blit(text_surf, text_rect)
                            
                scaled_w, scaled_h = int(640 * scale), int(360 * scale)
                scaled_menu = pygame.transform.scale(menu_surf, (scaled_w, scaled_h))
                self.display.blit(scaled_menu, (offset_x, offset_y))
            
        self.mock_events.clear()
        self.update() 

    def paintEvent(self, event):
        painter = QPainter(self)
        data = pygame.image.tostring(self.display, 'RGB')
        bytes_per_line = self.display.get_width() * 3
        img = QImage(data, self.display.get_width(), self.display.get_height(), bytes_per_line, QImage.Format_RGB888)
        scaled_img = img.scaled(self.size(), Qt.KeepAspectRatio, Qt.FastTransformation)
        
        x = (self.width() - scaled_img.width()) // 2
        y = (self.height() - scaled_img.height()) // 2
        
        painter.fillRect(self.rect(), Qt.black) 
        painter.drawImage(x, y, scaled_img)