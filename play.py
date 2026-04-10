import pygame
import sys
import os
import json
from scripts.game import Game
from scripts.utils import load_images

os.environ['SDL_VIDEO_CENTERED'] = '1'

# Надійний спосіб знайти папку з грою (Бронебійний фікс)
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
    if os.path.exists(os.path.join(base_dir, "_internal", "data")):
        os.chdir(os.path.join(base_dir, "_internal"))
    else:
        os.chdir(base_dir)
else:
    os.chdir(os.path.abspath("."))

def main():
    pygame.init()
    pygame.mixer.init()

    # Зчитуємо конфіг
    config = {"resolution_index": 2, "fullscreen": False}
    if os.path.exists('data/config.json'):
        try:
            with open('data/config.json', 'r', encoding='utf-8') as f:
                config.update(json.load(f))
        except: pass

    resolutions = [(640, 360), (1280, 720), (1920, 1080)]
    res = resolutions[config.get('resolution_index', 1)]
    
    # ФІКС: Тільки Fullscreen, ніякого SCALED у віконному режимі
    flags = pygame.FULLSCREEN | pygame.SCALED if config.get('fullscreen') else 0

    screen = pygame.display.set_mode(res, flags)

    # Завантажуємо базові тайли для рушія
    assets = {}
    tiles_path = 'data/images/tiles'
    if os.path.exists(tiles_path):
        for folder in os.listdir(tiles_path):
            if os.path.isdir(os.path.join(tiles_path, folder)):
                assets[folder] = load_images(f'tiles/{folder}')

    game = Game(assets, res[0], res[1])

    # Завантажуємо першу карту по сюжету
    level_list = []
    if os.path.exists('data/maps'):
        map_objects = []
        for f_name in os.listdir('data/maps'):
            if f_name.endswith('.json'):
                try:
                    with open(f'data/maps/{f_name}', 'r', encoding='utf-8') as f:
                        d = json.load(f)
                        if not d.get('ignore_in_progression', False):
                            map_objects.append({'name': f_name, 'order': d.get('level_order', 999)})
                except: pass
        map_objects.sort(key=lambda x: (x['order'], x['name']))
        level_list = [x['name'] for x in map_objects]

    if level_list:
        game.load_level(f"data/maps/{level_list[0]}")
    elif os.path.exists('data/maps/main_menu.json'):
        game.load_level("data/maps/main_menu.json")

    clock = pygame.time.Clock()

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        mpos = pygame.mouse.get_pos()
        
        # Перевірка: чи не змінив гравець роздільну здатність у налаштуваннях
        current_res = resolutions[game.config.get('resolution_index', 2)]
        current_fs = game.config.get('fullscreen', False)
        
        if current_res != res or current_fs != config.get('fullscreen'):
            res = current_res
            config['fullscreen'] = current_fs
            # ФІКС: Тут теж прибираємо SCALED для віконного режиму
            flags = pygame.FULLSCREEN | pygame.SCALED if config['fullscreen'] else 0
            screen = pygame.display.set_mode(res, flags)
            game.resize_display(res[0], res[1])

        game.update(events, mpos)
        
        screen.fill((0,0,0))
        game.draw(screen, mpos)
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()