import pygame
import sys
import os
import json

# --- ФІКС ДЛЯ .EXE (Допомагає знайти файли після компіляції) ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

os.chdir(resource_path('.'))
# ---------------------------------------------------------------

from scripts.game import Game
from scripts.utils import load_images

pygame.init()
pygame.mixer.init()

# Налаштування вікна гри (можеш змінити роздільну здатність)
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("My NumiEngine Game") # <--- НАЗВА ВІКНА ТВОЄЇ ГРИ
clock = pygame.time.Clock()

# Завантажуємо базові тайли
assets = {}
tiles_path = 'data/images/tiles'
if os.path.exists(tiles_path):
    for folder in os.listdir(tiles_path):
        if os.path.isdir(os.path.join(tiles_path, folder)):
            assets[folder] = load_images('tiles/' + folder)

# --- ОЧИЩЕННЯ ПАМ'ЯТІ РЕДАКТОРА ---
# Щоб скомпільована .exe гра ЗАВЖДИ починалася з першого файлу в Sequence Manager (меню)
if os.path.exists('data/maps/current_play.txt'):
    try:
        os.remove('data/maps/current_play.txt')
    except: pass

# Ініціалізуємо рушій (внутрішня роздільна здатність 640x360)
game = Game(assets, 640, 360)
zoom = min(SCREEN_WIDTH / 640, SCREEN_HEIGHT / 360)
virtual_surface = pygame.Surface((640, 360))

# --- ЗАВАНТАЖЕННЯ ПАУЗИ ---
is_paused = False
pause_ui_elements = []
if os.path.exists('data/maps/pause.json'):
    try:
        with open('data/maps/pause.json', 'r', encoding='utf-8') as f:
            pause_ui_elements = json.load(f).get('ui_elements', [])
    except: pass
pygame.font.init()
font = pygame.font.SysFont('arial', 14, bold=True)

# --- ГОЛОВНИЙ ЦИКЛ ГРИ ---
while True:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # Обробка ESC для паузи
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if not game.is_menu_mode: 
                is_paused = not is_paused
            
    # Вираховуємо позицію миші з урахуванням чорних смуг
    offset_x = (SCREEN_WIDTH - int(640 * zoom)) // 2
    offset_y = (SCREEN_HEIGHT - int(360 * zoom)) // 2
    mpos = pygame.mouse.get_pos()
    mpos_virtual = ((mpos[0] - offset_x) / zoom, (mpos[1] - offset_y) / zoom)

    virtual_surface.fill((0, 0, 0))

    if not is_paused:
        game.update(events, mpos_virtual)
        game.draw(virtual_surface, mpos_virtual)
    else:
        game.draw(virtual_surface, mpos_virtual)
        
        # Малюємо оверлей паузи
        overlay = pygame.Surface((640, 360), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        virtual_surface.blit(overlay, (0, 0))
        
        # Кліки в паузі
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for el in pause_ui_elements:
                    if el['type'] in assets and el['variant'] < len(assets[el['type']]):
                        img = assets[el['type']][el['variant']]
                        rect = pygame.Rect(el['pos'][0], el['pos'][1], img.get_width(), img.get_height())
                        if rect.collidepoint(mpos_virtual):
                            action = el.get('action', 'resume_game')
                            if action == 'resume_game':
                                is_paused = False
                            elif action == 'load_map':
                                target = el.get('target', 'menu.json')
                                with open('data/maps/current_play.txt', 'w') as f:
                                    f.write(target)
                                game.load_level(f"data/maps/{target}")
                                is_paused = False
                            elif action == 'quit_game':
                                pygame.quit()
                                sys.exit()

        # Відмальовка кнопок паузи
        for el in pause_ui_elements:
            if el['type'] in assets and el['variant'] < len(assets[el['type']]):
                img = assets[el['type']][el['variant']]
                rect = pygame.Rect(el['pos'][0], el['pos'][1], img.get_width(), img.get_height())
                if rect.collidepoint(mpos_virtual):
                    pygame.draw.rect(virtual_surface, (255, 204, 0), rect.inflate(4, 4), 2, border_radius=4)
                virtual_surface.blit(img, (el['pos'][0], el['pos'][1]))
                text = el.get('text', '')
                if text:
                    text_surf = font.render(text, True, (255, 255, 255))
                    shadow_surf = font.render(text, True, (0, 0, 0))
                    text_rect = text_surf.get_rect(center=(el['pos'][0] + img.get_width()/2, el['pos'][1] + img.get_height()/2))
                    virtual_surface.blit(shadow_surf, (text_rect.x + 1, text_rect.y + 1))
                    virtual_surface.blit(text_surf, text_rect)

    # Масштабуємо і виводимо на реальний екран
    scaled_w, scaled_h = int(640 * zoom), int(360 * zoom)
    scaled_surface = pygame.transform.scale(virtual_surface, (scaled_w, scaled_h))
    
    screen.fill((5, 5, 8)) # Чорний фон країв
    screen.blit(scaled_surface, (offset_x, offset_y))

    pygame.display.flip()
    clock.tick(60)