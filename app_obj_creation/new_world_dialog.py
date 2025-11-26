"""
New World Dialog Module.

This module provides a dialog window for creating new World objects.
It facilitates the assignment of a Lattice to a World and provides a dynamic
interface for assigning truth values (elements of that lattice) to every
propositional variable defined in the project.
"""

from typing import Dict, Set, Tuple, Optional, Any
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QComboBox,
    QGroupBox,
    QVBoxLayout,
    QWidget
)

class NewWorldDialog(QDialog):
    """
    A dialog for creating a new World and assigning truth values to propositions.
    """

    def __init__(
        self, 
        lattice_dict: Dict[str, Any], 
        props: Set[str], 
        parent: Optional[QWidget] = None
    ):
        """
        Initializes the dialog.

        Args:
            lattice_dict (Dict[str, Any]): Dictionary mapping lattice names to Lattice objects.
            props (Set[str]): A set of propositional variables (e.g., {'p', 'q'}) that need assignments.
            parent (Optional[QWidget]): The parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Create New World")
        self.resize(450, 500)
        
        self.lattice_dict = lattice_dict
        self.props = sorted(list(props))
        self.assignment_widgets: Dict[str, QComboBox] = {}
        
        # Main Layout
        main_layout = QVBoxLayout(self)
        
        # --- Top Section: Basic Info ---
        form_layout = QFormLayout()
        
        self.long_name_input = QLineEdit()
        self.long_name_input.setPlaceholderText("Unique identifier (e.g., World_1)")
        
        self.short_name_input = QLineEdit()
        self.short_name_input.setPlaceholderText("Graph label (e.g., w1)")
        
        self.combo_lattice = QComboBox()
        self.combo_lattice.addItems(sorted(list(self.lattice_dict.keys())))
        self.combo_lattice.currentTextChanged.connect(self.update_assignment_options)
        
        form_layout.addRow("Long Name:", self.long_name_input)
        form_layout.addRow("Short Name:", self.short_name_input)
        form_layout.addRow("Assigned Lattice:", self.combo_lattice)
        
        main_layout.addLayout(form_layout)
        
        # --- Middle Section: Assignments ---
        self.assignments_group = QGroupBox("Proposition Assignments")
        self.assignments_layout = QFormLayout(self.assignments_group)
        
        for p in self.props:
            combo = QComboBox()
            self.assignment_widgets[p] = combo
            self.assignments_layout.addRow(f"Value for '{p}':", combo)
            
        main_layout.addWidget(self.assignments_group)
        
        # Initialize options based on the default selection
        if self.lattice_dict:
            first_lat_name = self.combo_lattice.currentText()
            self.update_assignment_options(first_lat_name)

        # --- Bottom Section: Buttons ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def update_assignment_options(self, lattice_name: str) -> None:
        """
        Updates the available options for all proposition assignments based on the selected lattice.
        Triggered when the user changes the Lattice selection.

        Args:
            lattice_name (str): The name of the newly selected lattice.
        """
        if lattice_name not in self.lattice_dict:
            return

        # Get elements of the selected lattice
        current_lattice = self.lattice_dict[lattice_name]
        # Sort elements for consistent UI
        elements = sorted([str(e) for e in current_lattice.elements])
        
        # Update every assignment combobox
        for combo in self.assignment_widgets.values():
            current_selection = combo.currentText()
            combo.clear()
            combo.addItems(elements)
            
            # Attempt to preserve previous selection if it exists in the new lattice
            index = combo.findText(current_selection)
            if index >= 0:
                combo.setCurrentIndex(index)

    def get_data(self) -> Tuple[str, str, str, Dict[str, str]]:
        """
        Retrieves the user input from the dialog.

        Returns:
            Tuple containing:
            1. long_name (str): The unique ID of the world.
            2. short_name (str): The display label.
            3. selected_lattice_name (str): The name of the assigned lattice.
            4. assignments_dict (Dict[str, str]): Map of {proposition: value}.
        """
        long_name = self.long_name_input.text().strip()
        short_name = self.short_name_input.text().strip()
        lat_name = self.combo_lattice.currentText()
        
        # Collect data from the dynamic comboboxes
        assignments = {}
        for p, combo in self.assignment_widgets.items():
            assignments[p] = combo.currentText()
        
        return long_name, short_name, lat_name, assignments