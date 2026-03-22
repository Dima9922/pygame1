import sys
import pygame
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTreeView, QFrame, 
                             QSplitter, QPushButton, QLabel,
                             QListWidget, QListWidgetItem, QApplication)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap, QImage
from ui.pygame_widget import NumiViewport 

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

        # --- SPLITTERS ---
        self.horizontal_splitter = QSplitter(Qt.Horizontal)

        # Sidebar
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
        
        self.btn_new_folder = QPushButton("+ New Folder")
        self.btn_new_folder.setObjectName("NewFolderBtn")
        self.sidebar_layout.addWidget(self.btn_new_folder)

        # Right Side (Viewport + Browser)
        self.right_container = QFrame()
        self.right_layout = QVBoxLayout(self.right_container)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.vertical_splitter = QSplitter(Qt.Vertical)
        
        self.viewport = NumiViewport(self.assets)
        self.vertical_splitter.addWidget(self.viewport)
        
        # Browser Panel
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
        self.asset_list.clicked.connect(self.on_tile_clicked)
        
        self.browser_layout.addWidget(self.asset_list)
        self.vertical_splitter.addWidget(self.browser_panel)
        
        self.vertical_splitter.setStretchFactor(0, 7)
        self.vertical_splitter.setStretchFactor(1, 3)
        self.right_layout.addWidget(self.vertical_splitter)

        self.horizontal_splitter.addWidget(self.sidebar)
        self.horizontal_splitter.addWidget(self.right_container)
        self.horizontal_splitter.setSizes([250, 1030])
        self.horizontal_splitter.setStretchFactor(1, 1)
        
        self.main_layout.addWidget(self.horizontal_splitter)

    def on_folder_clicked(self, index):
        folder_name = self.tree_model.itemFromIndex(index).text()
        self.asset_list.clear()
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
        """Зберігає мапу у файл"""
        self.viewport.editor.tilemap.save('map.json')
        print("Мапу успішно збережено в map.json!")
        # Тут можна додати спливаюче вікно про успішне збереження пізніше

    def on_play_clicked(self):
        if self.btn_play.text() == "▶ PLAY":
            self.btn_play.setText("■ STOP")
            self.btn_play.setStyleSheet("background-color: #d73a49; color: white; font-weight: bold;")
            
            self.sidebar.hide()
            self.browser_panel.hide()
            
            # ДОДАЙ ЦЕЙ РЯДОК: Змушує Qt миттєво розтягнути вікно перед створенням гри
            QApplication.processEvents() 
            
            self.viewport.set_mode("PLAY")
            self.viewport.setFocus()
            
        else:
            self.btn_play.setText("▶ PLAY")
            self.btn_play.setStyleSheet("")
            
            self.sidebar.show()
            self.browser_panel.show()
            
            self.viewport.set_mode("EDITOR")
    
    def load_stylesheet(self):
        try:
            with open("ui/styles.qss", "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError: pass