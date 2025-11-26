"""
Main Application Module.

This module defines the MainWindow class, which serves as the primary user interface
for the Lattice & Model Editor. It orchestrates the creation, visualization, and
management of algebraic structures (Lattices) and modal logic components (Worlds, Models).
"""

import sys
from typing import Dict, Set, Any
from collections import defaultdict

# GUI Imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QMenu, QMessageBox, QInputDialog, QLabel, QSplitter, QLineEdit, QComboBox, 
    QTreeWidget, QTreeWidgetItem, QFrame, QPushButton, QListWidget, 
    QAbstractItemView, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QPoint

# Internal Logic Imports
from math_objects.lattice import Lattice, FilteredLattice, ManyLattice
from math_objects.world import World
from math_objects.model import Model
from json_object_handler.json_handler import JSONHandler
from parser.formula_parser import FormulaParser

# Dialog Imports
from app_obj_creation.new_lattice_dialog import NewLatticeDialog
from app_obj_creation.new_filtered_lattice_dialog import NewFilteredLatticeDialog
from app_obj_creation.new_many_lattice_dialog import NewManyLatticeDialog
from app_obj_creation.new_world_dialog import NewWorldDialog
from app_obj_creation.new_model_dialog import NewModelDialog
from app_obj_loading.obj_loading import MultiSelectDialog


