import pygame
import pygame_gui

class EditorGUI:
    def __init__(self, manager, width, height):
        self.manager = manager
        self.rebuild(width, height)

    def rebuild(self, width, height):
        """Викликається при старті та при зміні розміру вікна."""
        self.manager.clear_and_reset()

        # --- ВЕРХНЯ ПАНЕЛЬ ---
        self.top_bar = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((0, 0), (width, 40)),
            manager=self.manager,
            anchors={'top': 'top', 'bottom': 'top', 'left': 'left', 'right': 'right'}
        )
        
        self.btn_save = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 5), (100, 30)),
            text='Save Map', manager=self.manager, container=self.top_bar
        )
        
        self.btn_play = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((120, 5), (80, 30)),
            text='▶ PLAY', manager=self.manager, container=self.top_bar
        )

        # --- ЛІВА ПАНЕЛЬ ---
        self.left_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((0, 40), (250, height - 40)),
            manager=self.manager,
            anchors={'top': 'top', 'bottom': 'bottom', 'left': 'left', 'right': 'left'}
        )

        # --- НИЖНЯ ПАНЕЛЬ ---
        panel_width = width - 250
        self.bottom_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((250, height - 200), (panel_width, 200)),
            manager=self.manager,
            anchors={'top': 'bottom', 'bottom': 'bottom', 'left': 'left', 'right': 'right'}
        )

        self.label_current_category = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 10), (400, 30)),
            text="PROJECT ASSETS",
            manager=self.manager,
            container=self.bottom_panel
        )
        
        # Розрахунок позиції кнопок справа (відступ 140px від правого краю панелі)
        btn_x_pos = panel_width - 150 # Збільшимо відступ для певності

        self.btn_new_folder = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((btn_x_pos, 20), (130, 40)), # y=20, height=40
            text='+ New Folder', 
            manager=self.manager, 
            container=self.bottom_panel,
            object_id="#new_folder_btn",
            starting_height=1 # ПІДНІМАЄМО НАД ПАНЕЛЛЮ
        )

        self.btn_add_file = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((btn_x_pos, 20), (130, 40)),
            text='+ Import File', 
            manager=self.manager, 
            container=self.bottom_panel,
            visible=False,
            starting_height=1
        )
        
        self.btn_back = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 20), (80, 40)),
            text='< BACK', 
            manager=self.manager, 
            container=self.bottom_panel, 
            visible=False,
            starting_height=1
        )

        # --- КОНТЕКСТНЕ МЕНЮ ---
        self.context_menu = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((0, 0), (120, 70)),
            starting_height=10, manager=self.manager, visible=False
        )
        self.btn_rename = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((5, 5), (110, 25)), text='Rename',
            manager=self.manager, container=self.context_menu
        )
        self.btn_delete = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((5, 35), (110, 25)), text='Delete',
            manager=self.manager, container=self.context_menu
        )

    def set_browser_title(self, text):
        self.label_current_category.set_text(text)
        
    def show_back_btn(self):
        self.btn_back.show()
        self.btn_add_file.show() 
        self.btn_new_folder.hide()
        
    def hide_back_btn(self):
        self.btn_back.hide()
        self.btn_add_file.hide()
        self.btn_new_folder.show()
    
    def hide_panels(self):
        self.left_panel.hide()
        self.bottom_panel.hide()

    def show_panels(self):
        self.left_panel.show()
        self.bottom_panel.show()