"""
File Browser Widget for CSV Data Visualizer.

This module contains the FileBrowserWidget class for browsing CSV files.
"""

import os
import logging
from typing import Dict, List, Any, Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTreeView, QHeaderView, 
                          QLabel, QLineEdit, QPushButton, QAbstractItemView, 
                          QHBoxLayout, QComboBox, QSizePolicy, QMenu,
                          QCheckBox)
from PyQt6.QtCore import (Qt, QModelIndex, QDir, QSortFilterProxyModel, 
                       pyqtSignal, pyqtSlot)
from PyQt6.QtGui import (QIcon, QAction, QKeySequence, QStandardItem, 
                      QStandardItemModel, QBrush, QColor, QFont)

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
        self._group_info_map = {}
    
    def add_files(self, files: List[Dict[str, Any]]):
        """
        Add files to the model.
        
        Args:
            files: List of file information dictionaries
        """
        # Clear model
        self.clear()
        self.setHorizontalHeaderLabels(["Name"])
        
        # Clear file info maps
        self._file_info_map = {}
        self._group_info_map = {}
        
        # Create week folders
        week_folders = {}
        file_groups = {}
        
        # First pass: identify metrics and groups
        for file_info in files:
            # Check if this is a group
            is_group = file_info.get('is_group', False)
            
            if is_group:
                metric = file_info.get('metric', 'Unknown')
                self._group_info_map[metric] = file_info
                file_groups[metric] = file_info
        
        # Second pass: add files and groups to the model
        for file_info in files:
            # Get path components
            path = file_info.get('path', '')
            file_name = file_info.get('name', '')
            
            # Create display name
            display_name = file_info.get('display_name', file_name)
            
            # Check if this is a file group
            is_group = file_info.get('is_group', False)
            
            if is_group:
                # Add file group
                metric = file_info.get('metric', 'Unknown')
                file_count = file_info.get('file_count', 0)
                
                # Create group item with custom styling
                group_item = QStandardItem(f"{display_name} ({file_count} files)")
                group_item.setData(metric, Qt.ItemDataRole.UserRole)
                group_item.setData("group", Qt.ItemDataRole.UserRole + 1)
                
                # Set bold font
                font = QFont()
                font.setBold(True)
                group_item.setFont(font)
                
                # Set blue color
                group_item.setForeground(QBrush(QColor("#0078d4")))
                
                self.appendRow(group_item)
                
                # Add child files to group
                child_files = file_info.get('files', [])
                for child_file in child_files:
                    child_path = child_file.get('path', '')
                    child_name = child_file.get('display_name', child_file.get('name', ''))
                    
                    # Create child item
                    child_item = QStandardItem(child_name)
                    child_item.setData(child_path, Qt.ItemDataRole.UserRole)
                    child_item.setData("file", Qt.ItemDataRole.UserRole + 1)
                    
                    # Store file info in map
                    self._file_info_map[child_path] = child_file
                    
                    # Add to group
                    group_item.appendRow(child_item)
            
            elif path:  # Regular file
                # Check if this file is part of a group
                is_in_group = False
                if 'metric' in file_info:
                    metric = file_info['metric']
                    if metric in file_groups:
                        # Skip this file as it will be shown under its group
                        is_in_group = True
                
                if not is_in_group:
                    # Check if file is in a week folder
                    week_number = file_info.get('week_number')
                    
                    if week_number is not None:
                        # Create week folder if not exists
                        if week_number not in week_folders:
                            folder_item = QStandardItem(f"Week {week_number}")
                            folder_item.setData("folder", Qt.ItemDataRole.UserRole + 1)
                            self.appendRow(folder_item)
                            week_folders[week_number] = folder_item
                        
                        # Add file to week folder
                        folder_item = week_folders[week_number]
                        
                        file_item = QStandardItem(display_name)
                        file_item.setData(path, Qt.ItemDataRole.UserRole)
                        file_item.setData("file", Qt.ItemDataRole.UserRole + 1)
                        folder_item.appendRow(file_item)
                        
                    else:
                        # Add file directly to root
                        file_item = QStandardItem(display_name)
                        file_item.setData(path, Qt.ItemDataRole.UserRole)
                        file_item.setData("file", Qt.ItemDataRole.UserRole + 1)
                        self.appendRow(file_item)
                
                # Store file info in map
                if path:
                    self._file_info_map[path] = file_info
    
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
        
        # Get path and item type from model data
        item = self.itemFromIndex(index)
        path = item.data(Qt.ItemDataRole.UserRole)
        item_type = item.data(Qt.ItemDataRole.UserRole + 1)
        
        # Check if it's a folder or group
        if item_type == "folder":
            return None
        elif item_type == "group":
            # Return group info
            return self._group_info_map.get(path)
        elif item_type == "file":
            # Return file info
            return self._file_info_map.get(path)
        
        return None


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
        
        # Get item type
        item_type = item.data(Qt.ItemDataRole.UserRole + 1)
        
        # Always show folders and groups
        if item_type == "folder" or item_type == "group":
            # Check if any child matches
            child_count = item.rowCount()
            for i in range(child_count):
                child_index = source_model.index(i, 0, index)
                if self.filterAcceptsRow(i, index):
                    return True
            
            # If no filter, show empty folders/groups too
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
        
        # Create options widget
        self.options_widget = QWidget()
        self.options_layout = QHBoxLayout(self.options_widget)
        self.options_layout.setContentsMargins(6, 0, 6, 6)
        
        # Add aggregation toggle checkbox
        self.aggregate_checkbox = QCheckBox("Group Related Files")
        self.aggregate_checkbox.setChecked(self.app_controller.settings.enable_file_aggregation)
        self.aggregate_checkbox.toggled.connect(self._toggle_aggregation)
        
        self.options_layout.addWidget(self.aggregate_checkbox)
        self.options_layout.addStretch()
        
        # Add refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_directory)
        self.options_layout.addWidget(self.refresh_button)
        
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
        self.layout.addWidget(self.options_widget)
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
    
    def _toggle_aggregation(self, enabled: bool):
        """
        Toggle file aggregation feature.
        
        Args:
            enabled: Whether aggregation is enabled
        """
        self.logger.info(f"File aggregation toggled: {enabled}")
        
        # Update settings
        self.app_controller.settings.enable_file_aggregation = enabled
        self.app_controller.settings.save_settings()
        
        # Refresh directory
        self.refresh_directory()
    
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
            self.logger.info(f"{'Group' if file_info.get('is_group', False) else 'File'} selected: {file_info.get('name', 'Unknown')}")
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
            is_group = file_info.get('is_group', False)
            self.logger.info(f"{'Group' if is_group else 'File'} double-clicked: {file_info.get('name', 'Unknown')}")
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
                
                # Add additional actions for file groups
                if file_info.get('is_group', False):
                    # Add action to expand/collapse group
                    if self.tree_view.isExpanded(index):
                        collapse_action = QAction("Collapse Group", self)
                        collapse_action.triggered.connect(lambda: self.tree_view.collapse(index))
                        menu.addAction(collapse_action)
                    else:
                        expand_action = QAction("Expand Group", self)
                        expand_action.triggered.connect(lambda: self.tree_view.expand(index))
                        menu.addAction(expand_action)
                
                # Show menu
                menu.exec(self.tree_view.viewport().mapToGlobal(position))
    
    def _open_file(self, file_info: Dict[str, Any]):
        """
        Open a file.
        
        Args:
            file_info: File information dictionary
        """
        is_group = file_info.get('is_group', False)
        self.logger.info(f"Opening {'group' if is_group else 'file'}: {file_info.get('name', 'Unknown')}")
        self.selected_file_info = file_info
        
        # Emit signal
        self.file_selected.emit(file_info)