class MainWindow(QMainWindow):
    """
    The main application window containing the workspace, sidebar, and tools.
    """

    def __init__(self):
        """Initializes the main window and internal storage structures."""
        super().__init__()
        self.setWindowTitle("Many Logics Modal Structure Editor")
        self.resize(1000, 700)

        # --- Internal Storage ---
        # Dictionaries mapping Name -> Object
        self.lattices: Dict[str, Lattice] = {}
        self.filtered_lattices: Dict[str, FilteredLattice] = {}
        self.many_lattices: Dict[str, ManyLattice] = {}
        self.worlds: Dict[str, World] = {}
        self.models: Dict[str, Model] = {}
        
        # Default propositions
        self.props: Set[str] = {"p", "q", "r", "s"}

        # Tree categories mapping (Label -> TreeItem)
        self.tree_categories: Dict[str, QTreeWidgetItem] = {}

        # Initialize UI
        self.setup_ui()
        self.create_menu()

    def setup_ui(self) -> None:
        """Constructs the main user interface layout."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # ==========================================
        #           LEFT WIDGET: Sidebar
        # ==========================================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # 1. Project Explorer (Tree)
        label_list = QLabel("Project Explorer:")
        label_list.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(label_list)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_tree_context_menu)
        left_layout.addWidget(self.tree)
        self.init_tree_categories()

        self.tree.itemClicked.connect(self.on_tree_item_clicked)

        # 2. Visual Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        left_layout.addWidget(line)

        # 3. Propositions Section
        label_props = QLabel("Propositions:")
        label_props.setStyleSheet("font-weight: bold; margin-top: 10px;")
        left_layout.addWidget(label_props)

        self.prop_list_widget = QListWidget()
        self.prop_list_widget.setMaximumHeight(150)
        self.prop_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.refresh_props_ui()
        left_layout.addWidget(self.prop_list_widget)

        # Buttons (Add / Remove)
        btn_layout = QHBoxLayout()
        self.btn_add_prop = QPushButton("Add")
        self.btn_add_prop.clicked.connect(self.add_proposition)
        
        self.btn_remove_prop = QPushButton("Remove")
        self.btn_remove_prop.clicked.connect(self.remove_proposition)
        
        btn_layout.addWidget(self.btn_add_prop)
        btn_layout.addWidget(self.btn_remove_prop)
        left_layout.addLayout(btn_layout)

        splitter.addWidget(left_widget)

        # ==========================================
        #          RIGHT WIDGET: Workspace
        # ==========================================
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)

        # 1. Details Section
        label_details = QLabel("Object Details:")
        label_details.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(label_details)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setPlaceholderText("Select an object in the tree to view details.")
        self.details_text.setMaximumHeight(200)
        right_layout.addWidget(self.details_text)

        # Hasse Diagram Button
        self.btn_hasse = QPushButton("Show Hasse Diagram")
        self.btn_hasse.clicked.connect(self.show_current_hasse)
        self.btn_hasse.setEnabled(False) 
        right_layout.addWidget(self.btn_hasse)

        # Separator
        line_eval = QFrame()
        line_eval.setFrameShape(QFrame.Shape.HLine)
        line_eval.setFrameShadow(QFrame.Shadow.Sunken)
        right_layout.addWidget(line_eval)

        # 2. Formula Evaluator Section
        label_eval = QLabel("Formula Evaluator:")
        label_eval.setStyleSheet("font-weight: bold; margin-top: 10px;")
        right_layout.addWidget(label_eval)

        # --- A. Model and World Selection ---
        selection_layout = QHBoxLayout()
        
        self.combo_models = QComboBox()
        self.combo_models.setPlaceholderText("Select Model")
        self.combo_models.currentIndexChanged.connect(self.update_world_combo)
        selection_layout.addWidget(QLabel("Model:"))
        selection_layout.addWidget(self.combo_models)
        
        self.combo_worlds = QComboBox()
        self.combo_worlds.setPlaceholderText("Select World")
        selection_layout.addWidget(QLabel("World:"))
        selection_layout.addWidget(self.combo_worlds)

        self.btn_visualize = QPushButton("Show Graph")
        self.btn_visualize.clicked.connect(self.visualize_current_model)
        selection_layout.addWidget(self.btn_visualize)
        
        right_layout.addLayout(selection_layout)

        # --- B. Interpretation Switch ---
        eval_mode_layout = QHBoxLayout()
        self.eval_radio_down = QRadioButton("Down")
        self.eval_radio_up = QRadioButton("Up")
        self.eval_radio_down.setChecked(True)  # Default
        self.eval_radio_down.setToolTip("Use Down Interpretation (Heyting)")
        
        self.eval_btn_group = QButtonGroup()
        self.eval_btn_group.addButton(self.eval_radio_down)
        self.eval_btn_group.addButton(self.eval_radio_up)
        
        eval_mode_layout.addWidget(QLabel("Interpretation:"))
        eval_mode_layout.addWidget(self.eval_radio_down)
        eval_mode_layout.addWidget(self.eval_radio_up)
        eval_mode_layout.addStretch()
        
        right_layout.addLayout(eval_mode_layout)

        # --- C. Syntax Help ---
        lbl_help = QLabel("Syntax: ~A, []A, <>A, (A & B), (A | B), (A -> B), (A <-> B)")
        lbl_help.setStyleSheet("color: gray; font-size: 11px; margin-top: 5px;")
        right_layout.addWidget(lbl_help)

        # --- D. Symbol Buttons ---
        symbols_layout = QHBoxLayout()
        symbols_layout.setSpacing(2)
        
        symbol_map = [
            ("□", "[]"), 
            ("◇", "<>"), 
            ("¬", "~"), 
            ("∧", "&"), 
            ("∨", "|"), 
            ("→", "->"), 
            ("↔", "<->")
        ]

        for label, insert_text in symbol_map:
            btn = QPushButton(label)
            btn.setFixedWidth(30)
            btn.setToolTip(f"Insert {insert_text}")
            # Note: lambda loop variable capture fix
            btn.clicked.connect(lambda checked, t=insert_text: self.insert_symbol(t))
            symbols_layout.addWidget(btn)

        symbols_layout.addStretch()
        right_layout.addLayout(symbols_layout)

        # --- E. Input Field ---
        input_layout = QHBoxLayout()
        self.formula_input = QLineEdit()
        self.formula_input.setPlaceholderText("Type formula here...")
        self.formula_input.returnPressed.connect(self.evaluate_formula) 
        
        self.btn_eval = QPushButton("Evaluate")
        self.btn_eval.clicked.connect(self.evaluate_formula)
        
        self.btn_validity = QPushButton("Check Validity")
        self.btn_validity.setToolTip("Check if the formula holds in ALL worlds of the model")
        self.btn_validity.clicked.connect(self.check_model_validity)
        
        input_layout.addWidget(self.formula_input)
        input_layout.addWidget(self.btn_eval)
        input_layout.addWidget(self.btn_validity)
        right_layout.addLayout(input_layout)

        # Result Area
        self.result_label = QLabel("Result: ")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px; color: blue; margin-top: 5px;")
        right_layout.addWidget(self.result_label)
        
        right_layout.addStretch()

        splitter.addWidget(right_widget)
        splitter.setSizes([250, 750])

    def init_tree_categories(self) -> None:
        """Creates the top-level category items in the Tree Widget."""
        categories = ["Lattices", "Filtered Lattices", "Many Lattices", "Worlds", "Models"]
        for cat in categories:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, cat)
            item.setExpanded(True)  # Keep them open by default
            self.tree_categories[cat] = item

    def create_menu(self) -> None:
        """Initializes the application menu bar actions."""
        menu_bar = self.menuBar()

        # --- NEW MENU ---
        new_menu = menu_bar.addMenu("New")
        new_menu.addAction("Lattice").triggered.connect(self.create_new_lattice)
        new_menu.addAction("Filtered Lattice").triggered.connect(self.create_new_filtered_lattice)
        new_menu.addAction("Many Lattice").triggered.connect(self.create_new_many_lattice)
        new_menu.addAction("World").triggered.connect(self.create_new_world)
        new_menu.addAction("Model").triggered.connect(self.create_new_model)

        # --- LOAD MENU ---
        load_menu = menu_bar.addMenu("Load")
        load_menu.addAction("Lattice").triggered.connect(lambda: self.load_specific_object("Lattice", "lattices", "name"))
        load_menu.addAction("Filtered Lattice").triggered.connect(lambda: self.load_specific_object("Filtered Lattice", "filtered_lattices", "filtered_lattice_name"))
        load_menu.addAction("Many Lattice").triggered.connect(lambda: self.load_specific_object("Many Lattice", "many_lattices", "many_lattice_name"))
        load_menu.addAction("World").triggered.connect(lambda: self.load_specific_object("World", "worlds", "world_name"))
        load_menu.addAction("Model").triggered.connect(lambda: self.load_specific_object("Model", "models", "model_name"))

        # --- DELETE MENU ---
        del_menu = menu_bar.addMenu("Delete")
        del_menu.addAction("Lattice").triggered.connect(lambda: self.delete_specific_object("Lattice", "lattices", "name"))
        del_menu.addAction("Filtered Lattice").triggered.connect(lambda: self.delete_specific_object("Filtered Lattice", "filtered_lattices", "filtered_lattice_name"))
        del_menu.addAction("Many Lattice").triggered.connect(lambda: self.delete_specific_object("Many Lattice", "many_lattices", "many_lattice_name"))
        del_menu.addAction("World").triggered.connect(lambda: self.delete_specific_object("World", "worlds", "world_name"))
        del_menu.addAction("Model").triggered.connect(lambda: self.delete_specific_object("Model", "models", "model_name"))

        # --- SEE MENU ---
        see_menu = menu_bar.addMenu("See")
        see_menu.addAction("Lattices in File").triggered.connect(lambda: self.see_objects_in_file("lattices", "name"))
        see_menu.addAction("Filtered Lattices in File").triggered.connect(lambda: self.see_objects_in_file("filtered_lattices", "filtered_lattice_name"))
        see_menu.addAction("Many Lattices in File").triggered.connect(lambda: self.see_objects_in_file("many_lattices", "many_lattice_name"))
        see_menu.addAction("Worlds in File").triggered.connect(lambda: self.see_objects_in_file("worlds", "world_name"))
        see_menu.addAction("Models in File").triggered.connect(lambda: self.see_objects_in_file("models", "model_name"))

    # ==========================================
    #             UI HELPER METHODS
    # ==========================================

    def refresh_model_combo(self) -> None:
        """Refreshes the Model ComboBox with currently loaded models."""
        self.combo_models.blockSignals(True)
        self.combo_models.clear()
        self.combo_models.addItems(list(self.models.keys()))
        self.combo_models.blockSignals(False)
        
        # Trigger world update manually for the first item
        self.update_world_combo()

    def update_world_combo(self) -> None:
        """Updates the World ComboBox based on the selected Model."""
        self.combo_worlds.clear()
        
        model_name = self.combo_models.currentText()
        if not model_name or model_name not in self.models:
            return

        model = self.models[model_name]
        
        if hasattr(model, 'worlds'):
            world_names = sorted([w.name_long for w in model.worlds])
            self.combo_worlds.addItems(world_names)

    def insert_symbol(self, text: str) -> None:
        """Inserts the given text into the formula input field at the cursor."""
        self.formula_input.insert(text)
        self.formula_input.setFocus()

    def refresh_props_ui(self) -> None:
        """Refreshes the Propositions list widget."""
        self.prop_list_widget.clear()
        for p in sorted(list(self.props)):
            self.prop_list_widget.addItem(p)

    def add_proposition(self) -> None:
        """Shows dialog to add new propositions."""
        text, ok = QInputDialog.getText(self, "Add Propositions", 
                                        "Enter propositions, e.g: p, q, r:")
        if ok and text:
            raw_items = text.split(',')
            new_items = [item.strip() for item in raw_items if item.strip()]
            
            if not new_items: return

            added_count = 0
            skipped_items = []

            for p in new_items:
                if p not in self.props:
                    self.props.add(p)
                    added_count += 1
                else:
                    skipped_items.append(p)
            
            if added_count > 0:
                self.refresh_props_ui()
                msg = f"Added {added_count} proposition(s)."
                if skipped_items:
                    msg += f" (Skipped existing: {', '.join(skipped_items)})"
                self.statusBar().showMessage(msg, 5000)
            elif skipped_items:
                QMessageBox.information(self, "Info", 
                                        f"No new propositions added.\nAlready exist: {', '.join(skipped_items)}")

    def remove_proposition(self) -> None:
        """Removes selected propositions from the project."""
        selected_items = self.prop_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select at least one proposition to remove.")
            return
        
        props_to_remove = [item.text() for item in selected_items]
        count = len(props_to_remove)
        
        msg = f"Are you sure you want to remove these {count} propositions?"
        if count <= 5:
            msg = f"Are you sure you want to remove: {', '.join(props_to_remove)}?"

        confirm = QMessageBox.question(self, "Confirm Remove", msg,
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            for p in props_to_remove:
                if p in self.props:
                    self.props.remove(p)
            
            self.refresh_props_ui()
            self.statusBar().showMessage(f"Removed {count} propositions.", 3000)

    # ==========================================
    #            OBJECT MANAGEMENT
    # ==========================================

    def is_object_loaded(self, category: str, name: str) -> bool:
        """Checks if an object is already loaded in memory."""
        if category == "Lattice": return name in self.lattices
        if category == "Filtered Lattice": return name in self.filtered_lattices
        if category == "Many Lattice": return name in self.many_lattices
        if category == "World": return name in self.worlds
        if category == "Model": return name in self.models
        return False

    def register_object(self, name: str, obj: Any, type_str: str) -> None:
        """Adds object to internal dict and Tree Widget."""
        key_map = {
            "Lattice": self.lattices,
            "Filtered Lattice": self.filtered_lattices,
            "Many Lattice": self.many_lattices,
            "World": self.worlds,
            "Model": self.models
        }
        tree_cat_map = {
            "Lattice": "Lattices",
            "Filtered Lattice": "Filtered Lattices",
            "Many Lattice": "Many Lattices",
            "World": "Worlds",
            "Model": "Models"
        }

        if type_str in key_map:
            key_map[type_str][name] = obj
        
        category_key = tree_cat_map.get(type_str)
        if category_key and category_key in self.tree_categories:
            parent_item = self.tree_categories[category_key]
            
            # Check duplicate visual
            exists = False
            for i in range(parent_item.childCount()):
                if parent_item.child(i).text(0) == name:
                    exists = True
                    break
            
            if not exists:
                item = QTreeWidgetItem(parent_item)
                item.setText(0, name)
        
        if type_str == "Model":
            self.refresh_model_combo()

    def remove_from_tree(self, category_label: str, object_name: str) -> None:
        """Removes a specific node from the TreeWidget."""
        root_item = self.tree_categories.get(category_label)
        if not root_item: return

        for i in range(root_item.childCount()):
            child = root_item.child(i)
            if child.text(0) == object_name:
                root_item.removeChild(child)
                break

    def remove_object_from_memory(self, ui_category: str, tree_category_label: str, object_name: str) -> None:
        """
        Removes the object from Memory and Tree immediately (No file deletion).
        """
        memory_map = {
            "Lattice": self.lattices,
            "Filtered Lattice": self.filtered_lattices,
            "Many Lattice": self.many_lattices,
            "World": self.worlds,
            "Model": self.models,
        }
        memory_dict = memory_map.get(ui_category)

        try:
            if object_name in memory_dict:
                del memory_dict[object_name]
            
            self.remove_from_tree(tree_category_label, object_name)
            
            if ui_category == "Model": 
                self.refresh_model_combo()
            elif ui_category == "World": 
                self.update_world_combo()
            
            self.details_text.clear()
            self.statusBar().showMessage(f"Removed '{object_name}' from workspace.", 2000)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove object:\n{e}")

    # ==========================================
    #             FILE OPERATIONS
    # ==========================================

    def see_objects_in_file(self, json_key: str, name_key: str) -> None:
        """Displays a list of names found in the standard file for a category."""
        filename_map = {
            "lattices": "json_files/lattices.json",
            "filtered_lattices": "json_files/filtered_lattices.json",
            "many_lattices": "json_files/many_lattices.json",
            "worlds": "json_files/worlds.json",
            "models": "json_files/models.json"
        }
        fname = filename_map.get(json_key)
        
        if not fname:
            QMessageBox.warning(self, "Error", f"Unknown configuration for key: {json_key}")
            return

        names = JSONHandler.get_names_from_json(fname, json_key, name_key)
        
        if not names:
            QMessageBox.information(self, "Result", f"No items found in {fname}.")
            return

        if len(names) > 50:
            display_text = "\n".join(names[:50]) + f"\n\n... and {len(names)-50} more."
        else:
            display_text = "\n".join(names)

        QMessageBox.information(self, f"Found {len(names)} items", 
                                f"File: {fname}\n\nAvailable Objects:\n{display_text}")

    def load_specific_object(self, ui_category_name: str, json_key: str, name_key: str) -> None:
        """Loads multiple objects from JSON files via a selection dialog."""
        filename_map = {
            "Lattice": "json_files/lattices.json",
            "Filtered Lattice": "json_files/filtered_lattices.json",
            "Many Lattice": "json_files/many_lattices.json",
            "World": "json_files/worlds.json",
            "Model": "json_files/models.json"
        }
        fname = filename_map.get(ui_category_name)
        if not fname: return

        names = JSONHandler.get_names_from_json(fname, json_key, name_key)
        if not names:
            QMessageBox.information(self, "Load", f"No {ui_category_name}s found in {fname}.")
            return

        dialog = MultiSelectDialog(f"Load {ui_category_name}", names, self)
        if dialog.exec():
            selected_names = dialog.get_selected_items()
            if not selected_names: return

            loaded_count = 0
            for selected_name in selected_names:
                if self.is_object_loaded(ui_category_name, selected_name):
                    print(f"Skipping '{selected_name}' (Already loaded).")
                    continue

                try:
                    obj = None
                    
                    if ui_category_name == "Lattice":
                        obj = JSONHandler.load_lattice_from_json(fname, selected_name)
                        if obj: self.register_object(selected_name, obj, "Lattice")

                    elif ui_category_name == "Filtered Lattice":
                        obj = JSONHandler.load_filtered_lattice_from_json(fname, selected_name)
                        if obj:
                            self.register_object(selected_name, obj, "Filtered Lattice")
                            base_name = obj.name
                            base_lat = JSONHandler.load_lattice_from_json("json_files/lattices.json", base_name)
                            if not self.is_object_loaded("Lattice", base_name):
                                if base_lat: self.register_object(base_name, base_lat, "Lattice")

                    elif ui_category_name == "Many Lattice":
                        obj = JSONHandler.load_many_lattice_from_json(fname, selected_name)
                        if obj:
                            self.register_object(selected_name, obj, "Many Lattice")
                            base_fil_lat_name = obj.name_filtered_lattice
                            base_filtered_lat = JSONHandler.load_filtered_lattice_from_json("json_files/filtered_lattices.json", base_fil_lat_name)
                            if not self.is_object_loaded("Filtered Lattice", base_fil_lat_name):
                                if base_filtered_lat: self.register_object(base_fil_lat_name, base_filtered_lat, "Filtered Lattice")
                            
                            base_name = base_filtered_lat.name
                            base_lat = JSONHandler.load_lattice_from_json("json_files/lattices.json", base_name)
                            if not self.is_object_loaded("Lattice", base_name):
                                if base_lat: self.register_object(base_name, base_lat, "Lattice")
                            
                            for sub in obj.comp_sub_lat:
                                if not self.is_object_loaded("Lattice", sub.name):
                                    self.register_object(sub.name, sub, "Lattice")

                    elif ui_category_name == "World":
                        obj = JSONHandler.load_world_from_json(fname, selected_name)
                        if obj:
                            self.register_object(selected_name, obj, "World")
                            lat = obj.lattice
                            if not self.is_object_loaded("Lattice", lat.name):
                                self.register_object(lat.name, lat, "Lattice")

                    elif ui_category_name == "Model":
                        obj1 = JSONHandler.load_model_from_json(fname, selected_name)
                        if obj1:
                            self.register_object(selected_name, obj1, "Model")
                            obj = obj1.many_lattice
                            if obj:
                                if not self.is_object_loaded("Many Lattice", obj.name_many_lattice):
                                    self.register_object(obj.name_many_lattice, obj, "Many Lattice")

                                base_fil_lat_name = obj.name_filtered_lattice
                                base_filtered_lat = JSONHandler.load_filtered_lattice_from_json("json_files/filtered_lattices.json", base_fil_lat_name)
                                if not self.is_object_loaded("Filtered Lattice", base_fil_lat_name):
                                    if base_filtered_lat: self.register_object(base_fil_lat_name, base_filtered_lat, "Filtered Lattice")
                                
                                base_name = base_filtered_lat.name
                                base_lat = JSONHandler.load_lattice_from_json("json_files/lattices.json", base_name)
                                if not self.is_object_loaded("Lattice", base_name):
                                    if base_lat: self.register_object(base_name, base_lat, "Lattice")
                                
                                for sub in obj.comp_sub_lat:
                                    if not self.is_object_loaded("Lattice", sub.name):
                                        self.register_object(sub.name, sub, "Lattice")
                            
                            for w in obj1.worlds:
                                if not self.is_object_loaded("World", w.name_long):
                                    self.register_object(w.name_long, w, "World")
                                    if not self.is_object_loaded("Lattice", w.lattice.name):
                                        self.register_object(w.lattice.name, w.lattice, "Lattice")

                    if obj or (ui_category_name == "Model" and obj1):
                        loaded_count += 1
                except Exception as e:
                    print(f"Failed to load '{selected_name}': {e}")

            self.statusBar().showMessage(f"Successfully loaded {loaded_count} objects.", 5000)

    def delete_specific_object(self, ui_category: str, json_key: str, name_key: str) -> None:
        """Deletes objects from JSON file and memory."""
        filename_map = {
            "Lattice": "json_files/lattices.json",
            "Filtered Lattice": "json_files/filtered_lattices.json",
            "Many Lattice": "json_files/many_lattices.json",
            "World": "json_files/worlds.json",
            "Model": "json_files/models.json"
        }
        fname = filename_map.get(ui_category)
        if not fname: return

        names = JSONHandler.get_names_from_json(fname, json_key, name_key)
        if not names:
            QMessageBox.information(self, "Delete", f"No {ui_category}s found in file.")
            return

        dialog = MultiSelectDialog(f"Delete {ui_category}", names, self)
        if dialog.exec():
            selected_names = dialog.get_selected_items()
            if not selected_names: return

            confirm = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete {len(selected_names)} item(s)?\nThis cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirm != QMessageBox.StandardButton.Yes:
                return

            deleted_count = 0
            config = {
                "Lattice": (JSONHandler.delete_lattice_from_json, self.lattices, "Lattices"),
                "Filtered Lattice": (JSONHandler.delete_filtered_lattice_from_json, self.filtered_lattices, "Filtered Lattices"),
                "Many Lattice": (JSONHandler.delete_many_lattice_from_json, self.many_lattices, "Many Lattices"),
                "World": (JSONHandler.delete_world_from_json, self.worlds, "Worlds"),
                "Model": (JSONHandler.delete_model_from_json, self.models, "Models"),
            }
            handler_func, memory_dict, tree_cat = config.get(ui_category)

            for name in selected_names:
                try:
                    handler_func(fname, name)
                    if name in memory_dict: del memory_dict[name]
                    self.remove_from_tree(tree_cat, name)
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting {name}: {e}")

            self.statusBar().showMessage(f"Deleted {deleted_count} objects.", 5000)
            if ui_category == "Model": self.refresh_model_combo()
            elif ui_category == "World": self.update_world_combo()

    # ==========================================
    #             OBJECT CREATION
    # ==========================================

    def create_new_lattice(self) -> None:
        dialog = NewLatticeDialog(self)
        if dialog.exec():
            name, elements, relations, negation, implication = dialog.get_data()
            if not name or not elements or not relations:
                QMessageBox.warning(self, "Error", "Name, elements and relations are required.")
                return
            try:
                lat = Lattice(name, elements, relations, negation, implication)
                if not JSONHandler.save_lattice_to_json("json_files/lattices.json", lat):
                    raise ValueError(f"A lattice '{name}' already exists.")
                self.register_object(name, lat, "Lattice")
                QMessageBox.information(self, "Success", f"Lattice {name} created and saved.")
            except Exception as e:
                QMessageBox.critical(self, "Creation Error", str(e))

    def create_new_filtered_lattice(self) -> None:
        if not self.lattices:
            QMessageBox.warning(self, "Error", "No base lattices loaded.")
            return

        dialog = NewFilteredLatticeDialog(self.lattices, self)
        if dialog.exec():
            new_name, base_lattice_name, filter_set = dialog.get_data()
            if not new_name:
                QMessageBox.warning(self, "Error", "Name cannot be empty.")
                return
            try:
                base_lat = self.lattices[base_lattice_name]
                fl = FilteredLattice(
                    new_name, base_lattice_name, base_lat.elements, base_lat.relations, 
                    base_lat.negation_map, base_lat.implication_map, filter_set
                )
                if not JSONHandler.save_filtered_lattice_to_json("json_files/filtered_lattices.json", fl):
                    raise ValueError(f"A filtered lattice '{new_name}' already exists.")
                self.register_object(new_name, fl, "Filtered Lattice")
                QMessageBox.information(self, "Success", f"Filtered Lattice '{new_name}' created.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create: {str(e)}")

    def create_new_many_lattice(self) -> None:
        if not self.filtered_lattices:
            QMessageBox.warning(self, "Error", "No Filtered Lattices loaded.")
            return
        if not self.lattices:
            QMessageBox.warning(self, "Error", "No Base Lattices loaded.")
            return

        dialog = NewManyLatticeDialog(self.filtered_lattices, self.lattices, self)
        if dialog.exec():
            new_name, base_fl_name, selected_subsets, existing_names, interp_mode = dialog.get_data()

            if not new_name:
                QMessageBox.warning(self, "Error", "Name cannot be empty.")
                return
            if not selected_subsets and not existing_names:
                QMessageBox.warning(self, "Error", "Select at least one sublattice.")
                return

            try:
                base_fl = self.filtered_lattices[base_fl_name]
                base_lat_name = getattr(base_fl, 'name_lattice', base_fl.name)
                base_lat = self.lattices[base_lat_name]
                
                comp_sub_lat_objects = []

                # 1. Existing
                for lat_name in existing_names:
                    if lat_name in self.lattices:
                        comp_sub_lat_objects.append(self.lattices[lat_name])

                # 2. Generated
                for i, subset in enumerate(selected_subsets):
                    subset_str = {str(e).strip() for e in subset}
                    sub_name = f"{new_name}_gen_{i+1}"
                    
                    sub_relations = set()
                    for (a, b) in base_lat.relations:
                        sa, sb = str(a).strip(), str(b).strip()
                        if sa in subset_str and sb in subset_str:
                            sub_relations.add((sa, sb))
                    
                    sub_lat = Lattice(sub_name, subset_str, sub_relations, {}, {})
                    comp_sub_lat_objects.append(sub_lat)

                # 3. Create ManyLattice
                ml = ManyLattice(
                    new_name, base_fl.name_filtered_lattice, base_fl.name,
                    base_fl.elements, base_fl.relations, comp_sub_lat_objects,
                    base_fl.negation_map, base_fl.implication_map, base_fl.filter
                )

                # 4. Populate Maps using Interpretation
                def safe_get_imp(a, b):
                    if (a, b) in base_lat.implication_map: return base_lat.implication_map[(a, b)]
                    if str((a, b)) in base_lat.implication_map: return base_lat.implication_map[str((a, b))]
                    return None

                def safe_get_neg(a):
                    if a in base_lat.negation_map: return base_lat.negation_map[a]
                    if str(a) in base_lat.negation_map: return base_lat.negation_map[str(a)]
                    return None

                for sub_lat in comp_sub_lat_objects:
                    if not sub_lat.implication_map and not sub_lat.negation_map:
                        # Implication
                        for a in sub_lat.elements:
                            for b in sub_lat.elements:
                                base_res = safe_get_imp(a, b)
                                if base_res:
                                    res = ml.down_interpretation(sub_lat, base_res) if interp_mode == "down" else ml.up_interpretation(sub_lat, base_res)
                                    sub_lat.implication_map[(a, b)] = res
                        # Negation
                        for a in sub_lat.elements:
                            base_res = safe_get_neg(a)
                            if base_res:
                                res = ml.down_interpretation(sub_lat, base_res) if interp_mode == "down" else ml.up_interpretation(sub_lat, base_res)
                                sub_lat.negation_map[a] = res

                        if not JSONHandler.save_lattice_to_json("json_files/lattices.json", sub_lat):
                             print(f"Note: Sublattice {sub_lat.name} updated.")
                        self.register_object(sub_lat.name, sub_lat, "Lattice")

                if not JSONHandler.save_many_lattice_to_json("json_files/many_lattices.json", ml):
                    raise ValueError(f"A many lattice {new_name} already exists.")
                self.register_object(new_name, ml, "Many Lattice") 
                QMessageBox.information(self, "Success", f"Many Lattice created using {interp_mode} Interpretation.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def create_new_world(self) -> None:
        if not self.lattices:
            QMessageBox.warning(self, "Error", "No Lattices loaded.")
            return
        dialog = NewWorldDialog(self.lattices, self.props, self)
        if dialog.exec():
            long_name, short_name, lat_name, assignments = dialog.get_data()
            if not long_name or not short_name:
                QMessageBox.warning(self, "Error", "Names cannot be empty.")
                return
            try:
                selected_lattice = self.lattices[lat_name]
                new_world = World(long_name, short_name, selected_lattice, assignments)
                if not JSONHandler.save_world_to_json("json_files/worlds.json", new_world):
                    raise ValueError(f"World '{long_name}' already exists.")
                self.register_object(long_name, new_world, "World")
                QMessageBox.information(self, "Success", f"World '{long_name}' created.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create world: {str(e)}")

    def create_new_model(self) -> None:
        if not self.many_lattices or not self.worlds:
            QMessageBox.warning(self, "Error", "Many Lattices and Worlds required.")
            return
        dialog = NewModelDialog(list(self.many_lattices.keys()), list(self.worlds.keys()), self.props, self)
        if dialog.exec():
            name, ml_name, w_names, init_name, rel_map, props, actions = dialog.get_data()
            if not name or not w_names or not init_name:
                QMessageBox.warning(self, "Error", "Missing required fields.")
                return
            try:
                many_lat = self.many_lattices[ml_name]
                initial_w = self.worlds[init_name]
                selected_worlds = [self.worlds[wn] for wn in w_names]
                
                acc_rel = defaultdict(set)
                for w in selected_worlds: acc_rel[w] = set()
                for src, targets in rel_map.items():
                    s_obj = self.worlds[src]
                    for t in targets: acc_rel[s_obj].add(self.worlds[t])

                new_model = Model(name, many_lat, set(selected_worlds), initial_w, acc_rel, props, actions)
                if not JSONHandler.save_model_to_json("json_files/models.json", new_model):
                    raise ValueError(f"Model '{name}' already exists.")
                self.register_object(name, new_model, "Model")
                QMessageBox.information(self, "Success", f"Model '{name}' created.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))


    # ==========================================
    #           ANALYSIS & VISUALIZATION
    # ==========================================

    def on_tree_item_clicked(self, item: QTreeWidgetItem) -> None:
        """Displays object details when clicked in the tree."""
        parent = item.parent()
        if not parent: return 

        category = parent.text(0)
        name = item.text(0)
        details = ""

        # Toggle Hasse Button
        is_visualizable = category in ["Lattices", "Filtered Lattices", "Many Lattices", "Worlds"]
        self.btn_hasse.setEnabled(is_visualizable)

        try:
            if category == "Lattices" and name in self.lattices:
                lat = self.lattices[name]
                details += f"=== LATTICE: {lat.name} ===\n\n"
                elems = ", ".join(sorted(list(lat.elements)))
                details += f"Elements ({len(lat.elements)}):\n{{{elems}}}\n\n"
                rels = ", ".join([f"({a},{b})" for a,b in sorted(list(lat.relations))])
                details += f"Relations:\n{{{rels}}}\n\n"
                
                details += "Negation:\n" + ("\n".join([f"  ¬{k} = {v}" for k,v in sorted(lat.negation_map.items())]) if lat.negation_map else "  (None)")
                details += "\n\nImplication:\n" + ("\n".join([f"  {k[0]} -> {k[1]} = {v}" for k,v in sorted(lat.implication_map.items())]) if lat.implication_map else "  (None)")

            elif category == "Filtered Lattices" and name in self.filtered_lattices:
                fl = self.filtered_lattices[name]
                details += f"=== FILTERED LATTICE: {fl.name_filtered_lattice} ===\n"
                details += f"Base Lattice: {fl.name}\n\n"
                details += f"Filter Set: {{{', '.join(sorted(list(fl.filter)))}}}\n"

            elif category == "Many Lattices" and name in self.many_lattices:
                ml = self.many_lattices[name]
                details += f"=== MANY LATTICE: {ml.name_many_lattice} ===\n"
                details += f"Base Filtered Lattice: {ml.name_filtered_lattice}\n\n"
                details += "Complete Sublattices:\n"
                for sub in ml.comp_sub_lat:
                    details += f" - {sub.name}: {{{', '.join(sorted(list(sub.elements)))}}}\n"

            elif category == "Worlds" and name in self.worlds:
                w = self.worlds[name]
                details += f"=== WORLD: {w.name_long} ===\nShort Name: {w.name_short}\n"
                details += f"Assigned Lattice: {w.lattice.name}\n\nAssignments:\n"
                details += "\n".join([f"  {p} = {v}" for p,v in w.assignments.items()]) if w.assignments else "  (None)"

            elif category == "Models" and name in self.models:
                m = self.models[name]
                details += f"=== MODEL: {m.name_model} ===\nMany Lattice: {m.many_lattice.name_many_lattice}\n"
                details += f"Initial State: {m.initial_state.name_short}\n\nWorlds:\n"
                for w in m.worlds: details += f" - {w.name_short}\n"
                
                details += "\nAccessibility (Outgoing):\n"
                sorted_worlds = sorted(m.worlds, key=lambda x: x.name_short)
                has_edges = False
                for src in sorted_worlds:
                    targets = m.accessibility_relation.get(src, set())
                    if targets:
                        has_edges = True
                        t_str = ", ".join(sorted([t.name_short for t in targets]))
                        details += f"  {src.name_short} -> {{{t_str}}}\n"
                    else:
                        details += f"  {src.name_short} -> (End/Sink)\n"
                if not has_edges: details += "  (None)\n"

                details += "\nActions:\n{" + ", ".join([f"{a}" for a in m.actions]) + "}" if m.actions else "{}"

            self.details_text.setText(details)

        except Exception as e:
            self.details_text.setText(f"Error displaying details: {e}")

    def visualize_current_model(self) -> None:
        model_name = self.combo_models.currentText()
        if not model_name or model_name not in self.models:
            QMessageBox.warning(self, "Error", "Please select a Model first.")
            return
        try:
            self.models[model_name].draw_graph()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to draw graph:\n{e}")

    def show_current_hasse(self) -> None:
        item = self.tree.currentItem()
        if not item or not item.parent(): return

        cat, name = item.parent().text(0), item.text(0)
        target = None
        
        if cat == "Lattices": target = self.lattices.get(name)
        elif cat == "Filtered Lattices": target = self.filtered_lattices.get(name)
        elif cat == "Many Lattices": target = self.many_lattices.get(name)
        elif cat == "Worlds": target = self.worlds.get(name).lattice if name in self.worlds else None

        if target: 
            try: target.draw_hasse()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))
        else:
            QMessageBox.warning(self, "Error", "Selected object is not a lattice.")

    # ==========================================
    #           FORMULA EVALUATION
    # ==========================================

    def open_tree_context_menu(self, position: QPoint) -> None:
        item = self.tree.itemAt(position)
        if not item or not item.parent(): return
        
        name, cat = item.text(0), item.parent().text(0)
        cat_map = {"Lattices": "Lattice", "Filtered Lattices": "Filtered Lattice", 
                   "Many Lattices": "Many Lattice", "Worlds": "World", "Models": "Model"}
        
        ui_cat = cat_map.get(cat)
        if not ui_cat: return

        menu = QMenu()
        action = menu.addAction(f"Remove '{name}'")
        if menu.exec(self.tree.viewport().mapToGlobal(position)) == action:
            self.remove_object_from_memory(ui_cat, cat, name)

    def evaluate_formula(self) -> None:
        try:
            f_str = self.formula_input.text().strip()
            if not f_str: 
                self.result_label.setText("Result: Empty")
                return

            m_name, w_name = self.combo_models.currentText(), self.combo_worlds.currentText()
            if not m_name or not w_name:
                QMessageBox.warning(self, "Error", "Select Model and World.")
                return

            model = self.models[m_name]
            world = next((w for w in model.worlds if w.name_long == w_name), None)
            if not world: return

            parser = FormulaParser(f_str)
            root = parser.parse()

            # Validation
            unknown = [a for a in root.get_atoms() if a not in world.assignments]
            if unknown:
                QMessageBox.warning(self, "Error", f"Missing assignments for: {', '.join(unknown)}")
                return

            mode = "up" if self.eval_radio_up.isChecked() else "down"
            res = root.evaluate(model, world, interpretation=mode)
            
            satisfied = res in model.many_lattice.filter
            status = "<span style='color:green;'>[SATISFIED]</span>" if satisfied else "<span style='color:red;'>[NOT SATISFIED]</span>"
            
            self.result_label.setText(f"Result: <b>{res}</b>  {status}")
            self.statusBar().showMessage(f"Evaluated in {w_name}: {res}", 5000)

        except ValueError as ve:
            self.result_label.setText("Syntax Error")
            QMessageBox.warning(self, "Syntax Error", str(ve))
        except Exception as e:
            self.result_label.setText("Error")
            QMessageBox.critical(self, "Error", str(e))

    def check_model_validity(self) -> None:
        try:
            f_str = self.formula_input.text().strip()
            m_name = self.combo_models.currentText()
            if not f_str or not m_name: return

            model = self.models[m_name]
            model_filter = model.many_lattice.filter
            
            try:
                root = FormulaParser(f_str).parse()
            except ValueError as ve:
                QMessageBox.warning(self, "Syntax Error", str(ve))
                return

            atoms = root.get_atoms()
            for w in model.worlds:
                missing = [a for a in atoms if a not in w.assignments]
                if missing:
                    QMessageBox.warning(self, "Error", f"World '{w.name_long}' missing: {', '.join(missing)}")
                    return

            mode = "up" if self.eval_radio_up.isChecked() else "down"
            failed = []
            
            for w in sorted(model.worlds, key=lambda x: x.name_long):
                if root.evaluate(model, w, interpretation=mode) not in model_filter:
                    failed.append(w.name_long)

            if not failed:
                msg = "<span style='color:green;'>Valid in Model: YES</span>"
                self.statusBar().showMessage(f"Valid in {m_name}", 5000)
            else:
                fail_str = ", ".join(failed[:3]) + ("..." if len(failed)>3 else "")
                msg = f"<span style='color:red;'>Valid in Model: NO</span> (Failed: {fail_str})"
                self.statusBar().showMessage(f"Invalid. Failed in {len(failed)} worlds.", 5000)
            
            self.result_label.setText(msg)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())