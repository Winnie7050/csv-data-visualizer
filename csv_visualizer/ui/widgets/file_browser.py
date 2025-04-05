"""
File Browser Widget for CSV Data Visualizer.

This module contains the FileBrowserWidget class for browsing CSV files.
"""

import os
import logging
from typing import Dict, List, Any, Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTreeView, QHeaderView, 
                          QLabel, QLineEdit, QPushButton, QAbstractItemView, 
                          QHBoxLayout, QComboBox, QSizePolicy, QMenu)
from PyQt6.QtCore import (Qt, QModelIndex, QDir, QSortFilterProxyModel, 
                       pyqtSignal, pyqtSlot, QFileSystemModel)
from PyQt6.QtGui import (QIcon, QAction, QKeySequence, QStandardItem, 
                      QStandardItemModel)

from csv_visualizer.utils.logging_utils import get_module_logger
from csv_visualizer.data.file_scanner import FileScanner


class FileTreeModel(QStandardItemModel):
    """Model for displaying CSV files in a tree view."""
    
    def __init__(self, parent=None):
        """Initialize the file tree model."""
        super().__init__(parent)
        self.setHorizontalHeaderLabels(["Name"])
        
        # Dictionary to store file info by path
        self._file_info_map = {}
    
    def add_files(self, files: List[Dict[str, Any]]):
        """
        Add files to the model.
        
        Args:
            files: List of file information dictionaries
        """
        # Clear model
        self.clear()
        self.setHorizontalHeaderLabels(["Name"])
        
        # Clear file info map
        self._file_info_map = {}
        
        # Create week folders
        week_folders = {}
        
        for file_info in files:
            # Get path components
            path = file_info['path']
            dir_path = os.path.dirname(path)
            file_name = file_info['name']
            
            # Create display name
            display_name = file_info.get('display_name', file_name)
            
            # Store file info in map
            self._file_info_map[path] = file_info
            
            # Check if file is in a week folder
            week_number = file_info.get('week_number')
            
            if week_number is not None:
                # Create week folder if not exists
                if week_number not in week_folders:
                    folder_item = QStandardItem(f"Week {week_number}")
                    folder_item.setData("folder", Qt.ItemDataRole.UserRole)
                    self.appendRow(folder_item)
                    week_folders[week_number] = folder_item
                
                # Add file to week folder
                folder_item = week_folders[week_number]
                
                file_item = QStandardItem(display_name)
                file_item.setData(path, Qt.ItemDataRole.UserRole)
                folder_item.appendRow(file_item)
                
            else:
                # Add file directly to root
                file_item = QStandardItem(display_name)
                file_item.setData(path, Qt.ItemDataRole.UserRole)
                self.appendRow(file_item)
    
    def get_file_info(self, index: QModelIndex) -> Optional[Dict[str, Any]]:
        """
        Get file information for an index.
        
        Args:
            index: Model index
            
        Returns:
            File information dictionary or None if not found
        """
        if not index.isValid():
            return None
        
        # Get path from model data
        item = self.itemFromIndex(index)
        path = item.data(Qt.ItemDataRole.UserRole)
        
        # Check if it's a folder
        if path == "folder":
            return None
        
        # Return file info from map
        return self._file_info_map.get(path)


class FileTreeFilterProxyModel(QSortFilterProxyModel):
    """Proxy model for filtering and sorting the file tree."""
    
    def __init__(self, parent=None):
        """Initialize the file tree filter proxy model."""
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setRecursiveFilteringEnabled(True)
    
    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """
        Filter rows based on filter text.
        
        Args:
            source_row: Row in source model
            source_parent: Parent index in source model
            
        Returns:
            True if row should be included, False otherwise
        """
        # Get source model
        source_model = self.sourceModel()
        
        # Get item
        index = source_model.index(source_row, 0, source_parent)
        item = source_model.itemFromIndex(index)
        
        # Always show folders
        if item.data(Qt.ItemDataRole.UserRole) == "folder":
            # Check if any child matches
            child_count = item.rowCount()
            for i in range(child_count):
                child_index = source_model.index(i, 0, index)
                if self.filterAcceptsRow(i, index):
                    return True
            
            # If no filter, show empty folders too
            return not self.filterRegularExpression().pattern()
        
        # Check if item text matches filter
        return super().filterAcceptsRow(source_row, source_parent)


