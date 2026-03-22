import sys
import os
import shutil
import json
import pygame
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTreeView, QFrame, 
                             QSplitter, QPushButton, QLabel,
                             QListWidget, QListWidgetItem,
                             QInputDialog, QFileDialog, QMessageBox, QApplication, 
                             QMenu, QComboBox, QCheckBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap, QImage
from ui.pygame_widget import NumiViewport 
from scripts.utils import load_images

valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
class MainWindow(QMainWindow):
    def __init__(self, assets):
        super().__init__()
        self.setWindowTitle("NumiEngine")
        self.resize(1280, 720)
        self.assets = assets 
        
        self.load_stylesheet()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- TOOLBAR ---
        self.toolbar = QFrame()
        self.toolbar.setFixedHeight(40)
        self.toolbar.setObjectName("Toolbar")
        self.toolbar_layout = QHBoxLayout(self.toolbar)
        
        self.btn_save = QPushButton("Save Map")
        self.btn_play = QPushButton("▶ PLAY")
        self.btn_save.clicked.connect(self.on_save_clicked)
        self.btn_play.clicked.connect(self.on_play_clicked)
        
        self.toolbar_layout.addWidget(self.btn_save)
        self.toolbar_layout.addStretch()
        self.toolbar_layout.addWidget(self.btn_play)
        self.toolbar_layout.addStretch()
        self.main_layout.addWidget(self.toolbar)

        # --- ГОЛОВНИЙ РОЗДІЛЮВАЧ ---
        self.horizontal_splitter = QSplitter(Qt.Horizontal)

        # 1. ЛІВА ПАНЕЛЬ (SIDEBAR)
        self.sidebar = QFrame()
        self.sidebar.setMinimumWidth(250)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.addWidget(QLabel("PROJECT"))
        
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.sidebar_layout.addWidget(self.tree_view)
        
        self.tree_model = QStandardItemModel()
        self.tree_view.setModel(self.tree_model)
        for folder_name in self.assets.keys():
            item = QStandardItem(folder_name)
            item.setEditable(False)
            self.tree_model.appendRow(item)
            
        self.tree_view.clicked.connect(self.on_folder_clicked)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        
        self.btn_add_tiles = QPushButton("+ Add Tiles")
        self.btn_add_tiles.setObjectName("NewFolderBtn")
        self.btn_add_tiles.hide() 
        self.sidebar_layout.addWidget(self.btn_add_tiles)

        self.btn_new_folder = QPushButton("+ Folder")
        self.btn_new_folder.setObjectName("NewFolderBtn")
        self.sidebar_layout.addWidget(self.btn_new_folder)
        
        self.btn_new_folder.clicked.connect(self.on_new_folder_clicked)
        self.btn_add_tiles.clicked.connect(self.on_add_tiles_clicked)

        # 2. ЦЕНТРАЛЬНА ПАНЕЛЬ (VIEWPORT + BROWSER)
        self.center_container = QFrame()
        self.center_layout = QVBoxLayout(self.center_container)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        
        self.vertical_splitter = QSplitter(Qt.Vertical)
        
        self.viewport = NumiViewport(self.assets)
        self.vertical_splitter.addWidget(self.viewport)
        
        self.browser_panel = QFrame()
        self.browser_panel.setMinimumHeight(200)
        self.browser_panel.setObjectName("BrowserPanel")
        self.browser_layout = QVBoxLayout(self.browser_panel)
        self.browser_layout.setContentsMargins(5, 5, 5, 5)

        self.asset_list = QListWidget()
        self.asset_list.setViewMode(QListWidget.IconMode)
        self.asset_list.setIconSize(QSize(64, 64))
        self.asset_list.setResizeMode(QListWidget.Adjust)
        self.asset_list.setSpacing(10)
        self.asset_list.setMovement(QListWidget.Static)
        
        # ПІДКЛЮЧЕННЯ ТАЙЛІВ ТУТ (після створення asset_list)
        self.asset_list.clicked.connect(self.on_tile_clicked)
        self.asset_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.asset_list.customContextMenuRequested.connect(self.show_tile_context_menu)
        
        self.browser_layout.addWidget(self.asset_list)
        self.vertical_splitter.addWidget(self.browser_panel)
        
        self.vertical_splitter.setStretchFactor(0, 7)
        self.vertical_splitter.setStretchFactor(1, 3)
        self.center_layout.addWidget(self.vertical_splitter)

        # 3. ПРАВА ПАНЕЛЬ (ВЛАСТИВОСТІ)
        self.properties_panel = QFrame()
        self.properties_panel.setMinimumWidth(250)
        self.properties_panel.setMaximumWidth(300) # Захист від розтягування
        self.properties_layout = QVBoxLayout(self.properties_panel)
        
        self.prop_title = QLabel("Властивості")
        self.prop_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        self.properties_layout.addWidget(self.prop_title)
        
        self.prop_type_label = QLabel("Тип об'єкта:")
        self.prop_type_combo = QComboBox()
        self.prop_type_combo.addItems(["Статичні блоки", "Анімований персонаж"])
        
        self.prop_collision_cb = QCheckBox("Має колізію (твердий)")
        self.prop_walk_cb = QCheckBox("Може ходити")
        
        self.properties_layout.addWidget(self.prop_type_label)
        self.properties_layout.addWidget(self.prop_type_combo)
        self.properties_layout.addWidget(self.prop_collision_cb)
        self.properties_layout.addWidget(self.prop_walk_cb)
        self.properties_layout.addStretch() 
        
        self.properties_panel.hide() 
        
        self.prop_type_combo.currentIndexChanged.connect(self.save_folder_properties)
        self.prop_collision_cb.toggled.connect(self.save_folder_properties)
        self.prop_walk_cb.toggled.connect(self.save_folder_properties)
        
        self.current_selected_folder = None 

        # --- ФІНАЛЬНА ЗБІРКА СПЛІТТЕРА (Порядок має значення!) ---
        self.horizontal_splitter.addWidget(self.sidebar)          # 1. Зліва
        self.horizontal_splitter.addWidget(self.center_container) # 2. Центр
        self.horizontal_splitter.addWidget(self.properties_panel) # 3. Справа
        
        # Налаштування розтягування (Центр забирає все вільне місце)
        self.horizontal_splitter.setCollapsible(0, False)
        self.horizontal_splitter.setCollapsible(1, False)
        self.horizontal_splitter.setCollapsible(2, False)
        
        self.horizontal_splitter.setStretchFactor(0, 0)
        self.horizontal_splitter.setStretchFactor(1, 1) # Тільки центр = 1
        self.horizontal_splitter.setStretchFactor(2, 0)
        
        self.horizontal_splitter.setSizes([250, 780, 250])
        
        self.main_layout.addWidget(self.horizontal_splitter)

    # ================= РЕШТА ФУНКЦІЙ =================

    def on_folder_clicked(self, index):
        folder_name = self.tree_model.itemFromIndex(index).text()
        self.asset_list.clear()
        self.btn_add_tiles.show()
        self.load_folder_properties(folder_name)
        if folder_name in self.assets:
            for i, surf in enumerate(self.assets[folder_name]):
                data = pygame.image.tostring(surf, 'RGBA')
                qimg = QImage(data, surf.get_width(), surf.get_height(), QImage.Format_RGBA8888)
                item = QListWidgetItem(QIcon(QPixmap.fromImage(qimg)), f"tile_{i}")
                item.setSizeHint(QSize(80, 90))
                item.setTextAlignment(Qt.AlignCenter)
                self.asset_list.addItem(item)

    def on_tile_clicked(self, index):
        tile_index = index.row()
        folder_index = self.tree_view.currentIndex()
        folder_name = self.tree_model.itemFromIndex(folder_index).text()
        self.viewport.set_current_tile(folder_name, tile_index)

    def on_save_clicked(self):
        self.viewport.editor.tilemap.save('map.json')
        print("Мапу успішно збережено в map.json!")

    def on_play_clicked(self):
        if self.btn_play.text() == "▶ PLAY":
            self.btn_play.setText("■ STOP")
            self.btn_play.setStyleSheet("background-color: #d73a49; color: white; font-weight: bold;")
            
            self.sidebar.hide()
            self.browser_panel.hide()
            self.properties_panel.hide()
            
            QApplication.processEvents() 
            
            self.viewport.set_mode("PLAY")
            self.viewport.setFocus()
            
        else:
            self.btn_play.setText("▶ PLAY")
            self.btn_play.setStyleSheet("")
            
            self.sidebar.show()
            self.browser_panel.show()
            if self.current_selected_folder: 
                self.properties_panel.show() 
            self.viewport.set_mode("EDITOR")
    
    def on_new_folder_clicked(self):
        folder_name, ok = QInputDialog.getText(self, "Нова папка", "Введіть назву (наприклад: water):")
        
        if ok and folder_name:
            path = os.path.join('data', 'images', 'tiles', folder_name)
            if not os.path.exists(path):
                os.makedirs(path) 
                self.assets[folder_name] = [] 
                
                item = QStandardItem(folder_name)
                item.setEditable(False)
                self.tree_model.appendRow(item)
                print(f"Створено нову папку: {folder_name}")
            else:
                QMessageBox.warning(self, "Помилка", "Така папка вже існує!")

    def on_add_tiles_clicked(self):
        index = self.tree_view.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "Увага", "Спочатку виберіть папку в дереві зліва, куди хочете додати тайли!")
            return
            
        folder_name = self.tree_model.itemFromIndex(index).text()
        files, _ = QFileDialog.getOpenFileNames(self, "Виберіть тайли", "", "Images (*.png)")
        
        if files:
            target_dir = os.path.join('data', 'images', 'tiles', folder_name)
            old_files = sorted([f for f in os.listdir(target_dir) if f.lower().endswith(valid_extensions)]) if os.path.exists(target_dir) else []
            
            for file_path in files:
                filename = os.path.basename(file_path)
                shutil.copy(file_path, os.path.join(target_dir, filename))
                
            new_files = sorted([f for f in os.listdir(target_dir) if f.lower().endswith(valid_extensions)])
            
            mapping = {}
            for i, old_file in enumerate(old_files):
                if old_file in new_files:
                    mapping[i] = new_files.index(old_file)
                    
            editor_tilemap = self.viewport.editor.tilemap
            
            for loc, t in editor_tilemap.tilemap.items():
                if t['type'] == folder_name and t['variant'] in mapping:
                    t['variant'] = mapping[t['variant']]
                    
            for t in editor_tilemap.offgrid_tiles:
                if t['type'] == folder_name and t['variant'] in mapping:
                    t['variant'] = mapping[t['variant']]
                    
            if self.viewport.current_tile_group == folder_name and self.viewport.current_tile_variant in mapping:
                self.viewport.set_current_tile(folder_name, mapping[self.viewport.current_tile_variant])
                
            self.assets[folder_name] = load_images('tiles/' + folder_name)
            self.on_folder_clicked(index)
            print(f"Додано {len(files)} файлів. Індекси на мапі автоматично відкориговано!")
    
    def show_context_menu(self, position):
        index = self.tree_view.indexAt(position)
        if not index.isValid(): return 
            
        menu = QMenu()
        rename_action = menu.addAction("Перейменувати")
        delete_action = menu.addAction("Видалити")
        
        action = menu.exec(self.tree_view.viewport().mapToGlobal(position))
        
        if action == rename_action:
            self.rename_folder(index)
        elif action == delete_action:
            self.delete_folder(index)

    def rename_folder(self, index):
        old_name = self.tree_model.itemFromIndex(index).text()
        new_name, ok = QInputDialog.getText(self, "Перейменувати", "Нова назва:", text=old_name)
        
        if ok and new_name and new_name != old_name:
            old_path = os.path.join('data', 'images', 'tiles', old_name)
            new_path = os.path.join('data', 'images', 'tiles', new_name)
            
            if not os.path.exists(new_path):
                try:
                    os.rename(old_path, new_path) 
                    self.assets[new_name] = self.assets.pop(old_name) 
                    self.tree_model.itemFromIndex(index).setText(new_name)
                    print(f"Папку {old_name} перейменовано на {new_name}")
                except Exception as e:
                    QMessageBox.critical(self, "Помилка", f"Не вдалося перейменувати: {e}")
            else:
                QMessageBox.warning(self, "Помилка", "Папка з такою назвою вже існує!")

    def delete_folder(self, index):
        folder_name = self.tree_model.itemFromIndex(index).text()
        reply = QMessageBox.question(self, 'Видалення', 
                                     f"Ви впевнені, що хочете видалити папку '{folder_name}' та всі тайли в ній?\nЦю дію неможливо скасувати!",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                     
        if reply == QMessageBox.Yes:
            path = os.path.join('data', 'images', 'tiles', folder_name)
            try:
                if os.path.exists(path):
                    import shutil
                    shutil.rmtree(path)
                
                if folder_name in self.assets:
                    del self.assets[folder_name]

                editor_tilemap = self.viewport.editor.tilemap
                
                keys_to_delete = [loc for loc, tile in editor_tilemap.tilemap.items() if tile['type'] == folder_name]
                for loc in keys_to_delete:
                    del editor_tilemap.tilemap[loc]
                
                editor_tilemap.offgrid_tiles = [t for t in editor_tilemap.offgrid_tiles if t['type'] != folder_name]
                
                if self.viewport.current_tile_group == folder_name:
                    self.viewport.set_current_tile(None, 0)
                    
                self.tree_model.removeRow(index.row())
                self.asset_list.clear()
                self.btn_add_tiles.hide()
                self.properties_panel.hide()
                print(f"Папку {folder_name} видалено, сцену очищено!")
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося видалити: {e}")
    
    def show_tile_context_menu(self, position):
        item = self.asset_list.itemAt(position)
        if not item: return
            
        menu = QMenu()
        delete_action = menu.addAction("Видалити тайл")
        action = menu.exec(self.asset_list.viewport().mapToGlobal(position))
        
        if action == delete_action:
            self.delete_tile(item)

    def delete_tile(self, item):
        row = self.asset_list.row(item) 
        folder_index = self.tree_view.currentIndex()
        folder_name = self.tree_model.itemFromIndex(folder_index).text()
        
        reply = QMessageBox.question(self, 'Видалення тайла', 
                                     f"Видалити цей тайл?\nРушій автоматично оновить мапу.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                     
        if reply == QMessageBox.Yes:
            folder_path = os.path.join('data', 'images', 'tiles', folder_name)
            try:
                files = sorted([f for f in os.listdir(folder_path) if f.endswith(valid_extensions)])
                if row < len(files):
                    file_to_delete = files[row]
                    os.remove(os.path.join(folder_path, file_to_delete))
                    del self.assets[folder_name][row]
                    
                    editor_tilemap = self.viewport.editor.tilemap
                    
                    keys_to_delete = []
                    for loc, t in editor_tilemap.tilemap.items():
                        if t['type'] == folder_name:
                            if t['variant'] == row:
                                keys_to_delete.append(loc)
                            elif t['variant'] > row:
                                t['variant'] -= 1 
                                
                    for loc in keys_to_delete:
                        del editor_tilemap.tilemap[loc]
                        
                    tiles_to_keep = []
                    for t in editor_tilemap.offgrid_tiles:
                        if t['type'] == folder_name:
                            if t['variant'] == row:
                                continue 
                            elif t['variant'] > row:
                                t['variant'] -= 1 
                        tiles_to_keep.append(t)
                    editor_tilemap.offgrid_tiles = tiles_to_keep
                    
                    if self.viewport.current_tile_group == folder_name:
                        if self.viewport.current_tile_variant == row:
                            self.viewport.set_current_tile(None, 0)
                        elif self.viewport.current_tile_variant > row:
                            self.viewport.set_current_tile(folder_name, self.viewport.current_tile_variant - 1)
                        
                    self.on_folder_clicked(folder_index)
                    print(f"Тайл {file_to_delete} успішно видалено, мапу відкориговано!")
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося видалити тайл: {e}")
    
    def load_folder_properties(self, folder_name):
        self.current_selected_folder = folder_name
        self.prop_title.setText(f"Властивості: {folder_name}")
        self.properties_panel.show()
        
        self.prop_type_combo.blockSignals(True)
        self.prop_collision_cb.blockSignals(True)
        self.prop_walk_cb.blockSignals(True)
        
        path = os.path.join('data', 'images', 'tiles', folder_name, 'properties.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.prop_type_combo.setCurrentText(data.get('type', "Статичні блоки"))
                self.prop_collision_cb.setChecked(data.get('collision', True))
                self.prop_walk_cb.setChecked(data.get('can_walk', False))
        else:
            self.prop_type_combo.setCurrentText("Статичні блоки")
            self.prop_collision_cb.setChecked(True)
            self.prop_walk_cb.setChecked(False)
            
        self.prop_type_combo.blockSignals(False)
        self.prop_collision_cb.blockSignals(False)
        self.prop_walk_cb.blockSignals(False)

    def save_folder_properties(self):
        if not self.current_selected_folder: return
        
        path = os.path.join('data', 'images', 'tiles', self.current_selected_folder, 'properties.json')
        data = {
            'type': self.prop_type_combo.currentText(),
            'collision': self.prop_collision_cb.isChecked(),
            'can_walk': self.prop_walk_cb.isChecked()
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
                                            
    def load_stylesheet(self):
        try:
            with open("ui/styles.qss", "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError: pass