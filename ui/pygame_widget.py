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
        self.setMouseTracking(True) # ВАЖЛИВО: дозволяє бачити мишку навіть без кліку
        
        self.zoom = 2
        self.display = pygame.Surface((640, 360)) 
        
        self.current_tile_group = None
        self.current_tile_variant = 0
        
        # Ініціалізуємо ядро твого редактора
        self.editor = Editor(self.assets) 
        self.game = None
        self.mode = "EDITOR"
        
        self.mpos = (0, 0)
        self.is_hovering = False
        self.mock_events = [] # Черга подій для сумісності з твоїм старим кодом

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_engine)
        self.timer.start(16)
        self.key_mapping = {
            Qt.Key_Up: pygame.K_UP, Qt.Key_Down: pygame.K_DOWN, 
            Qt.Key_Left: pygame.K_LEFT, Qt.Key_Right: pygame.K_RIGHT,
            Qt.Key_Space: pygame.K_SPACE, Qt.Key_Escape: pygame.K_ESCAPE, 
            Qt.Key_Delete: pygame.K_DELETE, Qt.Key_Shift: pygame.K_LSHIFT, 
            Qt.Key_Control: pygame.K_LCTRL,
            # ЯВНО ВКАЗУЄМО Англійську розкладку (WASD)
            Qt.Key_W: pygame.K_w, Qt.Key_A: pygame.K_a,
            Qt.Key_S: pygame.K_s, Qt.Key_D: pygame.K_d,
            # ЯВНО ВКАЗУЄМО Українську розкладку (ЦФІВ)
            1062: pygame.K_w, 1060: pygame.K_a, # Ц = W, Ф = A
            1030: pygame.K_s, 1042: pygame.K_d  # І = S, В = D
        }

    def set_mode(self, new_mode):
        self.mode = new_mode
        if self.mode == "PLAY":
            # Беремо актуальні розміри розтягнутого вікна
            current_w = max(1, self.width() // self.zoom)
            current_h = max(1, self.height() // self.zoom)
            
            # ФІКС: Оновлюємо розмір полотна, щоб камера Game рахувала центр правильно!
            self.display = pygame.Surface((current_w, current_h))
            
            # Запускаємо гру з цими ж розмірами
            self.game = Game(self.assets, current_w, current_h)
        else:
            self.game = None
            
    # --- ТРАНСЛЯЦІЯ ПОДІЙ QT У PYGAME ---
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
        # Для прокрутки (може знадобитися для камери або зміни тайлів)
        y = 1 if event.angleDelta().y() > 0 else -1
        self.mock_events.append(pygame.event.Event(pygame.MOUSEWHEEL, {'y': y}))

    def _convert_key(self, qt_key):
        """Внутрішня функція для перекладу клавіш"""
        if qt_key in self.key_mapping:
            return self.key_mapping[qt_key]
        
        # Для інших літер
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
            
    # --- ГОЛОВНИЙ ЦИКЛ РУШІЯ ---
    def update_engine(self):
        # Оновлюємо розмір поверхні ТІЛЬКИ в режимі редактора
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
        img = QImage(data, self.display.get_width(), self.display.get_height(), QImage.Format_RGB888)
        
        # МАГІЯ МАСШТАБУВАННЯ: Розтягуємо на весь екран зі збереженням пропорцій
        scaled_img = img.scaled(self.size(), Qt.KeepAspectRatio, Qt.FastTransformation)
        
        # Вираховуємо центр, щоб гра завжди була посередині
        x = (self.width() - scaled_img.width()) // 2
        y = (self.height() - scaled_img.height()) // 2
        
        painter.fillRect(self.rect(), Qt.black) # Заливаємо рамки чорним кольором
        painter.drawImage(x, y, scaled_img)     # Малюємо саму гру