class FileBrowserWidget(QWidget):
    """File Browser Widget for browsing CSV files."""
    
    # Signal emitted when a file is selected
    file_selected = pyqtSignal(dict)
    
    def __init__(self, app_controller):
        """
        Initialize the file browser widget.
        
        Args:
            app_controller: Application controller
        """
        super().__init__()
        
        self.app_controller = app_controller
        self.logger = get_module_logger("FileBrowserWidget")
        
        # File scanner
        self.file_scanner = FileScanner(self.logger, self.app_controller.settings)
        
        # Selected file info
        self.selected_file_info = None
        
        # Initialize UI
        self._init_ui()
        
        # Load initial directory
        self.refresh_directory()
        
        self.logger.info("File browser widget initialized")
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(6)
        
        # Create filter widget
        self.filter_widget = QWidget()
        self.filter_layout = QHBoxLayout(self.filter_widget)
        self.filter_layout.setContentsMargins(6, 6, 6, 0)
        
        self.filter_label = QLabel("Filter:")
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Search files...")
        self.filter_edit.textChanged.connect(self._filter_changed)
        
        self.filter_layout.addWidget(self.filter_label)
        self.filter_layout.addWidget(self.filter_edit)
        
        # Create tree model
        self.file_model = FileTreeModel(self)
        
        # Create proxy model for filtering
        self.proxy_model = FileTreeFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.file_model)
        
        # Create tree view
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.proxy_model)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setExpandsOnDoubleClick(True)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        
        # Connect signals
        self.tree_view.clicked.connect(self._item_clicked)
        self.tree_view.doubleClicked.connect(self._item_double_clicked)
        
        # Set context menu
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self._show_context_menu)
        
        # Add widgets to layout
        self.layout.addWidget(self.filter_widget)
        self.layout.addWidget(self.tree_view)
        
        # Set minimum width
        self.setMinimumWidth(200)
    
    def refresh_directory(self):
        """Refresh the file browser with the current directory."""
        self.logger.info("Refreshing directory browser")
        
        try:
            # Get directory from settings
            directory = self.app_controller.settings.data_directory
            
            # Scan directory for CSV files
            files = self.app_controller.data_manager.scan_directory(directory)
            
            # Update model
            self.file_model.add_files(files)
            
            # Expand all items
            self.tree_view.expandAll()
            
            # Resize column to content
            self.tree_view.resizeColumnToContents(0)
            
            self.logger.info(f"Directory refreshed: {len(files)} files found")
            
        except Exception as e:
            self.logger.error(f"Error refreshing directory: {str(e)}", exc_info=True)
    
    def get_selected_file_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the currently selected file.
        
        Returns:
            File information dictionary or None if no file is selected
        """
        return self.selected_file_info
    
    def _filter_changed(self, text: str):
        """
        Handle filter text change.
        
        Args:
            text: Filter text
        """
        self.proxy_model.setFilterFixedString(text)
        
        # If filter is not empty, expand all items
        if text:
            self.tree_view.expandAll()
    
    def _item_clicked(self, index: QModelIndex):
        """
        Handle item click.
        
        Args:
            index: Clicked item index
        """
        # Get source index
        source_index = self.proxy_model.mapToSource(index)
        
        # Get file info
        file_info = self.file_model.get_file_info(source_index)
        
        if file_info:
            self.logger.info(f"File selected: {file_info['name']}")
            self.selected_file_info = file_info
    
    def _item_double_clicked(self, index: QModelIndex):
        """
        Handle item double click.
        
        Args:
            index: Double-clicked item index
        """
        # Get source index
        source_index = self.proxy_model.mapToSource(index)
        
        # Get file info
        file_info = self.file_model.get_file_info(source_index)
        
        if file_info:
            self.logger.info(f"File double-clicked: {file_info['name']}")
            self.selected_file_info = file_info
            
            # Emit signal
            self.file_selected.emit(file_info)
    
    def _show_context_menu(self, position):
        """
        Show context menu for tree view.
        
        Args:
            position: Menu position
        """
        # Get index at position
        index = self.tree_view.indexAt(position)
        
        if index.isValid():
            # Get source index
            source_index = self.proxy_model.mapToSource(index)
            
            # Get file info
            file_info = self.file_model.get_file_info(source_index)
            
            if file_info:
                # Create menu
                menu = QMenu(self)
                
                # Add actions
                open_action = QAction("Open", self)
                open_action.triggered.connect(lambda: self._open_file(file_info))
                menu.addAction(open_action)
                
                # Show menu
                menu.exec(self.tree_view.viewport().mapToGlobal(position))
    
    def _open_file(self, file_info: Dict[str, Any]):
        """
        Open a file.
        
        Args:
            file_info: File information dictionary
        """
        self.logger.info(f"Opening file: {file_info['name']}")
        self.selected_file_info = file_info
        
        # Emit signal
        self.file_selected.emit(file_info)
