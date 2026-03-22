import sys
import os
import pygame
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from scripts.utils import load_images

def main():
    app = QApplication(sys.argv)
    
    # Ініціалізація Pygame та прихований екран для коректного .convert()
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN) 
    
    # Завантаження асетів
    tiles_base_path = 'data/images/tiles'
    if not os.path.exists(tiles_base_path):
        print(f"Помилка: Шлях {tiles_base_path} не знайдено!")
        return

    folder_names = sorted(os.listdir(tiles_base_path))
    assets = {}
    for folder in folder_names:
        folder_path = os.path.join(tiles_base_path, folder)
        if os.path.isdir(folder_path):
            assets[folder] = load_images('tiles/' + folder)
    
    # Запуск головного вікна
    window = MainWindow(assets)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()