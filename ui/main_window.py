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
                             QMenu, QComboBox, QCheckBox, QDoubleSpinBox, QSpinBox)
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

        self.horizontal_splitter = QSplitter(Qt.Horizontal)

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
        self.asset_list = QListWidget()
        self.asset_list.setViewMode(QListWidget.IconMode)
        self.asset_list.setIconSize(QSize(64, 64))
        self.asset_list.clicked.connect(self.on_tile_clicked)
        self.asset_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.asset_list.customContextMenuRequested.connect(self.show_tile_context_menu)
        self.browser_layout.addWidget(self.asset_list)
        self.vertical_splitter.addWidget(self.browser_panel)
        self.center_layout.addWidget(self.vertical_splitter)

        # --- ПРАВА ПАНЕЛЬ ---
        self.properties_panel = QFrame()
        self.properties_panel.setMinimumWidth(280)
        self.properties_panel.setMaximumWidth(350)
        self.properties_layout = QVBoxLayout(self.properties_panel)
        
        self.prop_title = QLabel("Properties")
        self.prop_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.properties_layout.addWidget(self.prop_title)
        
        self.prop_type_label = QLabel("Object Type:")
        self.prop_type_combo = QComboBox()
        self.prop_type_combo.addItems(["Static Blocks", "Kill Zone", "Spawner"])
        self.properties_layout.addWidget(self.prop_type_label)
        self.properties_layout.addWidget(self.prop_type_combo)
        
        self.prop_block_container = QWidget()
        self.prop_block_layout = QVBoxLayout(self.prop_block_container)
        self.prop_block_layout.setContentsMargins(0, 0, 0, 0)
        
        self.prop_visible_cb = QCheckBox("Visible in Game") 
        self.prop_collision_cb = QCheckBox("Has Collision (Solid)")
        self.prop_block_layout.addWidget(self.prop_visible_cb)
        self.prop_block_layout.addWidget(self.prop_collision_cb)
        self.properties_layout.addWidget(self.prop_block_container)
        
        self.prop_spawner_container = QWidget()
        self.prop_spawner_layout = QVBoxLayout(self.prop_spawner_container)
        self.prop_spawner_layout.setContentsMargins(0, 0, 0, 0)
        
        self.prop_preset_label = QLabel("Entity Preset:")
        self.prop_preset_combo = QComboBox()
        self.prop_preset_combo.addItems(["Player", "Enemy", "Friendly NPC"])
        self.prop_spawner_layout.addWidget(self.prop_preset_label)
        self.prop_spawner_layout.addWidget(self.prop_preset_combo)
        
        self.prop_walk_cb = QCheckBox("Can Walk")
        self.prop_jump_cb = QCheckBox("Can Jump")
        self.prop_wall_jump_cb = QCheckBox("Can Wall Jump")
        self.prop_dash_cb = QCheckBox("Dash Attack")
        self.prop_shoot_cb = QCheckBox("Ranged Attack")
        self.prop_spawner_layout.addWidget(self.prop_walk_cb)
        self.prop_spawner_layout.addWidget(self.prop_jump_cb)
        self.prop_spawner_layout.addWidget(self.prop_wall_jump_cb)
        self.prop_spawner_layout.addWidget(self.prop_dash_cb)
        self.prop_spawner_layout.addWidget(self.prop_shoot_cb)
        
        self.prop_speed_label = QLabel("Walk Speed:")
        self.prop_speed_input = QDoubleSpinBox()
        self.prop_speed_input.setRange(0.1, 10.0)
        self.prop_speed_input.setSingleStep(0.1)
        self.prop_spawner_layout.addWidget(self.prop_speed_label)
        self.prop_spawner_layout.addWidget(self.prop_speed_input)
        
        self.prop_jump_label = QLabel("Jump Height:")
        self.prop_jump_input = QSpinBox()
        self.prop_jump_input.setRange(1, 15)
        self.prop_spawner_layout.addWidget(self.prop_jump_label)
        self.prop_spawner_layout.addWidget(self.prop_jump_input)

        self.prop_shoot_cd_label = QLabel("Shoot Cooldown (frames):")
        self.prop_shoot_cd_input = QSpinBox()
        self.prop_shoot_cd_input.setRange(10, 300)
        self.prop_spawner_layout.addWidget(self.prop_shoot_cd_label)
        self.prop_spawner_layout.addWidget(self.prop_shoot_cd_input)
        
        self.properties_layout.addWidget(self.prop_spawner_container)
        
        # ДОДАЛИ КНОПКУ РЕСЕТУ
        self.btn_reset_props = QPushButton("Reset Properties")
        self.btn_reset_props.setStyleSheet("background-color: #d73a49; color: white; font-weight: bold; padding: 5px; margin-top: 15px;")
        self.properties_layout.addWidget(self.btn_reset_props)

        self.properties_layout.addStretch()
        self.properties_panel.hide()

        self.current_selected_folder = None 

        # Сигнали
        self.prop_type_combo.currentIndexChanged.connect(self.toggle_properties_ui)
        self.prop_preset_combo.currentIndexChanged.connect(self.toggle_spawner_features)
        self.prop_walk_cb.toggled.connect(self.toggle_spawner_features)
        self.prop_jump_cb.toggled.connect(self.toggle_spawner_features)
        self.prop_shoot_cb.toggled.connect(self.toggle_spawner_features)
        self.btn_reset_props.clicked.connect(self.reset_folder_properties) # ПІДКЛЮЧИЛИ КНОПКУ
        
        for w in [self.prop_type_combo, self.prop_preset_combo, self.prop_collision_cb, self.prop_visible_cb, 
                  self.prop_walk_cb, self.prop_shoot_cb, self.prop_jump_cb, self.prop_wall_jump_cb, self.prop_dash_cb,
                  self.prop_speed_input, self.prop_jump_input, self.prop_shoot_cd_input]:
            if isinstance(w, QComboBox): w.currentIndexChanged.connect(self.save_folder_properties)
            elif isinstance(w, QCheckBox): w.toggled.connect(self.save_folder_properties)
            else: w.valueChanged.connect(self.save_folder_properties)

        self.horizontal_splitter.addWidget(self.sidebar)
        self.horizontal_splitter.addWidget(self.center_container)
        self.horizontal_splitter.addWidget(self.properties_panel)
        self.horizontal_splitter.setStretchFactor(1, 1)
        self.main_layout.addWidget(self.horizontal_splitter)

    # ================= РЕШТА ФУНКЦІЙ =================
    def toggle_properties_ui(self):
        obj_type = self.prop_type_combo.currentText()
        is_spawner = (obj_type == "Spawner")
        is_killzone = (obj_type == "Kill Zone")
        is_block = (obj_type in ["Static Blocks", "Kill Zone"])
        
        self.prop_block_container.setVisible(is_block)
        self.prop_spawner_container.setVisible(is_spawner)
        
        # ФІКС: Примусово знімаємо галочку колізії для Спавнерів та Kill Zone
        if is_killzone or is_spawner:
            self.prop_collision_cb.setChecked(False)
            
        if is_killzone:
            self.prop_collision_cb.setVisible(False)
        else:
            self.prop_collision_cb.setVisible(True)
            
        if is_spawner:
            self.toggle_spawner_features()
        
    def toggle_spawner_features(self):
        preset = self.prop_preset_combo.currentText()
        is_player = (preset == "Player")
        is_enemy = (preset == "Enemy")
        
        self.prop_walk_cb.setVisible(True)
        is_walking = self.prop_walk_cb.isChecked()
        self.prop_speed_label.setVisible(is_walking)
        self.prop_speed_input.setVisible(is_walking)
        
        self.prop_jump_cb.setVisible(is_player)
        self.prop_wall_jump_cb.setVisible(is_player)
        self.prop_dash_cb.setVisible(is_player)
        
        is_jumping = is_player and self.prop_jump_cb.isChecked()
        self.prop_jump_label.setVisible(is_jumping)
        self.prop_jump_input.setVisible(is_jumping)
        
        can_shoot_entity = is_player or is_enemy
        self.prop_shoot_cb.setVisible(can_shoot_entity)
        is_shooting = can_shoot_entity and self.prop_shoot_cb.isChecked()
        self.prop_shoot_cd_label.setVisible(is_shooting)
        self.prop_shoot_cd_input.setVisible(is_shooting)

    def reset_folder_properties(self):
        """Скидає властивості до стандартного статичного блоку"""
        if not self.current_selected_folder: return
        
        reply = QMessageBox.question(self, 'Reset Properties', 
                                     f"Reset '{self.current_selected_folder}' to a default solid block?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                     
        if reply == QMessageBox.Yes:
            # Блокуємо сигнали, щоб не зберігати кожен клік
            widgets = [self.prop_type_combo, self.prop_preset_combo, self.prop_collision_cb, self.prop_visible_cb,
                      self.prop_walk_cb, self.prop_shoot_cb, self.prop_jump_cb, self.prop_wall_jump_cb, self.prop_dash_cb,
                      self.prop_speed_input, self.prop_jump_input, self.prop_shoot_cd_input]
            for w in widgets: w.blockSignals(True)
            
            # Скидаємо до дефолту
            self.prop_type_combo.setCurrentText("Static Blocks")
            self.prop_preset_combo.setCurrentText("Enemy")
            self.prop_collision_cb.setChecked(True)
            self.prop_visible_cb.setChecked(True)
            self.prop_walk_cb.setChecked(False)
            self.prop_shoot_cb.setChecked(False)
            self.prop_jump_cb.setChecked(False)
            self.prop_wall_jump_cb.setChecked(True)
            self.prop_dash_cb.setChecked(True)
            self.prop_speed_input.setValue(1.0)
            self.prop_jump_input.setValue(3)
            self.prop_shoot_cd_input.setValue(60)
            
            self.toggle_properties_ui()
            
            for w in widgets: w.blockSignals(False)
            
            # Примусово зберігаємо новий чистий стан
            self.save_folder_properties()
            print(f"Властивості для {self.current_selected_folder} скинуто до дефолтних!")

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
                self.asset_list.addItem(item)

    def load_folder_properties(self, folder_name):
        self.current_selected_folder = folder_name
        self.prop_title.setText(f"Properties: {folder_name}")
        self.properties_panel.show()
        
        widgets = [self.prop_type_combo, self.prop_preset_combo, self.prop_collision_cb, self.prop_visible_cb,
                  self.prop_walk_cb, self.prop_shoot_cb, self.prop_jump_cb, self.prop_wall_jump_cb, self.prop_dash_cb,
                  self.prop_speed_input, self.prop_jump_input, self.prop_shoot_cd_input]
        for w in widgets: w.blockSignals(True)
        
        path = os.path.join('data', 'images', 'tiles', folder_name, 'properties.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                obj_type = data.get('type', "Static Blocks")
                self.prop_type_combo.setCurrentText(obj_type)
                self.prop_preset_combo.setCurrentText(data.get('preset', "Enemy"))
                
                default_col = False if obj_type in ["Kill Zone", "Spawner"] else True
                self.prop_collision_cb.setChecked(data.get('collision', default_col))
                
                self.prop_visible_cb.setChecked(data.get('is_visible', True))
                self.prop_walk_cb.setChecked(data.get('can_walk', False))
                self.prop_shoot_cb.setChecked(data.get('can_shoot', False))
                self.prop_jump_cb.setChecked(data.get('can_jump', False))
                self.prop_wall_jump_cb.setChecked(data.get('can_wall_jump', True))
                self.prop_dash_cb.setChecked(data.get('can_dash', True))
                self.prop_speed_input.setValue(data.get('walk_speed', 1.0))
                self.prop_jump_input.setValue(data.get('jump_height', 3))
                self.prop_shoot_cd_input.setValue(data.get('shoot_cooldown', 60))
        else:
            self.prop_type_combo.setCurrentText("Static Blocks")
            self.prop_collision_cb.setChecked(True)
            self.prop_visible_cb.setChecked(True)
            self.prop_walk_cb.setChecked(False)
            
        self.toggle_properties_ui()
        for w in widgets: w.blockSignals(False)
    
    def save_folder_properties(self):
        if not self.current_selected_folder: return
        folder_dir = os.path.join('data', 'images', 'tiles', self.current_selected_folder)
        if not os.path.exists(folder_dir): return
            
        path = os.path.join(folder_dir, 'properties.json')
        data = {
            'type': self.prop_type_combo.currentText(),
            'preset': self.prop_preset_combo.currentText(),
            # ФІКС: Якщо це Kill Zone або Spawner, колізія ЗАВЖДИ False у файлі JSON
            'collision': False if self.prop_type_combo.currentText() in ["Kill Zone", "Spawner"] else self.prop_collision_cb.isChecked(),
            'is_visible': self.prop_visible_cb.isChecked(), 
            'can_walk': self.prop_walk_cb.isChecked(),
            'can_shoot': self.prop_shoot_cb.isChecked(),
            'can_jump': self.prop_jump_cb.isChecked(),
            'can_wall_jump': self.prop_wall_jump_cb.isChecked(),
            'can_dash': self.prop_dash_cb.isChecked(),
            'walk_speed': self.prop_speed_input.value(),
            'jump_height': self.prop_jump_input.value(),
            'shoot_cooldown': self.prop_shoot_cd_input.value()
        }
        with open(path, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)
            
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
            if getattr(self, 'current_selected_folder', None): 
                self.properties_panel.show() 
            self.viewport.set_mode("EDITOR")
    
    def on_new_folder_clicked(self):
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Name (e.g. water):")
        if ok and folder_name:
            path = os.path.join('data', 'images', 'tiles', folder_name)
            if not os.path.exists(path):
                os.makedirs(path) 
                self.assets[folder_name] = [] 
                
                item = QStandardItem(folder_name)
                item.setEditable(False)
                self.tree_model.appendRow(item)
            else:
                QMessageBox.warning(self, "Error", "Folder already exists!")

    def on_add_tiles_clicked(self):
        index = self.tree_view.currentIndex()
        if not index.isValid(): return
            
        folder_name = self.tree_model.itemFromIndex(index).text()
        files, _ = QFileDialog.getOpenFileNames(self, "Select Tiles", "", "Images (*.png)")
        
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
    
    def show_context_menu(self, position):
        index = self.tree_view.indexAt(position)
        if not index.isValid(): return 
            
        menu = QMenu()
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        
        action = menu.exec(self.tree_view.viewport().mapToGlobal(position))
        
        if action == rename_action:
            self.rename_folder(index)
        elif action == delete_action:
            self.delete_folder(index)

    def rename_folder(self, index):
        old_name = self.tree_model.itemFromIndex(index).text()
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=old_name)
        
        if ok and new_name and new_name != old_name:
            old_path = os.path.join('data', 'images', 'tiles', old_name)
            new_path = os.path.join('data', 'images', 'tiles', new_name)
            
            if not os.path.exists(new_path):
                try:
                    os.rename(old_path, new_path) 
                    self.assets[new_name] = self.assets.pop(old_name) 
                    self.tree_model.itemFromIndex(index).setText(new_name)
                    if getattr(self, 'current_selected_folder', None) == old_name:
                        self.load_folder_properties(new_name)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not rename: {e}")
            else:
                QMessageBox.warning(self, "Error", "Folder already exists!")

    def delete_folder(self, index):
        folder_name = self.tree_model.itemFromIndex(index).text()
        reply = QMessageBox.question(self, 'Delete', 
                                     f"Are you sure you want to delete folder '{folder_name}'?",
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
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete: {e}")
    
    def show_tile_context_menu(self, position):
        item = self.asset_list.itemAt(position)
        if not item: return
            
        menu = QMenu()
        delete_action = menu.addAction("Delete tile")
        action = menu.exec(self.asset_list.viewport().mapToGlobal(position))
        
        if action == delete_action:
            self.delete_tile(item)

    def delete_tile(self, item):
        row = self.asset_list.row(item) 
        folder_index = self.tree_view.currentIndex()
        folder_name = self.tree_model.itemFromIndex(folder_index).text()
        
        reply = QMessageBox.question(self, 'Delete tile', 
                                     f"Delete this tile? Map will auto-update.",
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
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete tile: {e}")
                                            
    def load_stylesheet(self):
        try:
            with open("ui/styles.qss", "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError: pass