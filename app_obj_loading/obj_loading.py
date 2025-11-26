"""
Object Loading Dialog Module.

This module provides a reusable dialog for selecting multiple items from a list.
It is used primarily for loading multiple objects (Lattices, Models, etc.)
from JSON files into the main application workspace.
"""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QDialog,
    QDialogButtonBox,
    QListWidget,
    QAbstractItemView,
    QWidget
)


class MultiSelectDialog(QDialog):
    """
    A dialog that presents a list of items and allows the user to select one or more.

    Attributes:
        selected_items (List[str]): Stores the text of the items selected by the user
                                    after the dialog is accepted.
    """

    def __init__(self, title: str, items: List[str], parent: Optional[QWidget] = None):
        """
        Initializes the MultiSelectDialog.

        Args:
            title (str): The title to display on the dialog window.
            items (List[str]): A list of strings to populate the selection widget.
            parent (Optional[QWidget]): The parent widget (MainWindow).
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(400, 500)
        self.selected_items: List[str] = []

        # Main Layout
        layout = QVBoxLayout(self)

        # Instruction Label
        layout.addWidget(QLabel("Select objects to load (Hold Ctrl/Shift to select multiple):"))

        # List Widget Configuration
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_widget.addItems(items)
        layout.addWidget(self.list_widget)

        # Dialog Buttons (OK / Cancel)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self) -> None:
        """
        Handles the OK button click.
        Captures the currently selected items before closing the dialog.
        """
        self.selected_items = [item.text() for item in self.list_widget.selectedItems()]
        super().accept()

    def get_selected_items(self) -> List[str]:
        """
        Retrieves the list of items selected by the user.

        Returns:
            List[str]: A list of strings corresponding to the selected rows.
        """
        return self.selected_items