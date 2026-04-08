import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QFrame, 
                             QSplitter, QPushButton, QLabel, QListWidget, QScrollArea,
                             QComboBox, QCheckBox, QDoubleSpinBox, QSpinBox, QLineEdit, QSlider, QTextEdit)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QStandardItemModel, QStandardItem
from ui.pygame_widget import NumiViewport 

def create_item(text):
    item = QStandardItem(text)
    item.setEditable(False)
    return item

def setup_ui(main_window, assets):
    main_window.central_widget = QWidget()
    main_window.setCentralWidget(main_window.central_widget)
    main_window.main_layout = QVBoxLayout(main_window.central_widget)
    main_window.main_layout.setContentsMargins(0, 0, 0, 0)
    main_window.main_layout.setSpacing(0)

    main_window.toolbar = QFrame()
    main_window.toolbar.setFixedHeight(45)
    main_window.toolbar.setObjectName("Toolbar")
    
    main_window.toolbar_layout = QHBoxLayout(main_window.toolbar)
    main_window.toolbar_layout.setContentsMargins(10, 5, 10, 5)
    main_window.toolbar_layout.setSpacing(8)

    # Блок 1: Керування мапами
    main_window.toolbar_layout.addWidget(QLabel("Map:"))
    main_window.map_combo = QComboBox()
    main_window.map_combo.setMinimumWidth(120)
    main_window.toolbar_layout.addWidget(main_window.map_combo)
    
    main_window.btn_new_map = QPushButton("+ New")
    main_window.btn_delete_map = QPushButton("❌ Delete")
    main_window.btn_delete_map.setStyleSheet("color: #f44336;")
    main_window.toolbar_layout.addWidget(main_window.btn_new_map)
    main_window.toolbar_layout.addWidget(main_window.btn_delete_map)

    # Розділювач
    div1 = QFrame()
    div1.setFrameShape(QFrame.VLine)
    div1.setStyleSheet("color: #444;")
    main_window.toolbar_layout.addWidget(div1)

    # Блок 2: Режими та Пауза
    main_window.btn_change_type = QPushButton("🔄 Type") 
    main_window.btn_change_type.setToolTip("Змінити тип карти (Меню <-> Ігровий Рівень)")
    main_window.btn_toggle_editor = QPushButton("🎨 Menu Editor")
    main_window.btn_toggle_editor.setCheckable(True)
    main_window.btn_set_pause = QPushButton("⏸ Set as Pause")
    main_window.btn_set_pause.setStyleSheet("color: #ffeb3b;")
    main_window.btn_set_pause.hide() 
    
    main_window.toolbar_layout.addWidget(main_window.btn_change_type)
    main_window.toolbar_layout.addWidget(main_window.btn_toggle_editor)
    main_window.toolbar_layout.addWidget(main_window.btn_set_pause)

    # Розділювач
    div2 = QFrame()
    div2.setFrameShape(QFrame.VLine)
    div2.setStyleSheet("color: #444;")
    main_window.toolbar_layout.addWidget(div2)

    # Блок 3: Білд та Сюжет
    main_window.btn_level_sequence = QPushButton("🚥 Sequence")
    main_window.btn_game_settings = QPushButton("⚙️ Game Settings")
    main_window.btn_game_settings.setToolTip("Налаштувати назву та іконку вікна гри")
    main_window.btn_build_game = QPushButton("🚀 Build Game")
    main_window.btn_build_game.setStyleSheet("background-color: #007acc; color: white; border: none; font-weight: bold;")
    
    main_window.toolbar_layout.addWidget(main_window.btn_level_sequence)
    main_window.toolbar_layout.addWidget(main_window.btn_game_settings)
    main_window.toolbar_layout.addWidget(main_window.btn_build_game)

    # Відступ, щоб притиснути Save і Play вправо
    main_window.toolbar_layout.addStretch()

    # Блок 4: Збереження та Гра
    main_window.btn_save = QPushButton("💾 Save")
    main_window.btn_play = QPushButton("▶ PLAY")
    main_window.btn_save.setStyleSheet("background-color: #007acc; color: white; border: none; font-weight: bold;")
    main_window.btn_play.setStyleSheet("background-color: #28a745; color: white; border: none; font-weight: bold;")
    
    main_window.toolbar_layout.addWidget(main_window.btn_save)
    main_window.toolbar_layout.addWidget(main_window.btn_play)
    
    main_window.main_layout.addWidget(main_window.toolbar)

    main_window.horizontal_splitter = QSplitter(Qt.Horizontal)

    main_window.sidebar_panel = QScrollArea()
    main_window.sidebar_panel.setWidgetResizable(True)
    main_window.sidebar_panel.setMinimumWidth(250)
    main_window.sidebar_widget = QWidget()
    main_window.sidebar_layout = QVBoxLayout(main_window.sidebar_widget)
    
    main_window.sidebar_layout.addWidget(QLabel("PROJECT"))
    main_window.tree_view = QTreeView()
    main_window.tree_view.setHeaderHidden(True)
    main_window.sidebar_layout.addWidget(main_window.tree_view)
    
    main_window.tree_model = QStandardItemModel()
    main_window.tree_view.setModel(main_window.tree_model)
    
    main_window.root_tiles = create_item("Tiles")
    main_window.root_entities = create_item("Entities")
    main_window.root_audio = create_item("Audio")
    main_window.tree_model.appendRow(main_window.root_tiles)
    main_window.tree_model.appendRow(main_window.root_entities)
    main_window.tree_model.appendRow(main_window.root_audio)
    
    for folder_name in sorted(assets.keys()):
        main_window.root_tiles.appendRow(create_item(folder_name))
        
    entities_path = os.path.join('data', 'images', 'entities')
    os.makedirs(entities_path, exist_ok=True)
    for ent in sorted(os.listdir(entities_path)):
        ent_full = os.path.join(entities_path, ent)
        if os.path.isdir(ent_full):
            ent_item = create_item(ent)
            main_window.root_entities.appendRow(ent_item)
            for anim in sorted(os.listdir(ent_full)):
                if os.path.isdir(os.path.join(ent_full, anim)):
                    ent_item.appendRow(create_item(anim))
                    
    sfx_path = os.path.join('data', 'sfx')
    os.makedirs(sfx_path, exist_ok=True)
    for sfx_file in sorted(os.listdir(sfx_path)):
        if sfx_file.lower().endswith(('.wav', '.mp3', '.ogg')):
            main_window.root_audio.appendRow(create_item(sfx_file))
            
    main_window.tree_view.expandAll()
    main_window.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
    
    main_window.btn_add_tiles = QPushButton("+ Add Images")
    main_window.btn_add_tiles.hide() 
    main_window.sidebar_layout.addWidget(main_window.btn_add_tiles)

    main_window.btn_add_audio = QPushButton("+ Add Audio")
    main_window.btn_add_audio.hide() 
    main_window.sidebar_layout.addWidget(main_window.btn_add_audio)

    main_window.btn_new_folder = QPushButton("+ Folder")
    main_window.btn_new_folder.setObjectName("NewFolderBtn") # Для QSS
    main_window.sidebar_layout.addWidget(main_window.btn_new_folder)
    main_window.sidebar_panel.setWidget(main_window.sidebar_widget)

    main_window.center_container = QFrame()
    main_window.center_layout = QVBoxLayout(main_window.center_container)
    main_window.center_layout.setContentsMargins(0, 0, 0, 0)
    main_window.vertical_splitter = QSplitter(Qt.Vertical)
    
    main_window.viewport = NumiViewport(assets)
    main_window.vertical_splitter.addWidget(main_window.viewport)
    
    main_window.browser_panel = QFrame()
    main_window.browser_panel.setMinimumHeight(200)
    main_window.browser_layout = QVBoxLayout(main_window.browser_panel)
    main_window.asset_list = QListWidget()
    main_window.asset_list.setViewMode(QListWidget.IconMode)
    main_window.asset_list.setIconSize(QSize(64, 64))
    main_window.asset_list.setContextMenuPolicy(Qt.CustomContextMenu)
    main_window.browser_layout.addWidget(main_window.asset_list)
    main_window.browser_scroll = QScrollArea()
    main_window.browser_scroll.setWidgetResizable(True)
    main_window.browser_scroll.setWidget(main_window.browser_panel)
    main_window.browser_scroll.setMinimumHeight(200)
    main_window.vertical_splitter.addWidget(main_window.browser_scroll)
    main_window.center_layout.addWidget(main_window.vertical_splitter)

    main_window.properties_panel = QScrollArea()
    main_window.properties_panel.setWidgetResizable(True)
    main_window.properties_panel.setMinimumWidth(300)
    main_window.properties_panel.setMaximumWidth(350)
    
    main_window.properties_widget = QWidget()
    main_window.properties_layout = QVBoxLayout(main_window.properties_widget)
    
    main_window.prop_title = QLabel("Properties")
    main_window.prop_title.setStyleSheet("""
        font-weight: bold; font-size: 15px; color: #ffffff; 
        background-color: #222222; padding: 6px 10px; 
        border-left: 4px solid #fbc02d; margin-bottom: 5px;
    """)
    main_window.properties_layout.addWidget(main_window.prop_title)
    
    main_window.prop_type_label = QLabel("Object Type:")
    main_window.prop_type_combo = QComboBox()
    main_window.prop_type_combo.addItems(["Static Blocks", "Kill Zone", "Spawner", "Background", "Level Exit", "UI Button"])
    main_window.properties_layout.addWidget(main_window.prop_type_label)
    main_window.properties_layout.addWidget(main_window.prop_type_combo)
    
    main_window.prop_block_container = QWidget()
    main_window.prop_block_layout = QVBoxLayout(main_window.prop_block_container)
    main_window.prop_block_layout.setContentsMargins(0, 0, 0, 0)
    main_window.prop_visible_cb = QCheckBox("Visible in Game") 
    main_window.prop_collision_cb = QCheckBox("Has Collision (Solid)")
    main_window.prop_block_layout.addWidget(main_window.prop_visible_cb)
    main_window.prop_block_layout.addWidget(main_window.prop_collision_cb)
    main_window.properties_layout.addWidget(main_window.prop_block_container)
    
    main_window.prop_bg_container = QWidget()
    main_window.prop_bg_layout = QVBoxLayout(main_window.prop_bg_container)
    main_window.prop_bg_layout.setContentsMargins(0, 0, 0, 0)
    main_window.prop_current_bg_label = QLabel("Active BG: None")
    main_window.prop_current_bg_label.setStyleSheet("color: #0366d6; font-weight: bold;")
    main_window.prop_current_music_label = QLabel("Active Music: None")
    main_window.prop_current_music_label.setStyleSheet("color: #28a745; font-weight: bold;")
    main_window.btn_clear_bg = QPushButton("Clear BG & Music")
    main_window.prop_bg_layout.addWidget(QLabel("1. Click a Tile to set Background"))
    main_window.prop_bg_layout.addWidget(main_window.prop_current_bg_label)
    main_window.prop_bg_layout.addWidget(QLabel("2. Click Audio to set Music"))
    main_window.prop_bg_layout.addWidget(main_window.prop_current_music_label)
    main_window.prop_bg_layout.addWidget(main_window.btn_clear_bg)
    main_window.properties_layout.addWidget(main_window.prop_bg_container)
    
    main_window.prop_spawner_container = QWidget()
    main_window.prop_spawner_layout = QVBoxLayout(main_window.prop_spawner_container)
    main_window.prop_spawner_layout.setContentsMargins(0, 0, 0, 0)
    
    main_window.prop_preset_label = QLabel("Entity Preset:")
    main_window.prop_preset_combo = QComboBox()
    main_window.prop_preset_combo.addItems(["Player", "Enemy", "Friendly NPC", "Collectible"])
    main_window.prop_spawner_layout.addWidget(main_window.prop_preset_label)
    main_window.prop_spawner_layout.addWidget(main_window.prop_preset_combo)

    main_window.char_divider = QFrame()
    main_window.char_divider.setFrameShape(QFrame.HLine)
    main_window.char_divider.setStyleSheet("background-color: #555; margin: 10px 0 5px 0;")
    main_window.prop_spawner_layout.addWidget(main_window.char_divider)

    main_window.char_title_label = QLabel("CHARACTER / ITEM SETTINGS")
    main_window.char_title_label.setStyleSheet("font-weight: bold; color: #fbc02d; font-size: 11px;")
    main_window.prop_spawner_layout.addWidget(main_window.char_title_label)

    main_window.prop_anim_idle_label = QLabel("Idle Anim:")
    main_window.prop_anim_idle_input = QLineEdit()
    main_window.prop_spawner_layout.addWidget(main_window.prop_anim_idle_label)
    main_window.prop_spawner_layout.addWidget(main_window.prop_anim_idle_input)

    main_window.prop_walk_cb = QCheckBox("Can Walk")
    main_window.prop_speed_label = QLabel("Speed:")
    main_window.prop_speed_input = QDoubleSpinBox()
    main_window.prop_speed_input.setRange(0.1, 10.0)
    main_window.prop_anim_walk_label = QLabel("Walk Anim:")
    main_window.prop_anim_walk_input = QLineEdit()
    main_window.prop_spawner_layout.addWidget(main_window.prop_walk_cb)
    main_window.prop_spawner_layout.addWidget(main_window.prop_speed_label)
    main_window.prop_spawner_layout.addWidget(main_window.prop_speed_input)
    main_window.prop_spawner_layout.addWidget(main_window.prop_anim_walk_label)
    main_window.prop_spawner_layout.addWidget(main_window.prop_anim_walk_input)

    main_window.prop_jump_cb = QCheckBox("Can Jump")
    main_window.prop_jump_label = QLabel("Jump Height:")
    main_window.prop_jump_input = QSpinBox()
    main_window.prop_jump_input.setRange(1, 15)
    main_window.prop_anim_jump_label = QLabel("Jump Anim:")
    main_window.prop_anim_jump_input = QLineEdit()
    main_window.prop_spawner_layout.addWidget(main_window.prop_jump_cb)
    main_window.prop_spawner_layout.addWidget(main_window.prop_jump_label)
    main_window.prop_spawner_layout.addWidget(main_window.prop_jump_input)
    main_window.prop_spawner_layout.addWidget(main_window.prop_anim_jump_label)
    main_window.prop_spawner_layout.addWidget(main_window.prop_anim_jump_input)

    main_window.prop_wall_jump_cb = QCheckBox("Can Wall Jump")
    main_window.prop_anim_wall_slide_label = QLabel("Wall Slide Anim:")
    main_window.prop_anim_wall_slide_input = QLineEdit()
    main_window.prop_spawner_layout.addWidget(main_window.prop_wall_jump_cb)
    main_window.prop_spawner_layout.addWidget(main_window.prop_anim_wall_slide_label)
    main_window.prop_spawner_layout.addWidget(main_window.prop_anim_wall_slide_input)

    main_window.prop_dash_cb = QCheckBox("Dash Attack")
    main_window.prop_anim_dash_label = QLabel("Dash Anim:")
    main_window.prop_anim_dash_input = QLineEdit()
    main_window.prop_spawner_layout.addWidget(main_window.prop_dash_cb)
    main_window.prop_spawner_layout.addWidget(main_window.prop_anim_dash_label)
    main_window.prop_spawner_layout.addWidget(main_window.prop_anim_dash_input)

    main_window.prop_shoot_cb = QCheckBox("Ranged Attack")
    main_window.prop_weapon_img_label = QLabel("Weapon Img:")
    main_window.prop_weapon_img_input = QLineEdit()
    main_window.prop_projectile_img_label = QLabel("Projectile Img:")
    main_window.prop_projectile_img_input = QLineEdit()
    main_window.prop_shoot_cd_label = QLabel("Shoot CD:")
    main_window.prop_shoot_cd_input = QSpinBox()
    main_window.prop_shoot_cd_input.setRange(10, 300)
    main_window.prop_vision_label = QLabel("Vision Range:")
    main_window.prop_vision_input = QSpinBox()
    main_window.prop_vision_input.setRange(1, 100)
    
    main_window.prop_dialogue_label = QLabel("Dialogue Text (розділяй через ';'):")
    main_window.prop_dialogue_input = QLineEdit("Привіт!;Як справи?")
    main_window.prop_dialogue_sound_label = QLabel("Talk Sound File:")
    main_window.prop_dialogue_sound_input = QLineEdit("talk.wav")

    main_window.prop_col_type_label = QLabel("Collectible Type:")
    main_window.prop_col_type_combo = QComboBox()
    main_window.prop_col_type_combo.addItems(["coin"])
    main_window.prop_col_value_label = QLabel("Coin Value:")
    main_window.prop_col_value_input = QSpinBox()
    main_window.prop_col_value_input.setRange(1, 999)
    main_window.prop_col_ui_icon_label = QLabel("HUD Icon Path (Optional):")
    main_window.prop_col_ui_icon_input = QLineEdit()
    main_window.prop_col_ui_icon_input.setPlaceholderText("Напр: entities/coin/hud.png")
    
    main_window.prop_spawner_layout.addWidget(main_window.prop_shoot_cb)
    main_window.prop_spawner_layout.addWidget(main_window.prop_weapon_img_label)
    main_window.prop_spawner_layout.addWidget(main_window.prop_weapon_img_input)
    main_window.prop_spawner_layout.addWidget(main_window.prop_projectile_img_label)
    main_window.prop_spawner_layout.addWidget(main_window.prop_projectile_img_input)
    main_window.prop_spawner_layout.addWidget(main_window.prop_shoot_cd_label)
    main_window.prop_spawner_layout.addWidget(main_window.prop_shoot_cd_input)
    main_window.prop_spawner_layout.addWidget(main_window.prop_vision_label)
    main_window.prop_spawner_layout.addWidget(main_window.prop_vision_input)
    
    main_window.prop_spawner_layout.addWidget(main_window.prop_dialogue_label)
    main_window.prop_spawner_layout.addWidget(main_window.prop_dialogue_input)
    main_window.prop_spawner_layout.addWidget(main_window.prop_dialogue_sound_label)
    main_window.prop_spawner_layout.addWidget(main_window.prop_dialogue_sound_input)
    
    main_window.prop_spawner_layout.addWidget(main_window.prop_col_type_label)
    main_window.prop_spawner_layout.addWidget(main_window.prop_col_type_combo)
    main_window.prop_spawner_layout.addWidget(main_window.prop_col_value_label)
    main_window.prop_spawner_layout.addWidget(main_window.prop_col_value_input)
    main_window.prop_spawner_layout.addWidget(main_window.prop_col_ui_icon_label)
    main_window.prop_spawner_layout.addWidget(main_window.prop_col_ui_icon_input)
    
    main_window.properties_layout.addWidget(main_window.prop_spawner_container)

    main_window.prop_ui_btn_container = QWidget()
    main_window.prop_ui_btn_layout = QVBoxLayout(main_window.prop_ui_btn_container)
    main_window.prop_ui_btn_layout.setContentsMargins(0, 0, 0, 0)

    main_window.prop_ui_text_label = QLabel("Button Text:")
    main_window.prop_ui_text_input = QLineEdit()
    main_window.prop_ui_action_label = QLabel("On Click Action:")
    main_window.prop_ui_action_combo = QComboBox()
    main_window.prop_ui_action_combo.addItems(["none", "load_map", "open_url", "quit_game", "resume_game", "toggle_music", "toggle_sfx", "toggle_hud", "cycle_resolution", "toggle_fullscreen"])
    main_window.prop_ui_target_label = QLabel("Target (Map/URL):")
    main_window.prop_ui_target_input = QComboBox()
    main_window.prop_ui_target_input.setEditable(True)

    main_window.prop_ui_btn_layout.addWidget(main_window.prop_ui_text_label)
    main_window.prop_ui_btn_layout.addWidget(main_window.prop_ui_text_input)
    main_window.prop_ui_btn_layout.addWidget(main_window.prop_ui_action_label)
    main_window.prop_ui_btn_layout.addWidget(main_window.prop_ui_action_combo)
    main_window.prop_ui_btn_layout.addWidget(main_window.prop_ui_target_label)
    main_window.prop_ui_btn_layout.addWidget(main_window.prop_ui_target_input)
    main_window.properties_layout.addWidget(main_window.prop_ui_btn_container)
    
    main_window.sfx_divider = QFrame()
    main_window.sfx_divider.setFrameShape(QFrame.HLine)
    main_window.sfx_divider.setFrameShadow(QFrame.Sunken)
    main_window.sfx_divider.setStyleSheet("background-color: #555; margin: 15px 0 5px 0;")
    main_window.properties_layout.addWidget(main_window.sfx_divider)

    main_window.sfx_title_label = QLabel("SFX SETTINGS & VOLUMES")
    main_window.sfx_title_label.setStyleSheet("font-weight: bold; color: #fbc02d; font-size: 11px;")
    main_window.properties_layout.addWidget(main_window.sfx_title_label)

    main_window.sfx_container = QWidget()
    main_window.sfx_layout = QVBoxLayout(main_window.sfx_container)
    main_window.sfx_layout.setContentsMargins(0, 0, 0, 0)
    
    def create_sfx_row(label_text, key):
        block = QWidget()
        layout = QVBoxLayout(block)
        layout.setContentsMargins(0, 5, 0, 5)
        
        layout.addWidget(QLabel(f"{label_text} Sound File:"))
        input_field = QLineEdit()
        setattr(main_window, f"prop_sfx_{key}_input", input_field)
        layout.addWidget(input_field)
        
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("Vol:"))
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(60)
        setattr(main_window, f"prop_sfx_{key}_slider", slider)
        
        val_label = QLabel("60%")
        setattr(main_window, f"prop_sfx_{key}_label", val_label)
        slider.valueChanged.connect(lambda v: val_label.setText(f"{v}%"))
        
        vol_layout.addWidget(slider)
        vol_layout.addWidget(val_label)
        layout.addLayout(vol_layout)
        
        setattr(main_window, f"row_sfx_{key}", block)
        main_window.sfx_layout.addWidget(block)

    create_sfx_row("Hit", "hit")
    create_sfx_row("Jump", "jump")
    create_sfx_row("Dash", "dash")
    create_sfx_row("Shoot", "shoot")

    main_window.properties_layout.addWidget(main_window.sfx_container)

    main_window.btn_reset_props = QPushButton("Reset Properties")
    main_window.btn_reset_props.setStyleSheet("background-color: #d73a49; color: white; font-weight: bold; margin-top: 15px;")
    main_window.properties_layout.addWidget(main_window.btn_reset_props)
    main_window.properties_layout.addStretch()
    
    main_window.properties_panel.setWidget(main_window.properties_widget)
    main_window.properties_panel.hide()

    main_window.horizontal_splitter.addWidget(main_window.sidebar_panel)
    main_window.horizontal_splitter.addWidget(main_window.center_container)
    main_window.horizontal_splitter.addWidget(main_window.properties_panel)
    main_window.horizontal_splitter.setStretchFactor(1, 1)
    
    main_window.main_vertical_splitter = QSplitter(Qt.Vertical)
    main_window.main_vertical_splitter.addWidget(main_window.horizontal_splitter)
    
    main_window.console_container = QWidget()
    main_window.console_layout = QVBoxLayout(main_window.console_container)
    main_window.console_layout.setContentsMargins(0, 0, 0, 0)
    
    main_window.console_header = QLabel(" 💻 Console Output (Логи та Помилки)")
    main_window.console_header.setStyleSheet("background-color: #1e1e1e; color: #fbc02d; font-weight: bold; padding: 4px; border-top: 2px solid #333;")
    main_window.console_layout.addWidget(main_window.console_header)
    
    main_window.console_output = QTextEdit()
    main_window.console_output.setReadOnly(True)
    main_window.console_output.setStyleSheet("background-color: #0d0d0d; color: #cccccc; font-family: Consolas, monospace; font-size: 13px; border: none; padding: 5px;")
    main_window.console_layout.addWidget(main_window.console_output)
    
    main_window.main_vertical_splitter.addWidget(main_window.console_container)
    main_window.main_vertical_splitter.setSizes([600, 100]) 
    
    main_window.main_layout.addWidget(main_window.main_vertical_splitter)

    try:
        with open("ui/styles.qss", "r", encoding="utf-8") as f:
            main_window.setStyleSheet(f.read())
    except FileNotFoundError: pass