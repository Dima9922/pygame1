import os
import shutil
from scripts.utils import ask_for_string, ask_for_file, load_images

class AssetActions:
    def __init__(self, engine):
        """
        engine: посилання на головний клас NumiEngine, 
        щоб ми могли змінювати self.assets, self.folder_names тощо.
        """
        self.engine = engine

    def create_folder(self):
        folder_name = ask_for_string("New Folder", "Введіть назву папки:")
        if folder_name and folder_name.strip():
            folder_name = folder_name.strip()
            path = os.path.join(self.engine.tiles_base_path, folder_name)
            
            if not os.path.exists(path):
                os.makedirs(path)
                # Оновлюємо списки в основному двигуні
                if folder_name not in self.engine.folder_names:
                    self.engine.folder_names.append(folder_name)
                    self.engine.folder_names.sort()
                self.engine.assets[folder_name] = []
                print(f"Папку {folder_name} створено!")

    def import_tile_image(self):
        if not self.engine.current_folder:
            return

        file_path = ask_for_file("Select Tile Image", [("Images", "*.png *.jpg *.jpeg")])
        if file_path:
            file_name = os.path.basename(file_path)
            destination = os.path.join(self.engine.tiles_base_path, self.engine.current_folder, file_name)
            
            shutil.copy(file_path, destination)
            
            # Оновлюємо асети конкретної папки
            self.engine.assets[self.engine.current_folder] = load_images('tiles/' + self.engine.current_folder)
            print(f"Імпортовано: {file_name}")

    def delete_selected(self):
        item = self.engine.selected_item
        if not item: return
        
        if item['type'] == 'folder':
            path = os.path.join(self.engine.tiles_base_path, item['name'])
            if os.path.exists(path):
                shutil.rmtree(path)
                self.engine.folder_names = sorted(os.listdir(self.engine.tiles_base_path))
                if item['name'] in self.engine.assets:
                    del self.engine.assets[item['name']]
        
        elif item['type'] == 'file':
            # Знаходимо ім'я файлу за індексом
            folder_path = os.path.join(self.engine.tiles_base_path, self.engine.current_folder)
            files = sorted(os.listdir(folder_path))
            file_to_remove = files[item['index']]
            os.remove(os.path.join(folder_path, file_to_remove))
            
            # Оновлюємо відображення
            self.engine.assets[self.engine.current_folder] = load_images('tiles/' + self.engine.current_folder)

        self.engine.gui.context_menu.hide()
        self.engine.selected_item = None
        print("Елемент видалено!")

    def rename_selected(self):
        item = self.engine.selected_item
        if not item: return
        
        old_name = item['name'] if item['type'] == 'folder' else "file"
        new_name = ask_for_string("Rename", f"Нова назва для {old_name}:")
        
        if new_name and new_name.strip():
            new_name = new_name.strip()
            
            if item['type'] == 'folder':
                old_path = os.path.join(self.engine.tiles_base_path, old_name)
                new_path = os.path.join(self.engine.tiles_base_path, new_name)
                
                if not os.path.exists(new_path):
                    os.rename(old_path, new_path)
                    self.engine.folder_names = sorted(os.listdir(self.engine.tiles_base_path))
                    # Переносимо асети в словнику під новий ключ
                    self.engine.assets[new_name] = self.engine.assets.pop(old_name)
            
        self.engine.gui.context_menu.hide()
        self.engine.selected_item = None