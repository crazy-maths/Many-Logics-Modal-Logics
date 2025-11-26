"""
New Filtered Lattice Dialog Module.

This module provides a dialog window for creating new Filtered Lattice objects.
It allows the user to select a base lattice from the existing project and
interactively choose which elements belong to the filter (designated true values).
"""

from typing import Dict, Optional, Tuple, Set, Any
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QWidget
)
from PyQt6.QtCore import Qt

class NewFilteredLatticeDialog(QDialog):
    """
    A dialog for creating a new Filtered Lattice.

    Attributes:
        lattice_dict (Dict[str, Any]): A dictionary mapping lattice names to Lattice objects.
    """

    def __init__(self, lattice_dict: Dict[str, Any], parent: Optional[QWidget] = None):
        """
        Initializes the dialog.

        Args:
            lattice_dict (Dict[str, Any]): Dictionary { "lattice_name": LatticeObject }.
                                           Required to fetch elements for the checklist.
            parent (Optional[QWidget]): The parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Create New Filtered Lattice")
        self.resize(400, 500)
        
        self.lattice_dict = lattice_dict
        
        layout = QFormLayout(self)
        
        # 1. Name Input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter unique name")
        
        # 2. Base Lattice Selection
        self.combo_lattice = QComboBox()
        # Sort keys for consistent UI
        self.combo_lattice.addItems(sorted(list(lattice_dict.keys())))
        self.combo_lattice.setPlaceholderText("Select a base lattice...")
        
        # Connect signal: When user changes lattice, update the filter list
        self.combo_lattice.currentTextChanged.connect(self.update_filter_options)
        
        # 3. Filter Selection (Checklist)
        self.list_elements = QListWidget()
        self.list_elements.setSelectionMode(QListWidget.SelectionMode.NoSelection)  # Use checkboxes
        self.list_elements.setToolTip("Check elements to include in the filter")
        
        layout.addRow("Name:", self.name_input)
        layout.addRow("Base Lattice:", self.combo_lattice)
        layout.addRow(QLabel("<b>Select Elements for Filter:</b>"))
        layout.addRow(self.list_elements)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        # Initialize list with the first lattice (if any)
        if lattice_dict:
            self.update_filter_options(self.combo_lattice.currentText())

    def update_filter_options(self, lattice_name: str) -> None:
        """
        Clears and repopulates the element list based on the selected lattice.

        Args:
            lattice_name (str): The name of the selected base lattice.
        """
        self.list_elements.clear()
        
        if not lattice_name or lattice_name not in self.lattice_dict:
            return

        # Get the Lattice Object
        lattice = self.lattice_dict[lattice_name]
        
        # Get elements and sort them for display
        elements = sorted(list(lattice.elements))
        
        for elem in elements:
            item = QListWidgetItem(str(elem))
            # Add checkbox flag
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)  # Default to empty filter
            self.list_elements.addItem(item)

    def get_data(self) -> Tuple[str, str, Set[str]]:
        """
        Retrieves the user input from the dialog.

        Returns:
            Tuple[str, str, Set[str]]: A tuple containing:
                - The name of the new filtered lattice.
                - The name of the base lattice.
                - A set of elements selected for the filter.
        """
        name = self.name_input.text().strip()
        base_lat_name = self.combo_lattice.currentText()
        
        filter_set = set()
        
        # Collect all checked items
        for i in range(self.list_elements.count()):
            item = self.list_elements.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                filter_set.add(item.text())

        return name, base_lat_name, filter_set