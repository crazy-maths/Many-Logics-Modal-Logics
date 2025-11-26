"""
JSON Handler Module.

This module provides the JSONHandler class, a static utility for reading, writing and deleting
the project's data structures (Lattices, Worlds, Models) to JSON files.
It handles serialization, error checking, and referential integrity reconstruction.
"""

import json
import re
import os
from ast import literal_eval
from typing import Optional, List, Dict, Any

from math_objects.lattice import Lattice, FilteredLattice, ManyLattice
from math_objects.world import World
from math_objects.model import Model


class JSONHandler:
    """
    Static utility class for managing JSON persistence of algebraic and logical objects.
    """

    @staticmethod
    def _load_safe(filename: str) -> Dict[str, Any]:
        """
        Helper: Safely loads JSON from a file.
        
        Args:
            filename (str): Path to the file.

        Returns:
            Dict[str, Any]: The loaded JSON data, or an empty dict if the file is missing, empty, or invalid.
        """
        if not os.path.exists(filename):
            return {}
        
        if os.path.getsize(filename) == 0:
            return {}

        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            return {}

    # ==========================================
    #                 LATTICE
    # ==========================================

    @staticmethod
    def load_lattice_from_json(filename: str, lattice_name: str) -> Optional[Lattice]:
        """
        Loads a Lattice object by name from a JSON file.

        Args:
            filename (str): Path to the JSON file.
            lattice_name (str): Name of the lattice to load.

        Returns:
            Optional[Lattice]: The loaded Lattice object, or None if not found/error.
        """
        data = JSONHandler._load_safe(filename)
            
        if 'lattices' in data and isinstance(data['lattices'], list):
            for lattice_data in data['lattices']:
                name = lattice_data.get('name')

                if name == lattice_name:
                    try:
                        elements = set(lattice_data.get('elements', []))
                        relations = set(tuple(rel) for rel in lattice_data.get('relations', []))
                        negation_map = lattice_data.get('negation_map', {})

                        # Robustly load implication map (converting string keys back to tuples)
                        implication_map_raw = lattice_data.get('implication_map', {})
                        implication_map = {}
                        for pair_str, value in implication_map_raw.items():
                            try:
                                # Attempt safe eval for keys like "('a', 'b')"
                                key = literal_eval(pair_str)
                                if isinstance(key, (list, tuple)):
                                    implication_map[tuple(key)] = value
                            except:
                                pass # Skip malformed keys

                        if elements and relations:
                            return Lattice(name, elements, relations, negation_map, implication_map)
                    except Exception as e:
                        print(f"Error creating Lattice object for '{name}': {e}")
                        return None
        
        print(f"Lattice '{lattice_name}' not found in {filename}.")
        return None

    @staticmethod
    def save_lattice_to_json(filename: str, new_lattice: Lattice) -> bool:
        """
        Saves a Lattice object to a JSON file.

        Args:
            filename (str): Path to the JSON file.
            new_lattice (Lattice): The object to save.

        Returns:
            bool: True if saved successfully, False otherwise.
        """
        try:
            data = JSONHandler._load_safe(filename)
            if 'lattices' not in data:
                data['lattices'] = []
            
            lattices_list = data['lattices']

            # Check for duplicates
            for lattice_data in lattices_list:
                if lattice_data.get('name') == new_lattice.name:
                    raise ValueError(f"A lattice '{new_lattice.name}' already exists.")
            
            # Serialize maps (Tuple keys -> String keys)
            implication_map_strings = {str(k): v for k, v in new_lattice.implication_map.items()}
            
            lattice_dict = {
                "name": new_lattice.name,
                "elements": list(new_lattice.elements),
                "relations": [list(rel) for rel in new_lattice.relations],
                "negation_map": new_lattice.negation_map,
                "implication_map": implication_map_strings
            }
            
            lattices_list.append(lattice_dict)
            data['lattices'] = lattices_list
            
            # Compact Formatting using Regex
            json_str = json.dumps(data, indent=1)
            json_str = re.sub(r'\[\s+("[^"]+",)\s+("[^"]+")\s+\]', r'[\1 \2]', json_str)

            with open(filename, 'w') as f:
                f.write(json_str)
            
            print(f"Lattice '{new_lattice.name}' saved successfully.")
            return True
        except Exception as e:
            print(f"Save Error: {e}")
            return False

    @staticmethod
    def delete_lattice_from_json(filename: str, lattice_name: str) -> None:
        """
        Deletes a Lattice by name from a JSON file.

        Args:
            filename (str): Path to the JSON file.
            lattice_name (str): Name of the lattice to delete.
        """
        data = JSONHandler._load_safe(filename)
        if 'lattices' not in data: return

        original_len = len(data['lattices'])
        data['lattices'] = [l for l in data['lattices'] if l.get('name') != lattice_name]

        if len(data['lattices']) == original_len:
            print(f"Error: Lattice '{lattice_name}' not found.")
            return

        try:
            json_str = json.dumps(data, indent=1)
            json_str = re.sub(r'\[\s+("[^"]+",)\s+("[^"]+")\s+\]', r'[\1 \2]', json_str)
            with open(filename, 'w') as f:
                f.write(json_str)
            print(f"Lattice '{lattice_name}' deleted.")
        except Exception as e:
            print(f"Delete Error: {e}")

    # ==========================================
    #             FILTERED LATTICE
    # ==========================================

    @staticmethod
    def load_filtered_lattice_from_json(filename: str, filtered_lattice_name: str) -> Optional[FilteredLattice]:
        """
        Loads a FilteredLattice object by name.

        Args:
            filename (str): Path to the JSON file.
            filtered_lattice_name (str): Name of the object to load.

        Returns:
            Optional[FilteredLattice]: The loaded object or None on failure.
        """
        data = JSONHandler._load_safe(filename)
            
        if 'filtered_lattices' in data:
            for fl_data in data['filtered_lattices']:
                if fl_data.get('filtered_lattice_name') == filtered_lattice_name:
                    try:
                        name_lattice = fl_data.get('lattice_name')
                        base = JSONHandler.load_lattice_from_json("json_files/lattices.json", name_lattice)
                        if not base: return None

                        filter_set = set(fl_data.get('filter', []))
                        
                        return FilteredLattice(
                            filtered_lattice_name, name_lattice, 
                            base.elements, base.relations, 
                            base.negation_map, base.implication_map, filter_set
                        )
                    except Exception as e:
                        print(f"Error loading Filtered Lattice: {e}")
                        return None
        return None

    @staticmethod
    def save_filtered_lattice_to_json(filename: str, new_fl: FilteredLattice) -> bool:
        """
        Saves a FilteredLattice object.

        Args:
            filename (str): Path to the JSON file.
            new_fl (FilteredLattice): The object to save.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            data = JSONHandler._load_safe(filename)
            if 'filtered_lattices' not in data: data['filtered_lattices'] = []
            
            fl_list = data['filtered_lattices']
            name = new_fl.name_filtered_lattice

            for item in fl_list:
                if item.get('filtered_lattice_name') == name:
                    raise ValueError(f"Filtered lattice '{name}' already exists.")
            
            fl_dict = {
                "filtered_lattice_name": name,
                "lattice_name": new_fl.name,
                "filter": list(new_fl.filter)
            }
            
            fl_list.append(fl_dict)
            data['filtered_lattices'] = fl_list
            
            with open(filename, 'w') as f:
                f.write(json.dumps(data, indent=1))
            
            print(f"Filtered Lattice '{name}' saved successfully.")
            return True
        except Exception as e:
            print(f"Save Error: {e}")
            return False

    @staticmethod
    def delete_filtered_lattice_from_json(filename: str, fl_name: str) -> None:
        """
        Deletes a FilteredLattice by name.

        Args:
            filename (str): Path to the JSON file.
            fl_name (str): Name of the object to delete.
        """
        data = JSONHandler._load_safe(filename)
        if 'filtered_lattices' not in data: return

        new_list = [l for l in data['filtered_lattices'] if l.get('filtered_lattice_name') != fl_name]
        
        if len(new_list) == len(data['filtered_lattices']):
            return

        data['filtered_lattices'] = new_list
        with open(filename, 'w') as f:
            f.write(json.dumps(data, indent=1))
        print(f"Filtered Lattice '{fl_name}' deleted.")

    # ==========================================
    #               MANY LATTICE
    # ==========================================

    @staticmethod
    def load_many_lattice_from_json(filename: str, many_lattice_name: str) -> Optional[ManyLattice]:
        """
        Loads a ManyLattice object by name.

        Args:
            filename (str): Path to the JSON file.
            many_lattice_name (str): Name of the object to load.

        Returns:
            Optional[ManyLattice]: The loaded object or None.
        """
        data = JSONHandler._load_safe(filename)
            
        if 'many_lattices' in data:
            for ml_data in data['many_lattices']:
                if ml_data.get('many_lattice_name') == many_lattice_name:
                    try:
                        fl_name = ml_data.get('filtered_lattice_name')
                        fl = JSONHandler.load_filtered_lattice_from_json("json_files/filtered_lattices.json", fl_name)
                        if not fl: return None

                        # Load Complete Sublattices
                        comp_sub_lat_list = []
                        for sub_name in ml_data.get("comp_sub_lat", []):
                            sub_lat = JSONHandler.load_lattice_from_json("json_files/lattices.json", sub_name)
                            if sub_lat: comp_sub_lat_list.append(sub_lat)

                        return ManyLattice(
                            many_lattice_name, fl.name_filtered_lattice, fl.name,
                            fl.elements, fl.relations, comp_sub_lat_list,
                            fl.negation_map, fl.implication_map, fl.filter
                        )
                    except Exception as e:
                        print(f"Error loading Many Lattice: {e}")
                        return None
        return None

    @staticmethod
    def save_many_lattice_to_json(filename: str, new_ml: ManyLattice) -> bool:
        """
        Saves a ManyLattice object.

        Args:
            filename (str): Path to the JSON file.
            new_ml (ManyLattice): The object to save.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            data = JSONHandler._load_safe(filename)
            if 'many_lattices' not in data: data['many_lattices'] = []
            
            ml_list = data['many_lattices']
            name = new_ml.name_many_lattice

            for item in ml_list:
                if item.get('many_lattice_name') == name:
                    raise ValueError(f"Many lattice '{name}' already exists.")
            
            ml_dict = {
                "many_lattice_name": name,
                "filtered_lattice_name": new_ml.name_filtered_lattice,
                "comp_sub_lat": [lat.name for lat in new_ml.comp_sub_lat]
            }
            
            ml_list.append(ml_dict)
            data['many_lattices'] = ml_list
            
            with open(filename, 'w') as f:
                f.write(json.dumps(data, indent=1))
            return True
        except Exception as e:
            print(f"Save Error: {e}")
            return False

    @staticmethod
    def delete_many_lattice_from_json(filename: str, ml_name: str) -> None:
        """
        Deletes a ManyLattice by name.

        Args:
            filename (str): Path to the JSON file.
            ml_name (str): Name of the object to delete.
        """
        data = JSONHandler._load_safe(filename)
        if 'many_lattices' not in data: return

        new_list = [l for l in data['many_lattices'] if l.get('many_lattice_name') != ml_name]
        data['many_lattices'] = new_list
        
        with open(filename, 'w') as f:
            f.write(json.dumps(data, indent=1))
        print(f"Many Lattice '{ml_name}' deleted.")

    # ==========================================
    #                  WORLD
    # ==========================================

    @staticmethod
    def load_world_from_json(filename: str, world_name: str) -> Optional[World]:
        """
        Loads a World object by name.

        Args:
            filename (str): Path to the JSON file.
            world_name (str): Long name of the world.

        Returns:
            Optional[World]: The loaded object or None.
        """
        data = JSONHandler._load_safe(filename)
            
        if 'worlds' in data:
            for w_data in data['worlds']:
                if w_data.get('world_name') == world_name:
                    try:
                        short_name = w_data.get('short_world_name')
                        lattice = JSONHandler.load_lattice_from_json("json_files/lattices.json", w_data.get('lattice'))
                        assignments = w_data.get('assignments', {})
                        
                        if lattice:
                            return World(world_name, short_name, lattice, assignments)
                    except Exception as e:
                        print(f"Error loading World: {e}")
                        return None
        return None

    @staticmethod
    def save_world_to_json(filename: str, new_world: World) -> bool:
        """
        Saves a World object.

        Args:
            filename (str): Path to the JSON file.
            new_world (World): The object to save.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            data = JSONHandler._load_safe(filename)
            if 'worlds' not in data: data['worlds'] = []
            
            w_list = data['worlds']
            name = new_world.name_long

            for item in w_list:
                if item.get('world_name') == name:
                    raise ValueError(f"World '{name}' already exists.")
            
            w_dict = {
                "world_name": name,
                "short_world_name": new_world.name_short,
                "lattice": new_world.lattice.name,
                "assignments": new_world.assignments
            }
            
            w_list.append(w_dict)
            data['worlds'] = w_list
            
            with open(filename, 'w') as f:
                f.write(json.dumps(data, indent=1))
            return True
        except Exception as e:
            return False

    @staticmethod
    def delete_world_from_json(filename: str, w_name: str) -> None:
        """
        Deletes a World by name.

        Args:
            filename (str): Path to the JSON file.
            w_name (str): Name of the world to delete.
        """
        data = JSONHandler._load_safe(filename)
        if 'worlds' not in data: return

        new_list = [w for w in data['worlds'] if w.get('world_name') != w_name]
        data['worlds'] = new_list
        
        with open(filename, 'w') as f:
            f.write(json.dumps(data, indent=1))
        print(f"World '{w_name}' deleted.")

    # ==========================================
    #                  MODEL
    # ==========================================

    @staticmethod
    def load_model_from_json(filename: str, model_name: str) -> Optional[Model]:
        """
        Loads a Model by name.
        
        This method ensures referential integrity by creating World objects ONCE
        and reusing the same instances for the accessibility relation keys.

        Args:
            filename (str): Path to the JSON file.
            model_name (str): Name of the model to load.

        Returns:
            Optional[Model]: The loaded Model object or None.
        """
        data = JSONHandler._load_safe(filename)
            
        if 'models' in data:
            for model_data in data['models']:
                if model_data.get('model_name') == model_name:
                    try:
                        # 1. Load Many Lattice
                        name_ml = model_data.get('many_lattice_name')
                        many_lattice = JSONHandler.load_many_lattice_from_json("json_files/many_lattices.json", name_ml)
                        
                        # 2. Load Worlds (Create ONCE, store in map)
                        worlds_set = set()
                        worlds_map = {} 
                        
                        for w_name in model_data.get("worlds", []):
                            w_obj = JSONHandler.load_world_from_json("json_files/worlds.json", w_name)
                            if w_obj:
                                worlds_set.add(w_obj)
                                worlds_map[w_obj.name_long] = w_obj 
                        
                        # 3. Reconstruct Accessibility using EXISTING objects
                        acc_data = model_data.get("accessability_relation", {})
                        accessability_relation = {}

                        for src_name, targets in acc_data.items():
                            if src_name in worlds_map:
                                src_obj = worlds_map[src_name]
                                target_objs = set()
                                for t_name in targets:
                                    if t_name in worlds_map:
                                        target_objs.add(worlds_map[t_name])
                                accessability_relation[src_obj] = target_objs

                        # 4. Initial State
                        initial_name = model_data.get("initial_state")
                        initial_state = worlds_map.get(initial_name)

                        # 5. Props
                        props = set(model_data.get('props', []))

                        # 6. Actions
                        actions = set(model_data.get('actions', []))

                        if many_lattice and worlds_set and initial_state:
                            return Model(model_name, many_lattice, worlds_set, initial_state, accessability_relation, props, actions)
                    
                    except Exception as e:
                        print(f"Error loading Model: {e}")
                        return None
        return None

    @staticmethod
    def save_model_to_json(filename: str, new_model: Model) -> bool:
        """
        Saves a Model object.

        Args:
            filename (str): Path to the JSON file.
            new_model (Model): The object to save.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            data = JSONHandler._load_safe(filename)
            if 'models' not in data: data['models'] = []
            
            m_list = data['models']
            name = new_model.name_model

            for item in m_list:
                if item.get('model_name') == name:
                    raise ValueError(f"Model '{name}' already exists.")
            
            # Convert accessibility relation (Objects -> Names)
            acc_dict = {}
            for world, targets in new_model.accessibility_relation.items():
                acc_dict[world.name_long] = [t.name_long for t in targets]
            
            model_dict = {
                "model_name": name,
                "many_lattice_name": new_model.many_lattice.name_many_lattice,
                "worlds": [w.name_long for w in new_model.worlds],
                "accessability_relation": acc_dict,
                "initial_state": new_model.initial_state.name_long,
                "props": list(new_model.props),
                "actions": list(new_model.actions)
            }
            
            m_list.append(model_dict)
            data['models'] = m_list
            
            # Compact Save
            json_str = json.dumps(data, indent=1)
            json_str = re.sub(r'\[\s+("[^"]+",)\s+("[^"]+")\s+\]', r'[\1 \2]', json_str)

            with open(filename, 'w') as f:
                f.write(json_str)
            return True
        except Exception as e:
            print(f"Model Save Error: {e}")
            return False

    @staticmethod
    def delete_model_from_json(filename: str, model_name: str) -> None:
        """
        Deletes a Model by name.

        Args:
            filename (str): Path to the JSON file.
            model_name (str): Name of the model to delete.
        """
        data = JSONHandler._load_safe(filename)
        if 'models' not in data: return

        new_list = [m for m in data['models'] if m.get('model_name') != model_name]
        data['models'] = new_list
        
        with open(filename, 'w') as f:
            f.write(json.dumps(data, indent=1))
        print(f"Model '{model_name}' deleted.")

    @staticmethod
    def get_names_from_json(filename: str, json_key: str, name_key: str) -> List[str]:
        """
        Robustly returns a list of object names found in a file under the specific key.

        Args:
            filename (str): Path to the JSON file.
            json_key (str): The top-level key (e.g., 'lattices', 'worlds').
            name_key (str): The key holding the object's name (e.g., 'name', 'world_name').

        Returns:
            List[str]: A list of names found. Returns empty list on error.
        """
        names = []
        try:
            data = JSONHandler._load_safe(filename)
            if json_key in data and isinstance(data[json_key], list):
                for item in data[json_key]:
                    if name_key in item:
                        names.append(item[name_key])
        except Exception as e:
            print(f"Error reading names: {e}")
        return names