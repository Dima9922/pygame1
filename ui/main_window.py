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
                             QMenu, QComboBox, QCheckBox, QDoubleSpinBox, QSpinBox, QLineEdit, QScrollArea)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap, QImage
from ui.pygame_widget import NumiViewport 
from scripts.utils import load_images

valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')

def create_item(text):
    item = QStandardItem(text)
    item.setEditable(False)
    return item

class MainWindow(QMainWindow):
    def __init__(self, assets):
        super().__init__()
        self.setWindowTitle("NumiEngine")
        self.resize(1280, 720)
        self.assets = assets 
        self.current_selected_folder = None 
        
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

        # --- ЛІВА ПАНЕЛЬ ЗІ СКРОЛОМ ---
        self.sidebar_panel = QScrollArea()
        self.sidebar_panel.setWidgetResizable(True)
        self.sidebar_panel.setMinimumWidth(250)
        self.sidebar_widget = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar_widget)
        
        self.sidebar_layout.addWidget(QLabel("PROJECT"))
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.sidebar_layout.addWidget(self.tree_view)
        
        self.tree_model = QStandardItemModel()
        self.tree_view.setModel(self.tree_model)
        
        self.root_tiles = create_item("Tiles")
        self.root_entities = create_item("Entities")
        self.tree_model.appendRow(self.root_tiles)
        self.tree_model.appendRow(self.root_entities)
        
        for folder_name in sorted(self.assets.keys()):
            self.root_tiles.appendRow(create_item(folder_name))
            
        entities_path = os.path.join('data', 'images', 'entities')
        os.makedirs(entities_path, exist_ok=True)
        for ent in sorted(os.listdir(entities_path)):
            ent_full = os.path.join(entities_path, ent)
            if os.path.isdir(ent_full):
                ent_item = create_item(ent)
                self.root_entities.appendRow(ent_item)
                for anim in sorted(os.listdir(ent_full)):
                    if os.path.isdir(os.path.join(ent_full, anim)):
                        ent_item.appendRow(create_item(anim))
                        
        self.tree_view.expandAll()
            
        self.tree_view.clicked.connect(self.on_folder_clicked)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        
        self.btn_add_tiles = QPushButton("+ Add Images")
        self.btn_add_tiles.setObjectName("NewFolderBtn")
        self.btn_add_tiles.hide() 
        self.sidebar_layout.addWidget(self.btn_add_tiles)

        self.btn_new_folder = QPushButton("+ Folder")
        self.btn_new_folder.setObjectName("NewFolderBtn")
        self.sidebar_layout.addWidget(self.btn_new_folder)
        self.btn_new_folder.clicked.connect(self.on_new_folder_clicked)
        self.btn_add_tiles.clicked.connect(self.on_add_tiles_clicked)
        
        self.sidebar_panel.setWidget(self.sidebar_widget)

        # --- ЦЕНТРАЛЬНА ПАНЕЛЬ ---
        self.center_container = QFrame()
        self.center_layout = QVBoxLayout(self.center_container)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.vertical_splitter = QSplitter(Qt.Vertical)
        
        self.viewport = NumiViewport(self.assets)
        self.vertical_splitter.addWidget(self.viewport)
        
        # --- НИЖНЯ ПАНЕЛЬ ЗІ СКРОЛОМ ---
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
        self.browser_scroll = QScrollArea()
        self.browser_scroll.setWidgetResizable(True)
        self.browser_scroll.setWidget(self.browser_panel)
        self.browser_scroll.setMinimumHeight(200)
        self.vertical_splitter.addWidget(self.browser_scroll)
        self.center_layout.addWidget(self.vertical_splitter)

        # --- ПРАВА ПАНЕЛЬ ЗІ СКРОЛОМ ---
        self.properties_panel = QScrollArea()
        self.properties_panel.setWidgetResizable(True)
        self.properties_panel.setMinimumWidth(300)
        self.properties_panel.setMaximumWidth(350)
        
        self.properties_widget = QWidget()
        self.properties_layout = QVBoxLayout(self.properties_widget)
        
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

        # Налаштування анімацій та ефектів
        self.prop_anim_idle_label = QLabel("Idle Anim (e.g. enemy/idle):")
        self.prop_anim_idle_input = QLineEdit()
        self.prop_spawner_layout.addWidget(self.prop_anim_idle_label)
        self.prop_spawner_layout.addWidget(self.prop_anim_idle_input)
        
        self.prop_walk_cb = QCheckBox("Can Walk")
        self.prop_spawner_layout.addWidget(self.prop_walk_cb)
        self.prop_speed_label = QLabel("Walk Speed:")
        self.prop_speed_input = QDoubleSpinBox()
        self.prop_speed_input.setRange(0.1, 10.0)
        self.prop_speed_input.setSingleStep(0.1)
        self.prop_anim_walk_label = QLabel("Walk Anim:")
        self.prop_anim_walk_input = QLineEdit()
        self.prop_spawner_layout.addWidget(self.prop_speed_label)
        self.prop_spawner_layout.addWidget(self.prop_speed_input)
        self.prop_spawner_layout.addWidget(self.prop_anim_walk_label)
        self.prop_spawner_layout.addWidget(self.prop_anim_walk_input)
        
        self.prop_jump_cb = QCheckBox("Can Jump")
        self.prop_spawner_layout.addWidget(self.prop_jump_cb)
        self.prop_jump_label = QLabel("Jump Height:")
        self.prop_jump_input = QSpinBox()
        self.prop_jump_input.setRange(1, 15)
        self.prop_anim_jump_label = QLabel("Jump Anim:")
        self.prop_anim_jump_input = QLineEdit()
        self.prop_spawner_layout.addWidget(self.prop_jump_label)
        self.prop_spawner_layout.addWidget(self.prop_jump_input)
        self.prop_spawner_layout.addWidget(self.prop_anim_jump_label)
        self.prop_spawner_layout.addWidget(self.prop_anim_jump_input)

        self.prop_wall_jump_cb = QCheckBox("Can Wall Jump")
        self.prop_spawner_layout.addWidget(self.prop_wall_jump_cb)
        self.prop_anim_wall_slide_label = QLabel("Wall Slide Anim:")
        self.prop_anim_wall_slide_input = QLineEdit()
        self.prop_spawner_layout.addWidget(self.prop_anim_wall_slide_label)
        self.prop_spawner_layout.addWidget(self.prop_anim_wall_slide_input)
        
        self.prop_dash_cb = QCheckBox("Dash Attack")
        self.prop_spawner_layout.addWidget(self.prop_dash_cb)
        self.prop_anim_dash_label = QLabel("Dash Anim:")
        self.prop_anim_dash_input = QLineEdit()
        self.prop_spawner_layout.addWidget(self.prop_anim_dash_label)
        self.prop_spawner_layout.addWidget(self.prop_anim_dash_input)

        self.prop_shoot_cb = QCheckBox("Ranged Attack")
        self.prop_spawner_layout.addWidget(self.prop_shoot_cb)
        self.prop_weapon_img_label = QLabel("Weapon Image (e.g. gun.png):")
        self.prop_weapon_img_input = QLineEdit()
        self.prop_projectile_img_label = QLabel("Projectile Image (e.g. projectile.png):")
        self.prop_projectile_img_input = QLineEdit()
        
        self.prop_shoot_cd_label = QLabel("Shoot Cooldown (frames):")
        self.prop_shoot_cd_input = QSpinBox()
        self.prop_shoot_cd_input.setRange(10, 300)
        
        # НОВЕ: Повзунок для радіуса зору
        self.prop_vision_label = QLabel("Vision Range (blocks):")
        self.prop_vision_input = QSpinBox()
        self.prop_vision_input.setRange(1, 100)
        self.prop_vision_input.setSingleStep(1)
        
        self.prop_spawner_layout.addWidget(self.prop_weapon_img_label)
        self.prop_spawner_layout.addWidget(self.prop_weapon_img_input)
        self.prop_spawner_layout.addWidget(self.prop_projectile_img_label)
        self.prop_spawner_layout.addWidget(self.prop_projectile_img_input)
        self.prop_spawner_layout.addWidget(self.prop_shoot_cd_label)
        self.prop_spawner_layout.addWidget(self.prop_shoot_cd_input)
        self.prop_spawner_layout.addWidget(self.prop_vision_label)
        self.prop_spawner_layout.addWidget(self.prop_vision_input)
        
        self.properties_layout.addWidget(self.prop_spawner_container)
        
        self.btn_reset_props = QPushButton("Reset Properties")
        self.btn_reset_props.setStyleSheet("background-color: #d73a49; color: white; font-weight: bold; padding: 5px; margin-top: 15px;")
        self.properties_layout.addWidget(self.btn_reset_props)

        self.properties_layout.addStretch()
        
        self.properties_panel.setWidget(self.properties_widget)
        self.properties_panel.hide()

        # Підключення сигналів
        self.prop_type_combo.currentIndexChanged.connect(self.toggle_properties_ui)
        self.prop_preset_combo.currentIndexChanged.connect(self.toggle_spawner_features)
        self.prop_walk_cb.toggled.connect(self.toggle_spawner_features)
        self.prop_jump_cb.toggled.connect(self.toggle_spawner_features)
        self.prop_dash_cb.toggled.connect(self.toggle_spawner_features)
        self.prop_wall_jump_cb.toggled.connect(self.toggle_spawner_features)
        self.prop_shoot_cb.toggled.connect(self.toggle_spawner_features)
        self.btn_reset_props.clicked.connect(self.reset_folder_properties)
        
        inputs = [self.prop_anim_idle_input, self.prop_anim_walk_input, self.prop_anim_jump_input, 
                  self.prop_anim_wall_slide_input, self.prop_anim_dash_input,
                  self.prop_weapon_img_input, self.prop_projectile_img_input]
        for input_field in inputs:
            input_field.textChanged.connect(self.save_folder_properties)
        
        for w in [self.prop_type_combo, self.prop_preset_combo, self.prop_collision_cb, self.prop_visible_cb, 
                  self.prop_walk_cb, self.prop_shoot_cb, self.prop_jump_cb, self.prop_wall_jump_cb, self.prop_dash_cb,
                  self.prop_speed_input, self.prop_jump_input, self.prop_shoot_cd_input, self.prop_vision_input]:
            if isinstance(w, QComboBox): w.currentIndexChanged.connect(self.save_folder_properties)
            elif isinstance(w, QCheckBox): w.toggled.connect(self.save_folder_properties)
            else: w.valueChanged.connect(self.save_folder_properties)

        self.horizontal_splitter.addWidget(self.sidebar_panel)
        self.horizontal_splitter.addWidget(self.center_container)
        self.horizontal_splitter.addWidget(self.properties_panel)
        self.horizontal_splitter.setStretchFactor(1, 1)
        self.main_layout.addWidget(self.horizontal_splitter)

    def get_path_parts(self, index):
        parts = []
        item = self.tree_model.itemFromIndex(index)
        while item:
            parts.insert(0, item.text())
            item = item.parent()
        return parts

    def toggle_properties_ui(self):
        obj_type = self.prop_type_combo.currentText()
        is_spawner = (obj_type == "Spawner")
        is_killzone = (obj_type == "Kill Zone")
        is_block = (obj_type in ["Static Blocks", "Kill Zone"])
        
        self.prop_block_container.setVisible(is_block)
        self.prop_spawner_container.setVisible(is_spawner)
        
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
        self.prop_anim_walk_label.setVisible(is_walking)
        self.prop_anim_walk_input.setVisible(is_walking)
        
        self.prop_jump_cb.setVisible(is_player)
        is_jumping = is_player and self.prop_jump_cb.isChecked()
        self.prop_jump_label.setVisible(is_jumping)
        self.prop_jump_input.setVisible(is_jumping)
        self.prop_anim_jump_label.setVisible(is_jumping)
        self.prop_anim_jump_input.setVisible(is_jumping)

        self.prop_wall_jump_cb.setVisible(is_player)
        is_wall_jump = is_player and self.prop_wall_jump_cb.isChecked()
        self.prop_anim_wall_slide_label.setVisible(is_wall_jump)
        self.prop_anim_wall_slide_input.setVisible(is_wall_jump)
        
        self.prop_dash_cb.setVisible(is_player)
        is_dash = is_player and self.prop_dash_cb.isChecked()
        self.prop_anim_dash_label.setVisible(is_dash)
        self.prop_anim_dash_input.setVisible(is_dash)

        can_shoot_entity = is_player or is_enemy
        self.prop_shoot_cb.setVisible(can_shoot_entity)
        is_shooting = can_shoot_entity and self.prop_shoot_cb.isChecked()
        self.prop_weapon_img_label.setVisible(is_shooting)
        self.prop_weapon_img_input.setVisible(is_shooting)
        self.prop_projectile_img_label.setVisible(is_shooting)
        self.prop_projectile_img_input.setVisible(is_shooting)
        self.prop_shoot_cd_label.setVisible(is_shooting)
        self.prop_shoot_cd_input.setVisible(is_shooting)
        
        # Відображення радіуса зору тільки для ворогів
        self.prop_vision_label.setVisible(is_enemy)
        self.prop_vision_input.setVisible(is_enemy)

    def reset_folder_properties(self):
        if not self.current_selected_folder: return
        reply = QMessageBox.question(self, 'Reset Properties', 
                                     f"Reset '{self.current_selected_folder}' to a default solid block?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            widgets = [self.prop_type_combo, self.prop_preset_combo, self.prop_collision_cb, self.prop_visible_cb,
                      self.prop_walk_cb, self.prop_shoot_cb, self.prop_jump_cb, self.prop_wall_jump_cb, self.prop_dash_cb,
                      self.prop_speed_input, self.prop_jump_input, self.prop_shoot_cd_input, self.prop_vision_input,
                      self.prop_anim_idle_input, self.prop_anim_walk_input, self.prop_anim_jump_input,
                      self.prop_anim_dash_input, self.prop_anim_wall_slide_input,
                      self.prop_weapon_img_input, self.prop_projectile_img_input]
            for w in widgets: w.blockSignals(True)
            
            self.prop_type_combo.setCurrentText("Static Blocks")
            self.prop_preset_combo.setCurrentText("Enemy")
            self.prop_anim_idle_input.setText("enemy/idle")
            self.prop_anim_walk_input.setText("enemy/run")
            self.prop_anim_jump_input.setText("player/jump")
            self.prop_anim_dash_input.setText("player/slide")
            self.prop_anim_wall_slide_input.setText("player/wall_slide")
            self.prop_weapon_img_input.setText("gun.png")
            self.prop_projectile_img_input.setText("projectile.png")
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
            self.prop_vision_input.setValue(15) # 15 блоків (це 240 пікселів)
            
            self.toggle_properties_ui()
            for w in widgets: w.blockSignals(False)
            self.save_folder_properties()

    def on_folder_clicked(self, index):
        parts = self.get_path_parts(index)
        self.asset_list.clear()
        
        if parts[0] == "Tiles":
            if len(parts) == 2:
                self.btn_add_tiles.show()
                folder_name = parts[1]
                self.load_folder_properties(folder_name)
                if folder_name in self.assets:
                    for i, surf in enumerate(self.assets[folder_name]):
                        data = pygame.image.tostring(surf, 'RGBA')
                        qimg = QImage(data, surf.get_width(), surf.get_height(), QImage.Format_RGBA8888)
                        item = QListWidgetItem(QIcon(QPixmap.fromImage(qimg)), f"tile_{i}")
                        item.setSizeHint(QSize(80, 90))
                        self.asset_list.addItem(item)
            else:
                self.btn_add_tiles.hide()
                self.properties_panel.hide()
                self.current_selected_folder = None
                
        elif parts[0] == "Entities":
            self.properties_panel.hide() 
            self.current_selected_folder = None
            if len(parts) == 3: 
                self.btn_add_tiles.show()
                folder_path = os.path.join('data', 'images', 'entities', parts[1], parts[2])
                if os.path.exists(folder_path):
                    files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(valid_extensions)])
                    for f in files:
                        img_path = os.path.join(folder_path, f)
                        qimg = QImage(img_path)
                        item = QListWidgetItem(QIcon(QPixmap.fromImage(qimg)), f)
                        item.setSizeHint(QSize(80, 90))
                        self.asset_list.addItem(item)
            else:
                self.btn_add_tiles.hide()

    def load_folder_properties(self, folder_name):
        self.current_selected_folder = folder_name
        self.prop_title.setText(f"Properties: {folder_name}")
        self.properties_panel.show()
        
        widgets = [self.prop_type_combo, self.prop_preset_combo, self.prop_collision_cb, self.prop_visible_cb,
                  self.prop_walk_cb, self.prop_shoot_cb, self.prop_jump_cb, self.prop_wall_jump_cb, self.prop_dash_cb,
                  self.prop_speed_input, self.prop_jump_input, self.prop_shoot_cd_input, self.prop_vision_input,
                  self.prop_anim_idle_input, self.prop_anim_walk_input, self.prop_anim_jump_input,
                  self.prop_anim_dash_input, self.prop_anim_wall_slide_input,
                  self.prop_weapon_img_input, self.prop_projectile_img_input]
        for w in widgets: w.blockSignals(True)
        
        path = os.path.join('data', 'images', 'tiles', folder_name, 'properties.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                obj_type = data.get('type', "Static Blocks")
                self.prop_type_combo.setCurrentText(obj_type)
                self.prop_preset_combo.setCurrentText(data.get('preset', "Enemy"))
                
                self.prop_anim_idle_input.setText(data.get('anim_idle', 'enemy/idle'))
                self.prop_anim_walk_input.setText(data.get('anim_walk', 'enemy/run'))
                self.prop_anim_jump_input.setText(data.get('anim_jump', 'player/jump'))
                self.prop_anim_dash_input.setText(data.get('anim_dash', 'player/slide'))
                self.prop_anim_wall_slide_input.setText(data.get('anim_wall_slide', 'player/wall_slide'))
                self.prop_weapon_img_input.setText(data.get('weapon_img', 'gun.png'))
                self.prop_projectile_img_input.setText(data.get('projectile_img', 'projectile.png'))
                
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
                self.prop_vision_input.setValue(data.get('vision_range', 15)) # 15 блоків
        else:
            self.prop_type_combo.setCurrentText("Static Blocks")
            self.prop_anim_idle_input.setText("enemy/idle")
            self.prop_anim_walk_input.setText("enemy/run")
            self.prop_anim_jump_input.setText("player/jump")
            self.prop_anim_dash_input.setText("player/slide")
            self.prop_anim_wall_slide_input.setText("player/wall_slide")
            self.prop_weapon_img_input.setText("gun.png")
            self.prop_projectile_img_input.setText("projectile.png")
            self.prop_collision_cb.setChecked(True)
            self.prop_visible_cb.setChecked(True)
            self.prop_walk_cb.setChecked(False)
            self.prop_vision_input.setValue(15)
            
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
            'anim_idle': self.prop_anim_idle_input.text(),
            'anim_walk': self.prop_anim_walk_input.text(),
            'anim_jump': self.prop_anim_jump_input.text(),
            'anim_dash': self.prop_anim_dash_input.text(),
            'anim_wall_slide': self.prop_anim_wall_slide_input.text(),
            'weapon_img': self.prop_weapon_img_input.text(),
            'projectile_img': self.prop_projectile_img_input.text(),
            'collision': False if self.prop_type_combo.currentText() in ["Kill Zone", "Spawner"] else self.prop_collision_cb.isChecked(),
            'is_visible': self.prop_visible_cb.isChecked(), 
            'can_walk': self.prop_walk_cb.isChecked(),
            'can_shoot': self.prop_shoot_cb.isChecked(),
            'can_jump': self.prop_jump_cb.isChecked(),
            'can_wall_jump': self.prop_wall_jump_cb.isChecked(),
            'can_dash': self.prop_dash_cb.isChecked(),
            'walk_speed': self.prop_speed_input.value(),
            'jump_height': self.prop_jump_input.value(),
            'shoot_cooldown': self.prop_shoot_cd_input.value(),
            'vision_range': self.prop_vision_input.value()
        }
        try:
            with open(path, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)
        except FileNotFoundError:
            pass
            
    def on_tile_clicked(self, index):
        parts = self.get_path_parts(self.tree_view.currentIndex())
        if parts and parts[0] == "Tiles" and len(parts) == 2:
            self.viewport.set_current_tile(parts[1], index.row())
        else:
            self.viewport.set_current_tile(None, 0)

    def on_save_clicked(self):
        self.viewport.editor.tilemap.save('map.json')
        print("Мапу успішно збережено в map.json!")

    def on_play_clicked(self):
        if self.btn_play.text() == "▶ PLAY":
            self.btn_play.setText("■ STOP")
            self.btn_play.setStyleSheet("background-color: #d73a49; color: white; font-weight: bold;")
            self.sidebar_panel.hide()
            self.browser_scroll.hide()
            self.properties_panel.hide()
            QApplication.processEvents() 
            self.viewport.set_mode("PLAY")
            self.viewport.setFocus()
        else:
            self.btn_play.setText("▶ PLAY")
            self.btn_play.setStyleSheet("")
            
            try:
                pygame.mixer.music.stop()
                pygame.mixer.stop()
            except Exception:
                pass
                
            self.sidebar_panel.show()
            self.browser_scroll.show()
            if getattr(self, 'current_selected_folder', None): 
                self.properties_panel.show() 
            self.viewport.set_mode("EDITOR")
    
    def on_new_folder_clicked(self):
        index = self.tree_view.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "Error", "Select 'Tiles' or 'Entities' to create a folder there.")
            return
            
        parts = self.get_path_parts(index)
        root = parts[0]
        
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Name:")
        if not ok or not folder_name: return
            
        if root == "Tiles":
            path = os.path.join('data', 'images', 'tiles', folder_name)
            if not os.path.exists(path):
                os.makedirs(path) 
                self.assets[folder_name] = [] 
                self.root_tiles.appendRow(create_item(folder_name))
            else:
                QMessageBox.warning(self, "Error", "Folder already exists!")
                
        elif root == "Entities":
            if len(parts) <= 2: 
                path = os.path.join('data', 'images', 'entities', folder_name)
                if not os.path.exists(path):
                    os.makedirs(path)
                    os.makedirs(os.path.join(path, 'idle'))
                    os.makedirs(os.path.join(path, 'run'))
                    
                    ent_item = create_item(folder_name)
                    ent_item.appendRow(create_item("idle"))
                    ent_item.appendRow(create_item("run"))
                    self.root_entities.appendRow(ent_item)
                else:
                    QMessageBox.warning(self, "Error", "Entity already exists!")
            elif len(parts) == 3: 
                path = os.path.join('data', 'images', 'entities', parts[1], folder_name)
                if not os.path.exists(path):
                    os.makedirs(path)
                    item = self.tree_model.itemFromIndex(index).parent()
                    item.appendRow(create_item(folder_name))
                else:
                    QMessageBox.warning(self, "Error", "Animation already exists!")

    def on_add_tiles_clicked(self):
        index = self.tree_view.currentIndex()
        parts = self.get_path_parts(index)
        if not parts: return
        
        target_dir = ""
        if parts[0] == "Tiles" and len(parts) == 2:
            target_dir = os.path.join('data', 'images', 'tiles', parts[1])
        elif parts[0] == "Entities" and len(parts) == 3:
            target_dir = os.path.join('data', 'images', 'entities', parts[1], parts[2])
        else:
            return
            
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png)")
        if files:
            old_files = sorted([f for f in os.listdir(target_dir) if f.lower().endswith(valid_extensions)]) if os.path.exists(target_dir) else []
            for file_path in files:
                shutil.copy(file_path, os.path.join(target_dir, os.path.basename(file_path)))
            
            if parts[0] == "Tiles":
                new_files = sorted([f for f in os.listdir(target_dir) if f.lower().endswith(valid_extensions)])
                mapping = {}
                for i, old_file in enumerate(old_files):
                    if old_file in new_files:
                        mapping[i] = new_files.index(old_file)
                        
                editor_tilemap = self.viewport.editor.tilemap
                folder_name = parts[1]
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
        parts = self.get_path_parts(index)
        if len(parts) == 1: return 
        
        menu = QMenu()
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        action = menu.exec(self.tree_view.viewport().mapToGlobal(position))
        
        if action == rename_action:
            self.rename_folder(index, parts)
        elif action == delete_action:
            self.delete_folder(index, parts)

    def rename_folder(self, index, parts):
        old_name = parts[-1]
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=old_name)
        if ok and new_name and new_name != old_name:
            if parts[0] == "Tiles":
                old_path = os.path.join('data', 'images', 'tiles', old_name)
                new_path = os.path.join('data', 'images', 'tiles', new_name)
            elif parts[0] == "Entities":
                if len(parts) == 2:
                    old_path = os.path.join('data', 'images', 'entities', old_name)
                    new_path = os.path.join('data', 'images', 'entities', new_name)
                else:
                    old_path = os.path.join('data', 'images', 'entities', parts[1], old_name)
                    new_path = os.path.join('data', 'images', 'entities', parts[1], new_name)

            if not os.path.exists(new_path):
                try:
                    os.rename(old_path, new_path) 
                    if parts[0] == "Tiles":
                        self.assets[new_name] = self.assets.pop(old_name) 
                        if getattr(self, 'current_selected_folder', None) == old_name:
                            self.load_folder_properties(new_name)
                    self.tree_model.itemFromIndex(index).setText(new_name)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not rename: {e}")
            else:
                QMessageBox.warning(self, "Error", "Folder already exists!")

    def delete_folder(self, index, parts):
        folder_name = parts[-1]
        reply = QMessageBox.question(self, 'Delete', f"Delete '{folder_name}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if parts[0] == "Tiles":
                    path = os.path.join('data', 'images', 'tiles', folder_name)
                    if os.path.exists(path): shutil.rmtree(path)
                    if folder_name in self.assets: del self.assets[folder_name]

                    editor_tilemap = self.viewport.editor.tilemap
                    keys_to_delete = [loc for loc, tile in editor_tilemap.tilemap.items() if tile['type'] == folder_name]
                    for loc in keys_to_delete: del editor_tilemap.tilemap[loc]
                    editor_tilemap.offgrid_tiles = [t for t in editor_tilemap.offgrid_tiles if t['type'] != folder_name]
                    
                    if self.viewport.current_tile_group == folder_name:
                        self.viewport.set_current_tile(None, 0)
                        
                elif parts[0] == "Entities":
                    if len(parts) == 2: path = os.path.join('data', 'images', 'entities', folder_name)
                    else: path = os.path.join('data', 'images', 'entities', parts[1], folder_name)
                    if os.path.exists(path): shutil.rmtree(path)

                self.tree_model.itemFromIndex(index).parent().removeRow(index.row())
                self.asset_list.clear()
                self.btn_add_tiles.hide()
                self.properties_panel.hide()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete: {e}")
    
    def show_tile_context_menu(self, position):
        item = self.asset_list.itemAt(position)
        if not item: return
        menu = QMenu()
        delete_action = menu.addAction("Delete image")
        action = menu.exec(self.asset_list.viewport().mapToGlobal(position))
        if action == delete_action:
            self.delete_tile(item)

    def delete_tile(self, item):
        row = self.asset_list.row(item) 
        index = self.tree_view.currentIndex()
        parts = self.get_path_parts(index)
        
        reply = QMessageBox.question(self, 'Delete', "Delete this image?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if parts[0] == "Tiles":
                    folder_name = parts[1]
                    folder_path = os.path.join('data', 'images', 'tiles', folder_name)
                    files = sorted([f for f in os.listdir(folder_path) if f.endswith(valid_extensions)])
                    if row < len(files):
                        os.remove(os.path.join(folder_path, files[row]))
                        del self.assets[folder_name][row]
                        
                        editor_tilemap = self.viewport.editor.tilemap
                        keys_to_delete = []
                        for loc, t in editor_tilemap.tilemap.items():
                            if t['type'] == folder_name:
                                if t['variant'] == row: keys_to_delete.append(loc)
                                elif t['variant'] > row: t['variant'] -= 1 
                        for loc in keys_to_delete: del editor_tilemap.tilemap[loc]
                            
                        tiles_to_keep = []
                        for t in editor_tilemap.offgrid_tiles:
                            if t['type'] == folder_name:
                                if t['variant'] == row: continue 
                                elif t['variant'] > row: t['variant'] -= 1 
                            tiles_to_keep.append(t)
                        editor_tilemap.offgrid_tiles = tiles_to_keep
                        
                        if self.viewport.current_tile_group == folder_name:
                            if self.viewport.current_tile_variant == row: self.viewport.set_current_tile(None, 0)
                            elif self.viewport.current_tile_variant > row: self.viewport.set_current_tile(folder_name, self.viewport.current_tile_variant - 1)
                
                elif parts[0] == "Entities":
                    folder_path = os.path.join('data', 'images', 'entities', parts[1], parts[2])
                    files = sorted([f for f in os.listdir(folder_path) if f.endswith(valid_extensions)])
                    if row < len(files):
                        os.remove(os.path.join(folder_path, files[row]))

                self.on_folder_clicked(index)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete: {e}")
                                            
    def load_stylesheet(self):
        try:
            with open("ui/styles.qss", "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError: pass