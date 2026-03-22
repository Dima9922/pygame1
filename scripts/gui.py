import pygame
import pygame_gui

class EditorGUI:
    def __init__(self, manager, width, height):
        self.manager = manager
        
        # --- 1. ВЕРХНЯ ПАНЕЛЬ ---
        self.top_bar = pygame_gui.elements.UIPanel(
            relative_rect = pygame.Rect((0, 0), (width, 40)),
            starting_height = 1,
            manager = self.manager
        )
        
        self.btn_save = pygame_gui.elements.UIButton(
            relative_rect = pygame.Rect((10, 5), (100, 30)),
            text = 'Save Map',
            manager = self.manager,
            container = self.top_bar
        )
        
        self.btn_play = pygame_gui.elements.UIButton(
            relative_rect = pygame.Rect((120, 5), (80, 30)),
            text = '▶ PLAY',
            manager = self.manager,
            container = self.top_bar
        )

        # --- 2. ЛІВА ПАНЕЛЬ (Інструменти) ---
        self.left_panel = pygame_gui.elements.UIPanel(
            relative_rect = pygame.Rect((0, 40), (250, height - 40)),
            starting_height = 1,
            manager = self.manager
        )
        
        self.label_tools = pygame_gui.elements.UILabel(
            relative_rect = pygame.Rect((10, 10), (200, 30)),
            text = 'FUNCTION LIST',
            manager = self.manager,
            container = self.left_panel
        )

        # --- 3. НИЖНЯ ПАНЕЛЬ (Браузер асетів) ---
        self.bottom_panel = pygame_gui.elements.UIPanel(
            relative_rect = pygame.Rect((250, height - 200), (width - 250, 200)),
            starting_height = 1,
            manager = self.manager
        )

        self.label_current_category = pygame_gui.elements.UILabel(
            relative_rect = pygame.Rect((10, 10), (300, 30)),
            text = "PROJECT ASSETS",
            manager = self.manager,
            container = self.bottom_panel
        )
        
        # Кнопка НАЗАД (спочатку схована)
        self.btn_back = pygame_gui.elements.UIButton(
            relative_rect = pygame.Rect((10, 45), (80, 30)),
            text = '< BACK',
            manager = self.manager,
            container = self.bottom_panel,
            visible = False 
        )

    # --- ЗРУЧНІ ФУНКЦІЇ ДЛЯ КЕРУВАННЯ ІНТЕРФЕЙСОМ ---
    def set_browser_title(self, text):
        self.label_current_category.set_text(text)
        
    def show_back_btn(self):
        self.btn_back.show()
        
    def hide_back_btn(self):
        self.btn_back.hide()