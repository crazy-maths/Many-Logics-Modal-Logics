"""
New Lattice Dialog Module.

This module provides a dialog window for creating new Lattice objects from scratch.
It allows the user to input elements and then interactively select relations,
negation mappings, and implication mappings generated from those elements.
"""

import itertools
from typing import Optional, Tuple, Set, Dict, List
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QWidget,
    QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QBrush


class NewLatticeDialog(QDialog):
    """
    A dialog for creating a new Lattice by defining elements and operations manually.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initializes the dialog.

        Args:
            parent (Optional[QWidget]): The parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Create New Lattice")
        self.resize(550, 700)
        
        # Main Layout
        layout = QVBoxLayout(self)
        
        # --- SECTION 1: INPUTS ---
        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.elements_input = QLineEdit()
        self.elements_input.setPlaceholderText("e.g: 0, 1, a, b")
        # Trigger list update when user presses Enter on elements
        self.elements_input.returnPressed.connect(self.populate_lists)
        
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Elements:", self.elements_input)
        layout.addLayout(form_layout)

        # --- SECTION 2: GENERATE BUTTON ---
        self.gen_btn = QPushButton("Generate Options from Elements")
        self.gen_btn.clicked.connect(self.populate_lists)
        layout.addWidget(self.gen_btn)
        
        # --- SECTION 3: LISTS ---
        # Relations List
        layout.addWidget(QLabel("<b>Relations</b> (Select pairs where a ≤ b):"))
        self.rel_list = self.create_list_widget("Check all pairs that are true in the lattice")
        layout.addWidget(self.rel_list)
        
        # Negation List
        layout.addWidget(QLabel("<b>Negation</b> (Select mapping a → ¬a):"))
        self.neg_list = self.create_list_widget("Select exactly one negation for each element")
        layout.addWidget(self.neg_list)

        # Implication List
        layout.addWidget(QLabel("<b>Implication</b> (Select mapping a, b → c):"))
        self.imp_list = self.create_list_widget("Select exactly one result for every pair")
        layout.addWidget(self.imp_list)

        # --- SECTION 4: DIALOG BUTTONS ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def create_list_widget(self, tooltip: str) -> QListWidget:
        """
        Helper to create a QListWidget with standard settings.

        Args:
            tooltip (str): The tooltip text to display on hover.

        Returns:
            QListWidget: The configured list widget.
        """
        lw = QListWidget()
        lw.setSelectionMode(QListWidget.SelectionMode.NoSelection)  # Selection handled via checkboxes
        lw.setToolTip(tooltip)
        return lw

    def add_header_item(self, list_widget: QListWidget, text: str) -> None:
        """
        Creates a visual separator item that cannot be selected.

        Args:
            list_widget (QListWidget): The list to add the header to.
            text (str): The header text.
        """
        item = QListWidgetItem(text)
        
        # Style: Gray background, Bold text
        font = QFont()
        font.setBold(True)
        item.setFont(font)
        item.setBackground(QBrush(QColor("#e0e0e0")))  # Light gray
        item.setForeground(QBrush(QColor("#000000")))
        
        # Flags: NoItemFlags means it cannot be selected or checked
        item.setFlags(Qt.ItemFlag.NoItemFlags) 
        
        list_widget.addItem(item)

    def add_checkable_item(self, list_widget: QListWidget, text: str, 
                           check_state: Qt.CheckState = Qt.CheckState.Unchecked) -> None:
        """
        Adds an item with a checkbox to the list.

        Args:
            list_widget (QListWidget): The target list.
            text (str): The item text.
            check_state (Qt.CheckState): The initial check state (Checked/Unchecked).
        """
        item = QListWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(check_state)
        list_widget.addItem(item)

    def populate_lists(self) -> None:
        """
        Generates combinations (Relations, Negation, Implication) based on the elements input.
        Clears existing lists and repopulates them.
        Reflexive relations (x, x) are automatically checked.
        """
        # 1. Parse elements
        raw_text = self.elements_input.text()
        elements = [e.strip() for e in raw_text.split(',') if e.strip()]
        
        if not elements:
            QMessageBox.warning(self, "Input Error", "Please enter elements first.")
            return

        # 2. Clear existing items
        self.rel_list.clear()
        self.neg_list.clear()
        self.imp_list.clear()
        
        # 3. Populate Relations (Flat list)
        # Note: Pairs (x, y) representing x <= y
        pairs = list(itertools.product(elements, repeat=2))
        for p in pairs:
            text = f"({p[0]}, {p[1]})"
            
            # Reflexivity Check: Automatically check if x == y
            if p[0] == p[1]:
                initial_state = Qt.CheckState.Checked
            else:
                initial_state = Qt.CheckState.Unchecked
                
            self.add_checkable_item(self.rel_list, text, initial_state)

        # 4. Populate Negation (Grouped by Element)
        for x in elements:
            self.add_header_item(self.neg_list, f"Negation of '{x}':")
            for y in elements:
                self.add_checkable_item(self.neg_list, f"({x}, {y})")

        # 5. Populate Implication (Grouped by Input Pair)
        input_pairs = list(itertools.product(elements, repeat=2))
        for (x, y) in input_pairs:
            self.add_header_item(self.imp_list, f"Result of {x} → {y}:")
            for z in elements:
                self.add_checkable_item(self.imp_list, f"({x}, {y}, {z})")

        # 6. Connect Signals for Mutual Exclusion
        # Disconnect first to avoid duplicate signals if button clicked twice
        try:
            self.neg_list.itemChanged.disconnect()
            self.imp_list.itemChanged.disconnect()
        except TypeError:
            pass  # Was not connected

        self.neg_list.itemChanged.connect(self.handle_negation_constraint)
        self.imp_list.itemChanged.connect(self.handle_implication_constraint)

    # --- CONSTRAINT LOGIC ---

    def handle_negation_constraint(self, item: QListWidgetItem) -> None:
        """
        Ensures only ONE negation mapping per element (Function property).
        If (a, b) is checked, automatically unchecks any other (a, x).

        Args:
            item (QListWidgetItem): The item that was changed.
        """
        if item.checkState() == Qt.CheckState.Unchecked:
            return

        # Extract the subject 'x' from (x, y)
        text = item.text().replace('(', '').replace(')', '').replace("'", "")
        parts = [p.strip() for p in text.split(',')]
        if len(parts) < 2: return
        subject = parts[0]

        self.neg_list.blockSignals(True)  # Stop recursion

        for i in range(self.neg_list.count()):
            other_item = self.neg_list.item(i)
            
            # Skip headers
            if not (other_item.flags() & Qt.ItemFlag.ItemIsUserCheckable):
                continue
            
            if other_item == item:
                continue

            # Parse other item
            other_text = other_item.text().replace('(', '').replace(')', '').replace("'", "")
            other_parts = [p.strip() for p in other_text.split(',')]
            
            # If it starts with the same element (e.g., '0'), uncheck it
            if other_parts[0] == subject:
                other_item.setCheckState(Qt.CheckState.Unchecked)

        self.neg_list.blockSignals(False)  # Resume

    def handle_implication_constraint(self, item: QListWidgetItem) -> None:
        """
        Ensures only ONE result per implication pair (Function property).
        If (a, b, c) is checked, unchecks any other (a, b, x).

        Args:
            item (QListWidgetItem): The item that was changed.
        """
        if item.checkState() == Qt.CheckState.Unchecked:
            return

        # Extract (x, y) from (x, y, z)
        text = item.text().replace('(', '').replace(')', '').replace("'", "")
        parts = [p.strip() for p in text.split(',')]
        if len(parts) < 3: return
        subject_pair = (parts[0], parts[1])

        self.imp_list.blockSignals(True)

        for i in range(self.imp_list.count()):
            other_item = self.imp_list.item(i)
            
            if not (other_item.flags() & Qt.ItemFlag.ItemIsUserCheckable):
                continue
            
            if other_item == item:
                continue

            other_text = other_item.text().replace('(', '').replace(')', '').replace("'", "")
            other_parts = [p.strip() for p in other_text.split(',')]
            other_pair = (other_parts[0], other_parts[1])

            if other_pair == subject_pair:
                other_item.setCheckState(Qt.CheckState.Unchecked)

        self.imp_list.blockSignals(False)

    def get_checked_items_text(self, list_widget: QListWidget) -> List[str]:
        """
        Helper to get text of all currently checked items in a list.

        Args:
            list_widget (QListWidget): The list to inspect.

        Returns:
            List[str]: A list of strings of the checked items.
        """
        texts = []
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                if item.checkState() == Qt.CheckState.Checked:
                    texts.append(item.text())
        return texts

    def get_data(self) -> Tuple[str, Set[str], Set[Tuple[str, str]], Dict[str, str], Dict[Tuple[str, str], str]]:
        """
        Returns the processed data in standard Python formats.

        Returns:
            Tuple: (name, elements, relations, negation_dict, implication_dict)
        """
        name = self.name_input.text()
        
        raw_elems = self.elements_input.text().split(',')
        elements = {e.strip() for e in raw_elems if e.strip()}
        
        relations = set()
        negation_dict = {}
        implication_dict = {}
        
        # Process Relations
        for txt in self.get_checked_items_text(self.rel_list):
            clean = txt.replace('(', '').replace(')', '').replace("'", "")
            p = [x.strip() for x in clean.split(',')]
            relations.add((p[0], p[1]))

        # Process Negation
        for txt in self.get_checked_items_text(self.neg_list):
            clean = txt.replace('(', '').replace(')', '').replace("'", "")
            p = [x.strip() for x in clean.split(',')]
            negation_dict[p[0]] = p[1]

        # Process Implication
        for txt in self.get_checked_items_text(self.imp_list):
            clean = txt.replace('(', '').replace(')', '').replace("'", "")
            p = [x.strip() for x in clean.split(',')]
            implication_dict[(p[0], p[1])] = p[2]

        return name, elements, relations, negation_dict, implication_dict