import pygame
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPainter
from scripts.editor import Editor
from scripts.game import Game

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
        self.game = None
        self.mode = "EDITOR"
        
        self.mpos = (0, 0)
        self.is_hovering = False
        self.mock_events = [] 

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_engine)
        self.timer.start(16)
        
        # ФІКС: Повернули всі клавіші управління редактором!
        self.key_mapping = {
            Qt.Key_Up: pygame.K_UP, Qt.Key_Down: pygame.K_DOWN, 
            Qt.Key_Left: pygame.K_LEFT, Qt.Key_Right: pygame.K_RIGHT,
            Qt.Key_Space: pygame.K_SPACE, Qt.Key_Escape: pygame.K_ESCAPE, 
            Qt.Key_Delete: pygame.K_DELETE, Qt.Key_Shift: pygame.K_LSHIFT, 
            Qt.Key_Control: pygame.K_LCTRL,
            # Англійська розкладка
            Qt.Key_W: pygame.K_w, Qt.Key_A: pygame.K_a,
            Qt.Key_S: pygame.K_s, Qt.Key_D: pygame.K_d, Qt.Key_X: pygame.K_x,
            Qt.Key_G: pygame.K_g, Qt.Key_T: pygame.K_t, Qt.Key_O: pygame.K_o,
            # Українська розкладка (ЦФІВ + Ч, П, Е, Щ)
            1062: pygame.K_w, 1060: pygame.K_a, 
            1030: pygame.K_s, 1042: pygame.K_d, 
            1063: pygame.K_x,                   
            1055: pygame.K_g, 1045: pygame.K_t, 1065: pygame.K_o 
        }

    def set_current_tile(self, group, variant):
        self.current_tile_group = group
        self.current_tile_variant = variant
        
    def set_mode(self, new_mode):
        self.mode = new_mode
        if self.mode == "PLAY":
            current_w = max(1, self.width() // self.zoom)
            current_h = max(1, self.height() // self.zoom)
            self.display = pygame.Surface((current_w, current_h))
            self.game = Game(self.assets, current_w, current_h)
        else:
            self.game = None
            
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
        if self.mode == "EDITOR":
            current_w, current_h = max(1, self.width() // self.zoom), max(1, self.height() // self.zoom)
            if self.display.get_width() != current_w or self.display.get_height() != current_h:
                self.display = pygame.Surface((current_w, current_h))

        self.display.fill((30, 30, 30))
        mpos_virtual = (self.mpos[0] / self.zoom, self.mpos[1] / self.zoom)

        if self.mode == "EDITOR":
            self.editor.update(self.mock_events, mpos_virtual, self.current_tile_group, self.current_tile_variant, self.is_hovering)
            self.editor.draw(self.display, mpos_virtual, self.current_tile_group, self.current_tile_variant, self.is_hovering)
        elif self.mode == "PLAY" and self.game:
            self.game.update(self.mock_events)
            self.game.draw(self.display)
            
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