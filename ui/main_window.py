import sys
import os
import shutil
import json
import pygame
from PySide6.QtWidgets import (QMainWindow, QInputDialog, QFileDialog, QMessageBox, QApplication, QMenu, QComboBox, QCheckBox, QListWidgetItem, QPushButton, QHBoxLayout, QLabel, QSlider, QLineEdit)
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap, QImage
from scripts.utils import load_images
from ui.main_window_ui import setup_ui, create_item

valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')

class MainWindow(QMainWindow):
    def __init__(self, assets):
        super().__init__()
        self.setWindowTitle("NumiEngine")
        self.resize(1280, 720)
        self.assets = assets 
        self.current_selected_folder = None 
        
        setup_ui(self, assets)
        
        # НОВЕ: Динамічно додаємо поле для анімації смерті в контейнер спавнера
        self.prop_anim_die_label = QLabel("Death Effect (Anim):")
        self.prop_anim_die_input = QLineEdit("particle/particle")
        self.prop_spawner_container.layout().addWidget(self.prop_anim_die_label)
        self.prop_spawner_container.layout().addWidget(self.prop_anim_die_input)
        
        self.btn_toggle_editor = QPushButton("🎨 Menu Editor")
        self.btn_toggle_editor.setCheckable(True)
        self.btn_toggle_editor.setToolTip("Switch between Level Editor and UI Editor")
        self.toolbar_layout.insertWidget(4, self.btn_toggle_editor)
        self.btn_toggle_editor.toggled.connect(self.on_editor_mode_toggled)
        
        os.makedirs('data/maps', exist_ok=True)
        if os.path.exists('map.json') and not os.path.exists('data/maps/0.json'):
            shutil.move('map.json', 'data/maps/0.json')
            
        self.update_map_list()
        
        current_map = self.map_combo.currentText()
        if current_map:
            self.on_map_changed(current_map)

        self.map_combo.currentTextChanged.connect(self.on_map_changed)
        self.btn_new_map.clicked.connect(self.on_new_map_clicked)
        self.btn_save.clicked.connect(self.on_save_clicked)
        self.btn_play.clicked.connect(self.on_play_clicked)
        self.tree_view.clicked.connect(self.on_folder_clicked)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        self.btn_new_folder.clicked.connect(self.on_new_folder_clicked)
        self.btn_add_tiles.clicked.connect(self.on_add_tiles_clicked)
        self.btn_add_audio.clicked.connect(self.on_add_audio_clicked)
        self.asset_list.clicked.connect(self.on_tile_clicked)
        self.asset_list.customContextMenuRequested.connect(self.show_tile_context_menu)
        
        self.prop_type_combo.currentIndexChanged.connect(self.toggle_properties_ui)
        self.prop_preset_combo.currentIndexChanged.connect(self.toggle_spawner_features)
        self.prop_walk_cb.toggled.connect(self.toggle_spawner_features)
        self.prop_jump_cb.toggled.connect(self.toggle_spawner_features)
        self.prop_dash_cb.toggled.connect(self.toggle_spawner_features)
        self.prop_wall_jump_cb.toggled.connect(self.toggle_spawner_features)
        self.prop_shoot_cb.toggled.connect(self.toggle_spawner_features)
        self.btn_reset_props.clicked.connect(self.reset_folder_properties)
        self.btn_clear_bg.clicked.connect(self.clear_background)
        
        inputs = [self.prop_anim_idle_input, self.prop_anim_walk_input, self.prop_anim_jump_input, 
                  self.prop_anim_wall_slide_input, self.prop_anim_dash_input,
                  self.prop_weapon_img_input, self.prop_projectile_img_input,
                  self.prop_sfx_hit_input, self.prop_sfx_jump_input, 
                  self.prop_sfx_dash_input, self.prop_sfx_shoot_input,
                  self.prop_anim_die_input] # ДОДАНО СЮДИ
        for input_field in inputs:
            input_field.textChanged.connect(self.save_folder_properties)
        
        for w in [self.prop_type_combo, self.prop_preset_combo, self.prop_collision_cb, self.prop_visible_cb, 
                  self.prop_walk_cb, self.prop_shoot_cb, self.prop_jump_cb, self.prop_wall_jump_cb, self.prop_dash_cb,
                  self.prop_speed_input, self.prop_jump_input, self.prop_shoot_cd_input, self.prop_vision_input]:
            if isinstance(w, QComboBox): w.currentIndexChanged.connect(self.save_folder_properties)
            elif isinstance(w, QCheckBox): w.toggled.connect(self.save_folder_properties)
            else: w.valueChanged.connect(self.save_folder_properties)
            
        if hasattr(self, 'prop_ui_text_input'):
            self.prop_ui_text_input.textChanged.connect(self.save_folder_properties)
            self.prop_ui_action_combo.currentIndexChanged.connect(self.save_folder_properties)
            self.prop_ui_target_input.textChanged.connect(self.save_folder_properties)
            
    def on_editor_mode_toggled(self, checked):
        if checked:
            self.btn_toggle_editor.setText("🌍 Level Editor")
            self.btn_toggle_editor.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
            self.viewport.set_mode("MENU_EDITOR")
            self.prop_title.setText("Properties: UI Editor")
        else:
            self.btn_toggle_editor.setText("🎨 Menu Editor")
            self.btn_toggle_editor.setStyleSheet("")
            self.viewport.set_mode("EDITOR")
            self.prop_title.setText("Properties")
            
        self.update_map_list()
        
        current_map = self.map_combo.currentText()
        if current_map:
            self.on_map_changed(current_map)

    def closeEvent(self, event):
        self.on_save_clicked()
        event.accept()

    def update_map_list(self):
        self.map_combo.blockSignals(True)
        self.map_combo.clear()
        
        is_menu_mode = self.btn_toggle_editor.isChecked()
        valid_maps = []
        
        map_files = sorted([f for f in os.listdir('data/maps') if f.endswith('.json')])
        
        for f_name in map_files:
            path = f'data/maps/{f_name}'
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    is_menu_file = data.get('is_menu', False)
                    
                    if is_menu_mode and is_menu_file:
                        valid_maps.append(f_name)
                    elif not is_menu_mode and not is_menu_file:
                        valid_maps.append(f_name)
            except:
                pass
                
        if not valid_maps:
            default_name = "main_menu.json" if is_menu_mode else "0.json"
            path = f'data/maps/{default_name}'
            with open(path, 'w') as f:
                if is_menu_mode:
                    json.dump({'is_menu': True, 'ui_elements': []}, f)
                else:
                    json.dump({'tilemap': {}, 'tile_size': 16, 'offgrid': []}, f)
            valid_maps = [default_name]
            
        self.map_combo.addItems(valid_maps)
        self.map_combo.blockSignals(False)

    def on_map_changed(self, map_name):
        if map_name:
            path = f'data/maps/{map_name}'
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if data.get('is_menu', False):
                    self.viewport.set_mode("MENU_EDITOR")
                    self.viewport.menu_editor.load(path)
                    
                    bg_path = getattr(self.viewport.menu_editor, 'bg_path', None)
                    if hasattr(self, 'prop_current_bg_label'):
                        self.prop_current_bg_label.setText(f"Active BG: {bg_path if bg_path else 'None'}")
                        self.prop_current_music_label.setText(f"Active Music: None (UI Mode)")
                else:
                    self.viewport.set_mode("EDITOR")
                    self.viewport.editor.tilemap.load(path)
                    
                    bg_path = getattr(self.viewport.editor.tilemap, 'bg_path', None)
                    bg_music = getattr(self.viewport.editor.tilemap, 'bg_music', None)
                    if hasattr(self, 'prop_current_bg_label'):
                        self.prop_current_bg_label.setText(f"Active BG: {bg_path if bg_path else 'None'}")
                        self.prop_current_music_label.setText(f"Active Music: {bg_music if bg_music else 'None'}")
            except Exception as e:
                print(f"Error loading map: {e}")

    def on_new_map_clicked(self):
        name, ok = QInputDialog.getText(self, "New Map", "Map name (e.g., '1' or 'main_menu'):")
        if ok and name:
            file_name = f"{name}.json"
            path = os.path.join('data/maps', file_name)
            if not os.path.exists(path):
                if self.btn_toggle_editor.isChecked():
                    with open(path, 'w') as f:
                        json.dump({'is_menu': True, 'ui_elements': []}, f)
                else:
                    with open(path, 'w') as f:
                        json.dump({'tilemap': {}, 'tile_size': 16, 'offgrid': []}, f)
                        
                self.update_map_list()
                self.map_combo.setCurrentText(file_name)
            else:
                QMessageBox.warning(self, "Error", "Map already exists!")
                
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
        is_bg = (obj_type == "Background")
        is_ui_btn = (obj_type == "UI Button")
        is_block = (obj_type in ["Static Blocks", "Kill Zone", "Level Exit"])
        
        self.prop_block_container.setVisible(is_block)
        self.prop_spawner_container.setVisible(is_spawner)
        self.prop_bg_container.setVisible(is_bg)
        
        if hasattr(self, 'prop_ui_btn_container'):
            self.prop_ui_btn_container.setVisible(is_ui_btn)
            
        if hasattr(self, 'sfx_container'):
            self.sfx_container.setVisible(is_spawner)
            self.sfx_divider.setVisible(is_spawner)
            self.sfx_title_label.setVisible(is_spawner)
        
        if is_killzone or is_spawner or is_bg or is_ui_btn:
            self.prop_collision_cb.setChecked(False)
            
        if is_killzone or is_bg or is_ui_btn:
            self.prop_collision_cb.setVisible(False)
        else:
            self.prop_collision_cb.setVisible(True)
            
        if is_spawner:
            self.toggle_spawner_features()
    
    def clear_background(self):
        if self.viewport.mode == "MENU_EDITOR":
            self.viewport.menu_editor.bg_path = None
        else:
            self.viewport.editor.tilemap.bg_path = None
            self.viewport.editor.tilemap.bg_music = None
        self.prop_current_bg_label.setText("Active BG: None")
        self.prop_current_music_label.setText("Active Music: None")
            
    def toggle_spawner_features(self):
        preset = self.prop_preset_combo.currentText()
        is_player = (preset == "Player")
        is_enemy = (preset == "Enemy")
        is_entity = is_player or is_enemy
        
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
        
        self.prop_vision_label.setVisible(is_enemy)
        self.prop_vision_input.setVisible(is_enemy)
        
        self.prop_anim_die_label.setVisible(is_entity)
        self.prop_anim_die_input.setVisible(is_entity)

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
                      self.prop_weapon_img_input, self.prop_projectile_img_input,
                      self.prop_sfx_hit_input, self.prop_sfx_jump_input, 
                      self.prop_sfx_dash_input, self.prop_sfx_shoot_input,
                      self.prop_anim_die_input]
            for w in widgets: w.blockSignals(True)
            
            self.prop_type_combo.setCurrentText("Static Blocks")
            self.prop_preset_combo.setCurrentText("Enemy")
            self.prop_anim_idle_input.setText("enemy/idle")
            self.prop_anim_walk_input.setText("enemy/run")
            self.prop_anim_jump_input.setText("player/jump")
            self.prop_anim_dash_input.setText("player/slide")
            self.prop_anim_wall_slide_input.setText("player/wall_slide")
            self.prop_anim_die_input.setText("particle/particle")
            self.prop_weapon_img_input.setText("gun.png")
            self.prop_projectile_img_input.setText("projectile.png")
            self.prop_sfx_hit_input.setText("hit.wav")
            self.prop_sfx_jump_input.setText("jump.wav")
            self.prop_sfx_dash_input.setText("dash.wav")
            self.prop_sfx_shoot_input.setText("shoot.wav")
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
            self.prop_vision_input.setValue(15) 
            
            self.toggle_properties_ui()
            for w in widgets: w.blockSignals(False)
            self.save_folder_properties()

    def load_folder_properties(self, folder_name):
        self.current_selected_folder = folder_name
        self.prop_title.setText(f"Properties: {folder_name}")
        self.properties_panel.show()
        
        if self.viewport.mode == "MENU_EDITOR":
            bg_path = getattr(self.viewport.menu_editor, 'bg_path', None)
            bg_music = None
        else:
            bg_path = getattr(self.viewport.editor.tilemap, 'bg_path', None)
            bg_music = getattr(self.viewport.editor.tilemap, 'bg_music', None)
            
        if hasattr(self, 'prop_current_bg_label'):
            self.prop_current_bg_label.setText(f"Active BG: {bg_path if bg_path else 'None'}")
            self.prop_current_music_label.setText(f"Active Music: {bg_music if bg_music else 'None'}")
        
        widgets = [self.prop_type_combo, self.prop_preset_combo, self.prop_collision_cb, self.prop_visible_cb,
                  self.prop_walk_cb, self.prop_shoot_cb, self.prop_jump_cb, self.prop_wall_jump_cb, self.prop_dash_cb,
                  self.prop_speed_input, self.prop_jump_input, self.prop_shoot_cd_input, self.prop_vision_input,
                  self.prop_anim_idle_input, self.prop_anim_walk_input, self.prop_anim_jump_input,
                  self.prop_anim_dash_input, self.prop_anim_wall_slide_input,
                  self.prop_weapon_img_input, self.prop_projectile_img_input,
                  self.prop_sfx_hit_input, self.prop_sfx_jump_input, 
                  self.prop_sfx_dash_input, self.prop_sfx_shoot_input,
                  self.prop_sfx_hit_slider, self.prop_sfx_jump_slider,
                  self.prop_sfx_dash_slider, self.prop_sfx_shoot_slider,
                  self.prop_anim_die_input]
        
        if hasattr(self, 'prop_ui_text_input'):
            widgets.extend([self.prop_ui_text_input, self.prop_ui_action_combo, self.prop_ui_target_input])
            
        for w in widgets: w.blockSignals(True)
        
        path = os.path.join('data', 'images', 'tiles', folder_name, 'properties.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                obj_type = data.get('type', "Static Blocks")
                self.prop_type_combo.setCurrentText(obj_type)
                self.prop_preset_combo.setCurrentText(data.get('preset', "Enemy"))
                
                if hasattr(self, 'prop_ui_text_input'):
                    self.prop_ui_text_input.setText(data.get('ui_text', 'Button'))
                    self.prop_ui_action_combo.setCurrentText(data.get('ui_action', 'load_map'))
                    self.prop_ui_target_input.setText(data.get('ui_target', '1.json'))
                
                self.prop_anim_idle_input.setText(data.get('anim_idle', 'enemy/idle'))
                self.prop_anim_walk_input.setText(data.get('anim_walk', 'enemy/run'))
                self.prop_anim_jump_input.setText(data.get('anim_jump', 'player/jump'))
                self.prop_anim_dash_input.setText(data.get('anim_dash', 'player/slide'))
                self.prop_anim_wall_slide_input.setText(data.get('anim_wall_slide', 'player/wall_slide'))
                self.prop_anim_die_input.setText(data.get('anim_die', 'particle/particle'))
                self.prop_weapon_img_input.setText(data.get('weapon_img', 'gun.png'))
                self.prop_projectile_img_input.setText(data.get('projectile_img', 'projectile.png'))
                
                sfx_hit = data.get('sfx_hit', 'hit.wav')
                sfx_jump = data.get('sfx_jump', 'jump.wav')
                sfx_dash = data.get('sfx_dash', 'dash.wav')
                sfx_shoot = data.get('sfx_shoot', 'shoot.wav')
                
                self.prop_sfx_hit_input.setText(sfx_hit)
                self.prop_sfx_jump_input.setText(sfx_jump)
                self.prop_sfx_dash_input.setText(sfx_dash)
                self.prop_sfx_shoot_input.setText(sfx_shoot)
                
                vols = data.get('sfx_volumes', {})
                self.prop_sfx_hit_slider.setValue(vols.get(sfx_hit, 60))
                self.prop_sfx_jump_slider.setValue(vols.get(sfx_jump, 60))
                self.prop_sfx_dash_slider.setValue(vols.get(sfx_dash, 60))
                self.prop_sfx_shoot_slider.setValue(vols.get(sfx_shoot, 60))
                
                default_col = False if obj_type in ["Kill Zone", "Spawner", "Background", "Level Exit", "UI Button"] else True
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
                self.prop_vision_input.setValue(data.get('vision_range', 15)) 
        else:
            self.prop_type_combo.setCurrentText("Static Blocks")
            self.prop_anim_idle_input.setText("enemy/idle")
            self.prop_anim_walk_input.setText("enemy/run")
            self.prop_anim_jump_input.setText("player/jump")
            self.prop_anim_dash_input.setText("player/slide")
            self.prop_anim_wall_slide_input.setText("player/wall_slide")
            self.prop_anim_die_input.setText("particle/particle")
            self.prop_weapon_img_input.setText("gun.png")
            self.prop_projectile_img_input.setText("projectile.png")
            self.prop_sfx_hit_input.setText("hit.wav")
            self.prop_sfx_jump_input.setText("jump.wav")
            self.prop_sfx_dash_input.setText("dash.wav")
            self.prop_sfx_shoot_input.setText("shoot.wav")
            self.prop_sfx_hit_slider.setValue(60)
            self.prop_sfx_jump_slider.setValue(60)
            self.prop_sfx_dash_slider.setValue(60)
            self.prop_sfx_shoot_slider.setValue(60)
            self.prop_collision_cb.setChecked(True)
            self.prop_visible_cb.setChecked(True)
            self.prop_walk_cb.setChecked(False)
            self.prop_vision_input.setValue(15)
            
        self.toggle_properties_ui()
        for w in widgets: w.blockSignals(False)
    
    def save_folder_properties(self):
        if self.viewport.mode == "MENU_EDITOR":
            sel_idx = getattr(self.viewport.menu_editor, 'selected_index', None)
            if sel_idx is not None and sel_idx < len(self.viewport.menu_editor.ui_elements):
                el = self.viewport.menu_editor.ui_elements[sel_idx]
                if hasattr(self, 'prop_ui_text_input'):
                    el['text'] = self.prop_ui_text_input.text()
                    el['action'] = self.prop_ui_action_combo.currentText()
                    el['target'] = self.prop_ui_target_input.text()
            return
        
        if not self.current_selected_folder: return
        folder_dir = os.path.join('data', 'images', 'tiles', self.current_selected_folder)
        if not os.path.exists(folder_dir): return
            
        path = os.path.join(folder_dir, 'properties.json')
        
        volumes = {}
        if hasattr(self, 'prop_sfx_hit_input'):
            volumes = {
                self.prop_sfx_hit_input.text(): self.prop_sfx_hit_slider.value(),
                self.prop_sfx_jump_input.text(): self.prop_sfx_jump_slider.value(),
                self.prop_sfx_dash_input.text(): self.prop_sfx_dash_slider.value(),
                self.prop_sfx_shoot_input.text(): self.prop_sfx_shoot_slider.value()
            }
        
        data = {
            'type': self.prop_type_combo.currentText(),
            'preset': self.prop_preset_combo.currentText(),
            'anim_idle': self.prop_anim_idle_input.text(),
            'anim_walk': self.prop_anim_walk_input.text(),
            'anim_jump': self.prop_anim_jump_input.text(),
            'anim_dash': self.prop_anim_dash_input.text(),
            'anim_wall_slide': self.prop_anim_wall_slide_input.text(),
            'anim_die': self.prop_anim_die_input.text(), # ДОДАНО СЮДИ
            'weapon_img': self.prop_weapon_img_input.text(),
            'projectile_img': self.prop_projectile_img_input.text(),
            'sfx_hit': self.prop_sfx_hit_input.text() if hasattr(self, 'prop_sfx_hit_input') else 'hit.wav',
            'sfx_jump': self.prop_sfx_jump_input.text() if hasattr(self, 'prop_sfx_jump_input') else 'jump.wav',
            'sfx_dash': self.prop_sfx_dash_input.text() if hasattr(self, 'prop_sfx_dash_input') else 'dash.wav',
            'sfx_shoot': self.prop_sfx_shoot_input.text() if hasattr(self, 'prop_sfx_shoot_input') else 'shoot.wav',
            'sfx_volumes': volumes,
            
            'ui_text': self.prop_ui_text_input.text() if hasattr(self, 'prop_ui_text_input') else 'Button',
            'ui_action': self.prop_ui_action_combo.currentText() if hasattr(self, 'prop_ui_action_combo') else 'load_map',
            'ui_target': self.prop_ui_target_input.text() if hasattr(self, 'prop_ui_target_input') else '1.json',
            
            'collision': False if self.prop_type_combo.currentText() in ["Kill Zone", "Spawner", "Background", "Level Exit", "UI Button"] else self.prop_collision_cb.isChecked(),
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
    
    def on_ui_element_selected(self):
        sel_idx = getattr(self.viewport.menu_editor, 'selected_index', None)
        
        if sel_idx is not None and sel_idx < len(self.viewport.menu_editor.ui_elements):
            el = self.viewport.menu_editor.ui_elements[sel_idx]
            
            self.properties_panel.show()
            self.prop_title.setText(f"Properties: Selected Button")
            
            if hasattr(self, 'prop_ui_text_input'):
                self.prop_ui_text_input.blockSignals(True)
                self.prop_ui_action_combo.blockSignals(True)
                self.prop_ui_target_input.blockSignals(True)
                
                self.prop_ui_text_input.setText(el.get('text', 'Button'))
                self.prop_ui_action_combo.setCurrentText(el.get('action', 'load_map'))
                self.prop_ui_target_input.setText(el.get('target', '1.json'))
                
                self.prop_ui_text_input.blockSignals(False)
                self.prop_ui_action_combo.blockSignals(False)
                self.prop_ui_target_input.blockSignals(False)
            
            self.prop_type_combo.blockSignals(True)
            self.prop_type_combo.setCurrentText("UI Button")
            self.prop_type_combo.blockSignals(False)
            self.toggle_properties_ui()
        else:
            self.properties_panel.hide()
            self.prop_title.setText("Properties")
            
    def on_folder_clicked(self, index):
        parts = self.get_path_parts(index)
        self.asset_list.clear()
        
        self.btn_add_audio.hide() 
        self.btn_add_tiles.hide()
        
        if parts[0] == "Tiles":
            self.browser_scroll.show() 
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
                self.properties_panel.hide()
                self.current_selected_folder = None
                
        elif parts[0] == "Entities":
            self.browser_scroll.show() 
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

        elif parts[0] == "Audio":
            self.browser_scroll.hide() 
            self.properties_panel.hide()
            self.current_selected_folder = None
            if len(parts) == 1: 
                self.btn_add_audio.show()
            elif len(parts) == 2: 
                if self.prop_type_combo.currentText() == "Background":
                    self.viewport.editor.tilemap.bg_music = parts[1]
                    self.prop_current_music_label.setText(f"Active Music: {parts[1]}")
                    self.properties_panel.show() 
            
    def on_tile_clicked(self, index):
        parts = self.get_path_parts(self.tree_view.currentIndex())
        if parts and parts[0] == "Tiles" and len(parts) == 2:
            if self.prop_type_combo.currentText() == "Background":
                bg_str = f"{parts[1]}/{index.row()}"
                
                if self.viewport.mode == "MENU_EDITOR":
                    self.viewport.menu_editor.bg_path = bg_str
                else:
                    self.viewport.editor.tilemap.bg_path = bg_str
                    
                if hasattr(self, 'prop_current_bg_label'):
                    self.prop_current_bg_label.setText(f"Active BG: {parts[1]} (Image {index.row()})")
                self.viewport.set_current_tile(None, 0)
            else:
                self.viewport.set_current_tile(parts[1], index.row())
        else:
            self.viewport.set_current_tile(None, 0)

    def on_save_clicked(self):
        map_name = self.map_combo.currentText()
        if map_name:
            path = f'data/maps/{map_name}'
            if self.viewport.mode == "MENU_EDITOR":
                self.viewport.menu_editor.save(path)
                print(f"Меню успішно збережено в {path}!")
            else:
                self.viewport.editor.tilemap.save(path)
                print(f"Мапу успішно збережено в {path}!")

    def on_play_clicked(self):
        if self.btn_play.text() == "▶ PLAY":
            self.on_save_clicked() 
            with open('data/maps/current_play.txt', 'w') as f:
                f.write(self.map_combo.currentText())
                
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
            
            current_index = self.tree_view.currentIndex()
            if current_index.isValid():
                parts = self.get_path_parts(current_index)
                if parts[0] != "Audio":
                    self.browser_scroll.show()
            else:
                self.browser_scroll.show()

            if getattr(self, 'current_selected_folder', None): 
                self.properties_panel.show() 
                
            if self.btn_toggle_editor.isChecked():
                self.viewport.set_mode("MENU_EDITOR")
            else:
                self.viewport.set_mode("EDITOR")
    
    def on_new_folder_clicked(self):
        index = self.tree_view.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "Error", "Select 'Tiles' or 'Entities' to create a folder there.")
            return
            
        parts = self.get_path_parts(index)
        root = parts[0]
        if root == "Audio": return
        
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

    def on_add_audio_clicked(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Audio", "", "Audio (*.wav *.mp3 *.ogg)")
        if files:
            target_dir = os.path.join('data', 'sfx')
            os.makedirs(target_dir, exist_ok=True)
            for file_path in files:
                file_name = os.path.basename(file_path)
                shutil.copy(file_path, os.path.join(target_dir, file_name))
                
                existing = [self.root_audio.child(i).text() for i in range(self.root_audio.rowCount())]
                if file_name not in existing:
                    self.root_audio.appendRow(create_item(file_name))

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
            elif parts[0] == "Audio" and len(parts) == 2:
                old_path = os.path.join('data', 'sfx', old_name)
                new_path = os.path.join('data', 'sfx', new_name)

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
                QMessageBox.warning(self, "Error", "File/Folder already exists!")

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
                    
                elif parts[0] == "Audio" and len(parts) == 2:
                    path = os.path.join('data', 'sfx', folder_name)
                    if os.path.exists(path): os.remove(path)

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