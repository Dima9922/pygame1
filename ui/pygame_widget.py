import pygame
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPainter

class NumiViewport(QWidget):
    def __init__(self, assets, parent=None):
        super().__init__(parent)
        self.assets = assets
        self.setFocusPolicy(Qt.StrongFocus)
        
        self.zoom = 2
        self.display = pygame.Surface((640, 360)) 
        
        self.current_tile_group = None
        self.current_tile_variant = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_engine)
        self.timer.start(16) 

    def set_current_tile(self, group, variant):
        self.current_tile_group = group
        self.current_tile_variant = variant

    def update_engine(self):
        self.display.fill((30, 30, 30))
        
        # Відображення вибраного тайла для тесту
        if self.current_tile_group and self.current_tile_group in self.assets:
            img = self.assets[self.current_tile_group][self.current_tile_variant]
            self.display.blit(img, (20, 20))
        
        self.update() 

    def paintEvent(self, event):
        painter = QPainter(self)
        data = pygame.image.tostring(self.display, 'RGB')
        img = QImage(data, self.display.get_width(), self.display.get_height(), QImage.Format_RGB888)
        painter.drawImage(self.rect(), img)