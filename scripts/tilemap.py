import json
import pygame

AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2, 
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8,
}

NEIGHBOR_OFFSETS = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]
AUTOTILE_TYPES = {'grass', 'stone'}

class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []
        
    def extract(self, id_pairs, keep = False):
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)
                    
        for loc in list(self.tilemap.keys()):
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                matches[-1]['pos'] = matches[-1]['pos'].copy()
                matches[-1]['pos'][0] *= self.tile_size
                matches[-1]['pos'][1] *= self.tile_size
                if not keep:
                    del self.tilemap[loc] 
        return matches
    
    def tiles_around(self, pos):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles
    
    def save(self, path):
        f = open(path, 'w')
        json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size, 'offgrid': self.offgrid_tiles}, f)
        f.close()
        
    def load(self, path):
        f = open(path, 'r')
        map_data = json.load(f)
        f.close()
        self.tilemap = map_data['tilemap']
        self.tile_size = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']
        
    def solid_check(self, pos):
        properties = getattr(self.game, 'tile_properties', {})
        
        # 1. Перевірка для об'єктів НА СІТЦІ
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tile_loc in self.tilemap:
            tile = self.tilemap[tile_loc]
            props = properties.get(tile['type'], {})
            if props.get('type') in ['Static Blocks', 'Kill Zone'] and props.get('collision', True): 
                return tile
                
        # 2. ФІКС: Перевірка для об'єктів ПОЗА СІТКОЮ (off-grid)
        for tile in self.offgrid_tiles:
            props = properties.get(tile['type'], {})
            if props.get('type') in ['Static Blocks', 'Kill Zone'] and props.get('collision', True): 
                if tile['type'] in self.game.assets and isinstance(self.game.assets[tile['type']], list) and tile['variant'] < len(self.game.assets[tile['type']]):
                    img = self.game.assets[tile['type']][tile['variant']]
                    rect = pygame.Rect(
                        tile['pos'][0],
                        tile['pos'][1],
                        img.get_width(),
                        img.get_height()
                    )
                    if rect.collidepoint(pos):
                        return tile
        return None
    
    def extract_spawners(self):
        spawners = []
        properties = getattr(self.game, 'tile_properties', {})
        
        for loc in list(self.tilemap.keys()):
            tile = self.tilemap[loc]
            props = properties.get(tile['type'], {})
            if props.get('type') == 'Spawner':
                if props.get('collision', False):
                    spawner_tile = tile.copy() 
                else:
                    spawner_tile = self.tilemap.pop(loc) 
                    
                spawner_tile['pos'] = [spawner_tile['pos'][0] * self.tile_size, spawner_tile['pos'][1] * self.tile_size]
                spawners.append(spawner_tile)

        for tile in self.offgrid_tiles.copy():
            props = properties.get(tile['type'], {})
            if props.get('type') == 'Spawner':
                if not props.get('collision', False):
                    self.offgrid_tiles.remove(tile) 
                spawners.append(tile)
        return spawners
    
    def physics_rects_around(self, pos):
        rects = []
        properties = getattr(self.game, 'tile_properties', {})
        
        # 1. Колізія для блоків НА СІТЦІ
        for tile in self.tiles_around(pos):
            props = properties.get(tile['type'], {})
            if props.get('type') in ['Static Blocks', 'Kill Zone'] and props.get('collision', True): 
                rects.append(pygame.Rect(
                    tile['pos'][0] * self.tile_size, 
                    tile['pos'][1] * self.tile_size, 
                    self.tile_size, self.tile_size
                ))
                
        # 2. ФІКС: Колізія для блоків ПОЗА СІТКОЮ
        for tile in self.offgrid_tiles:
            props = properties.get(tile['type'], {})
            if props.get('type') in ['Static Blocks', 'Kill Zone'] and props.get('collision', True): 
                if tile['type'] in self.game.assets and isinstance(self.game.assets[tile['type']], list) and tile['variant'] < len(self.game.assets[tile['type']]):
                    img = self.game.assets[tile['type']][tile['variant']]
                    rect = pygame.Rect(
                        tile['pos'][0],
                        tile['pos'][1],
                        img.get_width(),
                        img.get_height()
                    )
                    # Оптимізація: додаємо тверді блоки тільки якщо вони поруч із сутністю
                    if abs(pos[0] - rect.centerx) < 100 and abs(pos[1] - rect.centery) < 100:
                        rects.append(rect)
                        
        return rects
        
    def check_kill_zones(self, rect):
        properties = getattr(self.game, 'tile_properties', {})
        
        for tile in self.tiles_around((rect.centerx, rect.centery)):
            props = properties.get(tile['type'], {})
            if props.get('type') == 'Kill Zone':
                tile_rect = pygame.Rect(
                    tile['pos'][0] * self.tile_size, 
                    tile['pos'][1] * self.tile_size, 
                    self.tile_size, self.tile_size
                )
                if rect.colliderect(tile_rect):
                    return True
                    
        for tile in self.offgrid_tiles:
            props = properties.get(tile['type'], {})
            if props.get('type') == 'Kill Zone':
                if tile['type'] in self.game.assets and isinstance(self.game.assets[tile['type']], list) and tile['variant'] < len(self.game.assets[tile['type']]):
                    img = self.game.assets[tile['type']][tile['variant']]
                    tile_rect = pygame.Rect(
                        tile['pos'][0], tile['pos'][1], 
                        img.get_width(), img.get_height()
                    )
                    if rect.colliderect(tile_rect):
                        return True
        return False
    
    def autotile(self):
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                if check_loc in self.tilemap:
                    if self.tilemap[check_loc]['type'] == tile['type']:
                        neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            if (tile['type'] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbors]

    def render(self, surf, offset=(0, 0), render_hidden=False):
        properties = getattr(self.game, 'tile_properties', {})
        
        for tile in self.offgrid_tiles:
            props = properties.get(tile['type'], {})
            
            if not render_hidden:
                # ФІКС: Якщо це Спавнер БЕЗ колізії, він ПРИМУСОВО невидимий
                if props.get('type') == 'Spawner' and not props.get('collision', False):
                    continue
                if not props.get('is_visible', True):
                    continue
                
            if tile['type'] in self.game.assets and isinstance(self.game.assets[tile['type']], list) and tile['variant'] < len(self.game.assets[tile['type']]):
                surf.blit(self.game.assets[tile['type']][tile['variant']], 
                          (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1]))
        
        for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
                loc = str(x) + ';' + str(y)
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    props = properties.get(tile['type'], {})
                    
                    if not render_hidden:
                        # ФІКС: Якщо це Спавнер БЕЗ колізії, він ПРИМУСОВО невидимий
                        if props.get('type') == 'Spawner' and not props.get('collision', False):
                            continue
                        if not props.get('is_visible', True):
                            continue
                        
                    if tile['type'] in self.game.assets and isinstance(self.game.assets[tile['type']], list) and tile['variant'] < len(self.game.assets[tile['type']]):
                        surf.blit(self.game.assets[tile['type']][tile['variant']], 
                                  (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))