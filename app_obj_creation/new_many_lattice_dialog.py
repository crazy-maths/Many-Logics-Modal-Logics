"""
New Many-Lattice Dialog Module.

This module provides a dialog window for creating ManyLattice objects.
It allows users to:
1. Select a Base Filtered Lattice.
2. Choose an Interpretation Mode (Up/Down).
3. Either Auto-Generate valid sublattices from the base elements OR select existing lattices.
"""

import itertools
from typing import Dict, List, Set, Tuple, Optional, Any
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QRadioButton,
    QButtonGroup,
    QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QBrush


class NewManyLatticeDialog(QDialog):
    """
    A dialog for creating a new ManyLattice by defining its base structure and sublattices.
    """

    def __init__(
        self, 
        filtered_lattice_dict: Dict[str, Any], 
        lattice_dict: Dict[str, Any], 
        parent: Optional[QWidget] = None
    ):
        """
        Initializes the dialog.

        Args:
            filtered_lattice_dict (Dict[str, Any]): Available Filtered Lattices.
            lattice_dict (Dict[str, Any]): Available Base Lattices (for calculations).
            parent (Optional[QWidget]): Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Create New Many Lattice")
        self.resize(600, 650)
        
        self.filtered_lattice_dict = filtered_lattice_dict
        self.lattice_dict = lattice_dict
        
        main_layout = QVBoxLayout(self)
        
        # --- TOP SECTION: Common Info ---
        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter unique name for the Many Lattice")
        
        self.combo_filtered_lat = QComboBox()
        self.combo_filtered_lat.addItems(list(filtered_lattice_dict.keys()))
        self.combo_filtered_lat.setPlaceholderText("Select a base lattice...")
        self.combo_filtered_lat.currentTextChanged.connect(self.on_base_changed)
        
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Base Filtered Lattice:", self.combo_filtered_lat)
        main_layout.addLayout(form_layout)

        # --- Interpretation Mode Selection ---
        interp_layout = QHBoxLayout()
        interp_layout.addWidget(QLabel("<b>Interpretation Mode:</b>"))
        
        self.radio_down = QRadioButton("Down Interpretation")
        self.radio_up = QRadioButton("Up Interpretation")
        self.radio_down.setChecked(True)  # Default
        
        self.btn_group = QButtonGroup()
        self.btn_group.addButton(self.radio_down)
        self.btn_group.addButton(self.radio_up)
        
        interp_layout.addWidget(self.radio_down)
        interp_layout.addWidget(self.radio_up)
        interp_layout.addStretch()
        
        main_layout.addLayout(interp_layout)

        # --- MIDDLE SECTION: Tabs ---
        self.tabs = QTabWidget()
        
        # Tab 1: Generator
        self.tab_gen = QWidget()
        self.gen_layout = QVBoxLayout(self.tab_gen)
        self.gen_label = QLabel("<b>Auto-Generate from Elements:</b>")
        self.list_generated = QListWidget()
        self.list_generated.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.gen_layout.addWidget(self.gen_label)
        self.gen_layout.addWidget(self.list_generated)
        
        # Tab 2: Existing Lattices
        self.tab_existing = QWidget()
        self.exist_layout = QVBoxLayout(self.tab_existing)
        self.exist_label = QLabel("<b>Select Already Loaded Lattices:</b>")
        self.list_existing = QListWidget()
        self.list_existing.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.exist_layout.addWidget(self.exist_label)
        self.exist_layout.addWidget(self.list_existing)

        self.tabs.addTab(self.tab_gen, "Generate New")
        self.tabs.addTab(self.tab_existing, "Load Existing")
        
        main_layout.addWidget(self.tabs)
        
        # --- BOTTOM SECTION: Buttons ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        # Populate lists
        self.populate_existing_lattices()
        if filtered_lattice_dict:
            self.on_base_changed(self.combo_filtered_lat.itemText(0))

    def populate_existing_lattices(self) -> None:
        """Populates the 'Load Existing' tab with all lattices currently in memory."""
        self.list_existing.clear()
        for name in sorted(self.lattice_dict.keys()):
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.list_existing.addItem(item)

    def on_base_changed(self, fl_name: str) -> None:
        """
        Updates the Generator list when the base filtered lattice changes.
        Calculates all valid sublattices and displays them grouped by size.

        Args:
            fl_name (str): The name of the selected filtered lattice.
        """
        self.list_generated.clear()

        if not fl_name or fl_name not in self.filtered_lattice_dict:
            return

        # Logic to find base lattice object
        fl_obj = self.filtered_lattice_dict[fl_name]
        # Attempt to get base name from attribute
        base_name = getattr(fl_obj, 'name_lattice', getattr(fl_obj, 'name', None))

        if not base_name or base_name not in self.lattice_dict:
            self.add_header_item(self.list_generated, f"Error: Base lattice '{base_name}' not found.")
            return

        current_lattice = self.lattice_dict[base_name]
        elements = list(current_lattice.elements)
        
        # Safety check for performance
        if len(elements) > 10:
            self.add_header_item(self.list_generated, f"Lattice too large ({len(elements)}) to auto-generate.")
            return

        self.add_header_item(self.list_generated, f"Calculating sublattices for base '{base_name}'...", "#fff3cd")
        self.repaint() 

        # Generate Power Set
        valid_sublattices = []
        for r in range(1, len(elements) + 1):
            for subset in itertools.combinations(elements, r):
                subset_set = set(subset)
                if self.is_valid_sublattice(subset_set, current_lattice):
                    valid_sublattices.append(subset_set)

        self.list_generated.clear()
        
        # Sort by size to enable grouping
        valid_sublattices.sort(key=len)

        # Display with Group Headers
        current_size = -1
        for sub in valid_sublattices:
            size = len(sub)
            
            # Insert Header if size changes
            if size != current_size:
                current_size = size
                self.add_header_item(self.list_generated, f"Sublattices with {size} elements:")
            
            text_display = "{" + ", ".join(sorted(list(sub))) + "}"
            self.add_checkable_item(self.list_generated, text_display)

    def is_valid_sublattice(self, subset: Set[str], lattice: Any) -> bool:
        """
        Checks if a subset of elements is closed under Join and Meet operations.

        Args:
            subset (Set[str]): The set of elements to check.
            lattice (Lattice): The parent lattice object containing the operations.

        Returns:
            bool: True if closed (valid sublattice), False otherwise.
        """
        if len(subset) == 1:
            return True
        
        for a in subset:
            for b in subset:
                try:
                    if lattice.join(a, b) not in subset: return False
                    if lattice.meet(a, b) not in subset: return False
                except ValueError:
                    return False
        return True

    def add_header_item(self, list_widget: QListWidget, text: str, color: str = "#e0e0e0") -> None:
        """
        Adds a visual header/separator item to the list.

        Args:
            list_widget (QListWidget): Target list.
            text (str): Header text.
            color (str): Background color hex code.
        """
        item = QListWidgetItem(text)
        font = QFont()
        font.setBold(True)
        item.setFont(font)
        item.setBackground(QBrush(QColor(color)))
        item.setFlags(Qt.ItemFlag.NoItemFlags) 
        list_widget.addItem(item)

    def add_checkable_item(self, list_widget: QListWidget, text: str) -> None:
        """
        Adds a selectable item with a checkbox to the list.

        Args:
            list_widget (QListWidget): Target list.
            text (str): Item text.
        """
        item = QListWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Unchecked)
        list_widget.addItem(item)

    def get_data(self) -> Tuple[str, str, List[Set[str]], List[str], str]:
        """
        Retrieves all user input from the dialog.

        Returns:
            Tuple containing:
            1. name (str): The name of the new Many Lattice.
            2. base_fl_name (str): The name of the chosen base Filtered Lattice.
            3. generated_subsets (List[Set[str]]): List of raw element sets from Tab 1.
            4. selected_existing_names (List[str]): List of existing lattice names from Tab 2.
            5. interpretation_mode (str): "down" or "up".
        """
        name = self.name_input.text().strip()
        base_fl_name = self.combo_filtered_lat.currentText()
        
        interpretation_mode = "down" if self.radio_down.isChecked() else "up"

        # 1. Get Generated Subsets
        generated_subsets = []
        for i in range(self.list_generated.count()):
            item = self.list_generated.item(i)
            # Only process checkable items (skip headers)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable and item.checkState() == Qt.CheckState.Checked:
                clean = item.text().replace('{', '').replace('}', '')
                elems = {e.strip() for e in clean.split(',') if e.strip()}
                generated_subsets.append(elems)

        # 2. Get Existing Lattice Names
        selected_existing_names = []
        for i in range(self.list_existing.count()):
            item = self.list_existing.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_existing_names.append(item.text())

        return name, base_fl_name, generated_subsets, selected_existing_names, interpretation_mode