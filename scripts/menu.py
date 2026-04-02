import pygame

class Menu:
    def __init__(self, viewport, state_manager, title, buttons, is_overlay=False):
        self.viewport = viewport
        self.state_manager = state_manager
        self.title = title
        self.buttons_data = buttons
        self.is_overlay = is_overlay
        
        # Використовуємо стандартний шрифт системи
        pygame.font.init()
        self.title_font = pygame.font.SysFont('arial', 36, bold=True)
        self.btn_font = pygame.font.SysFont('arial', 18, bold=True)
        
        # Кольори
        self.color_normal = (200, 200, 200) # Світло-сірий
        self.color_hover = (255, 204, 0)    # Жовтий
        self.color_title = (255, 255, 255)  # Білий
        
        # Плівка для паузи
        self.bg_overlay = pygame.Surface((1, 1))
        self.bg_overlay.set_alpha(180) # Рівень затемнення (0-255)
        self.bg_overlay.fill((0, 0, 0))

        self.button_rects = []
        self.update_layout()

    def update_layout(self):
        """Центрує кнопки відносно поточного розміру ігрового екрана"""
        screen_w = self.viewport.display.get_width()
        screen_h = self.viewport.display.get_height()
        
        self.bg_overlay = pygame.transform.scale(self.bg_overlay, (screen_w, screen_h))
        center_x = screen_w // 2
        
        padding = 15
        total_height = 0
        btn_surfaces = []
        
        for btn in self.buttons_data:
            text_surf = self.btn_font.render(btn["text"], True, self.color_normal)
            btn_surfaces.append(text_surf)
            total_height += text_surf.get_height() + padding
            
        total_height -= padding 
        start_y = (screen_h // 2) - (total_height // 2) + 20 
        
        self.button_rects = []
        current_y = start_y
        
        for i, text_surf in enumerate(btn_surfaces):
            rect = text_surf.get_rect(centerx=center_x, y=current_y)
            self.button_rects.append({
                "rect": rect,
                "text": self.buttons_data[i]["text"],
                "action": self.buttons_data[i]["action"]
            })
            current_y += text_surf.get_height() + padding

    def update(self, events, mpos):
        for event in events:
            if event.type == pygame.VIDEORESIZE:
                self.update_layout()
                
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn in self.button_rects:
                    if btn["rect"].collidepoint(mpos):
                        self.handle_action(btn["action"])

    def handle_action(self, action):
        if action == "resume":
            self.state_manager("PLAY")
        elif action == "exit_to_editor":
            # Трюк: звертаємося до головного вікна і "натискаємо" кнопку STOP
            main_window = self.viewport.window()
            if hasattr(main_window, 'on_play_clicked'):
                main_window.on_play_clicked()
            else:
                self.state_manager("EDITOR")

    def draw(self, surface, mpos):
        screen_w = surface.get_width()
        
        if self.is_overlay:
            surface.blit(self.bg_overlay, (0, 0))
        else:
            surface.fill((20, 20, 40))

        title_surf = self.title_font.render(self.title, True, self.color_title)
        title_rect = title_surf.get_rect(centerx=screen_w // 2, y=screen_w * 0.1) 
        surface.blit(title_surf, title_rect)

        for btn in self.button_rects:
            color = self.color_hover if btn["rect"].collidepoint(mpos) else self.color_normal
            text_surf = self.btn_font.render(btn["text"], True, color)
            surface.blit(text_surf, btn["rect"])