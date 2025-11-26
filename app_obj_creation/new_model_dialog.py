"""
New Model Dialog Module.

This module provides a tabbed dialog window for creating new Model objects.
It guides the user through three steps:
1. General Info: Naming, selecting the Many-Lattice, and choosing Worlds.
2. Relations: Defining the accessibility relation graph between selected worlds.
3. Actions: Defining the actions of the model.
"""

from collections import defaultdict
from typing import List, Set, Dict, Tuple, Optional
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QComboBox,
    QListWidget,
    QAbstractItemView,
    QTabWidget,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QLabel
)
from PyQt6.QtCore import Qt


class NewModelDialog(QDialog):
    """
    A dialog for assembling a Model from existing components.
    """

    def __init__(
        self,
        many_lattice_names: List[str],
        world_names: List[str],
        props: Set[str],
        parent: Optional[QWidget] = None
    ):
        """
        Initializes the dialog.

        Args:
            many_lattice_names (List[str]): List of available Many-Lattice names.
            world_names (List[str]): List of available World names.
            props (Set[str]): Set of global propositions defined in the project.
            parent (Optional[QWidget]): The parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Create New Model")
        self.resize(600, 600)
        
        self.props = props
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        self.main_layout.addWidget(self.tabs)

        # --- TAB 1: General Info ---
        self.tab_general = QWidget()
        self.setup_general_tab(many_lattice_names, world_names)
        self.tabs.addTab(self.tab_general, "1. General Info")

        # --- TAB 2: Accessibility Relations ---
        self.tab_relations = QWidget()
        self.setup_relations_tab()
        self.tabs.addTab(self.tab_relations, "2. World Relations")

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.main_layout.addWidget(buttons)

    def setup_general_tab(self, ml_names: List[str], w_names: List[str]) -> None:
        """
        Sets up the General Info tab (Name, Lattice selection, World selection).
        """
        layout = QVBoxLayout(self.tab_general)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Model Name")
        
        self.combo_ml = QComboBox()
        self.combo_ml.addItems(ml_names)
        
        self.actions_input = QLineEdit()
        self.actions_input.setPlaceholderText("e.g: a1, a2")
        self.actions_input.setToolTip("Define actions here.")

        form.addRow("Name:", self.name_input)
        form.addRow("Many Lattice:", self.combo_ml)
        form.addRow("Actions:", self.actions_input)
        layout.addLayout(form)

        layout.addWidget(QLabel("Select Worlds:"))
        self.list_worlds = QListWidget()
        self.list_worlds.addItems(w_names)
        self.list_worlds.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        
        # Triggers updates for subsequent tabs when selection changes
        self.list_worlds.itemSelectionChanged.connect(self.update_relations_matrix) 
        self.list_worlds.itemSelectionChanged.connect(self.update_initial_state)
        layout.addWidget(self.list_worlds)

        form2 = QFormLayout()
        self.combo_initial = QComboBox()
        form2.addRow("Initial State:", self.combo_initial)
        layout.addLayout(form2)

    def setup_relations_tab(self) -> None:
        """Sets up the table for defining accessibility relations."""
        layout = QVBoxLayout(self.tab_relations)
        layout.addWidget(QLabel("Accessibility (Row -> Col):"))
        self.table_relations = QTableWidget()
        layout.addWidget(self.table_relations)

    # --- DYNAMIC UPDATES ---

    def update_initial_state(self) -> None:
        """Updates the 'Initial State' dropdown based on selected worlds."""
        selected = [item.text() for item in self.list_worlds.selectedItems()]
        current = self.combo_initial.currentText()
        
        self.combo_initial.clear()
        self.combo_initial.addItems(selected)
        
        # Preserve selection if still valid
        if current in selected:
            self.combo_initial.setCurrentText(current)

    def update_relations_matrix(self) -> None:
        """Rebuilds the relations table (N x N) based on selected worlds."""
        selected_names = [item.text() for item in self.list_worlds.selectedItems()]
        n = len(selected_names)
        
        self.table_relations.setRowCount(n)
        self.table_relations.setColumnCount(n)
        self.table_relations.setHorizontalHeaderLabels(selected_names)
        self.table_relations.setVerticalHeaderLabels(selected_names)
        
        for r in range(n):
            for c in range(n):
                item = QTableWidgetItem()
                item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.table_relations.setItem(r, c, item)


    def get_data(self) -> Tuple[str, str, List[str], str, Dict[str, Set[str]], Set[str], Set[str]]:
        """
        Retrieves all data from the dialog inputs and tables.

        Returns:
            Tuple containing:
            1. name (str)
            2. many_lattice_name (str)
            3. world_names (List[str])
            4. initial_state_name (str)
            5. relations_map (Dict[str, Set[str]])
            6. props (Set[str])
            7. actions (Set[str])
        """
        # 1. Basic Data
        name = self.name_input.text().strip()
        ml_name = self.combo_ml.currentText()
        raw_actions = self.actions_input.text()
        actions = [x.strip() for x in raw_actions.split(',') if x.strip()]
        
        # 2. Worlds Data
        selected_items = self.list_worlds.selectedItems()
        world_names_list = [item.text() for item in selected_items]
        initial_name = self.combo_initial.currentText()

        # 3. Accessibility Data (Tab 2)
        relations_map = defaultdict(set)
        for r in range(self.table_relations.rowCount()):
            source = self.table_relations.verticalHeaderItem(r).text()
            for c in range(self.table_relations.columnCount()):
                if self.table_relations.item(r, c).checkState() == Qt.CheckState.Checked:
                    target = self.table_relations.horizontalHeaderItem(c).text()
                    relations_map[source].add(target)

        return name, ml_name, world_names_list, initial_name, relations_map, self.props, actions