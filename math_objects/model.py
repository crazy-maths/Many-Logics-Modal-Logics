"""
Model Module.

This module defines the Model class, which represents a complete many-logics modal
structure. It connects a Many-Lattice (algebraic structure) with a set of
Worlds (states) and an accessibility relation (graph structure).
"""

from typing import Set, Dict, Optional, Tuple
from collections import defaultdict


from math_objects.lattice import ManyLattice
from math_objects.world import World

# Optional dependencies for visualization
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False


class Model:
    """
    Represents a complete many-logics modal structure.

    A Model consists of:
    1. A Many-Lattice (algebraic foundation).
    2. A set of Worlds (states).
    3. An accessibility relation between worlds.
    4. A set of propositions.
    5. A set of actions.
    """

    def __init__(
        self,
        name_model: str,
        many_lattice: ManyLattice,
        worlds: Set[World],
        initial_state: World,
        assessibility_relation: Optional[Dict[World, Set[World]]] = None,
        props: Optional[Set[str]] = None,
        actions : Optional[Set[str]] = None
    ):
        """
        Initializes the Model.

        Args:
            name_model (str): The unique name of the model.
            many_lattice (ManyLattice): The algebraic structure governing the logic.
            worlds (Set[World]): The set of all worlds in the model.
            initial_state (World): The starting world/state.
            assessibility_relation (Optional[Dict]): A mapping World -> Set[World].
            props (Optional[Set[str]]): A set of propositions.
            actions (Optional[Set[str]]): A set of actions.

        Raises:
            TypeError: If arguments are not of the expected types.
        """
        if not isinstance(many_lattice, ManyLattice):
            raise TypeError("The 'many_lattice' argument must be an instance of ManyLattice.")
        
        for world in worlds:
            if not isinstance(world, World):
                raise TypeError("The 'worlds' argument must contain instances of World.")

        self.name_model = name_model
        self.many_lattice = many_lattice
        self.worlds = worlds
        self.initial_state = initial_state
        self.props = props if props is not None else set()
        self.actions = actions if actions is not None else set()
        
        # Safe initialization for mutable default
        self.accessibility_relation = assessibility_relation if assessibility_relation is not None else defaultdict(set)

        # Ensure every world has an entry in the accessibility dictionary
        for world in self.worlds:
            if world not in self.accessibility_relation:
                self.accessibility_relation[world] = set()

    def add_world(self, world: World) -> None:
        """
        Adds a World object to the model.

        Args:
            world (World): The World object to add.

        Raises:
            TypeError: If the argument is not a World.
            ValueError: If a world with the same name already exists.
            Exception: If the world's lattice is not a registered sublattice.
        """
        if not isinstance(world, World):
            raise TypeError("The 'world' argument must be an instance of World.")
        
        if self.get_world(world.name_short):
            raise ValueError(f"A world with the name '{world.name_short}' already exists.")
        
        # Check by name to ensure compatibility with loaded objects
        valid_sublattice_names = [lat.name for lat in self.many_lattice.comp_sub_lat]
        if world.lattice.name not in valid_sublattice_names:
            raise Exception("The world's lattice must be a complete sublattice of the base lattice.")
        
        self.worlds.add(world)
        # Initialize empty relation
        if world not in self.accessibility_relation:
            self.accessibility_relation[world] = set()

    def delete_world(self, world: World) -> None:
        """
        Deletes a World object from the model.

        Args:
            world (World): The World object to delete.

        Raises:
            TypeError: If argument is not a World.
            ValueError: If the world has existing relations (incoming or outgoing).
        """
        if not isinstance(world, World):
            raise TypeError("The 'world' argument must be an instance of World.")
        
        # Check outgoing relations
        if self.accessibility_relation.get(world):
            raise ValueError(f"World '{world.name_short}' has outgoing relations. Delete them first.")
        
        # Check incoming relations
        for other_world, targets in self.accessibility_relation.items():
            if world in targets:
                raise ValueError(f"World '{other_world.name_short}' points to '{world.name_short}'. Remove relation first.")
        
        if world in self.accessibility_relation:
            del self.accessibility_relation[world]
            
        self.worlds.remove(world)

    def get_world(self, name_short: str) -> Optional[World]:
        """
        Retrieves a World object by its short name.

        Args:
            name_short (str): The short name of the world.

        Returns:
            Optional[World]: The World object if found, else None.
        """
        for world in self.worlds:
            if world.name_short == name_short:
                return world
        return None

    def add_relation(self, world1_name: str, world2_name: str) -> None:
        """
        Adds a directed accessibility relation from world1 to world2.

        Args:
            world1_name (str): Name of the source world.
            world2_name (str): Name of the target world.

        Raises:
            ValueError: If either world does not exist.
        """
        world1 = self.get_world(world1_name)
        world2 = self.get_world(world2_name)
        
        if not world1 or not world2:
            raise ValueError("Both worlds must exist in the model.")
        
        self.accessibility_relation[world1].add(world2)

    def delete_relation(self, world1_name: str, world2_name: str) -> None:
        """
        Removes a directed accessibility relation.

        Args:
            world1_name (str): Name of the source world.
            world2_name (str): Name of the target world.

        Raises:
            ValueError: If worlds do not exist or relation does not exist.
        """
        world1 = self.get_world(world1_name)
        world2 = self.get_world(world2_name)

        if not world1 or not world2:
            raise ValueError("Both worlds must exist in the model.")
        
        if world2 not in self.accessibility_relation[world1]:
            raise ValueError(f"No relation exists from {world1_name} to {world2_name}.")
        
        self.accessibility_relation[world1].remove(world2)

    def get_accessible_worlds(self, world_name: str) -> Set[World]:
        """
        Retrieves all worlds accessible from the given world.

        Args:
            world_name (str): The name of the starting world.

        Returns:
            Set[World]: A set of accessible World objects.
        """
        world = self.get_world(world_name)
        if not world:
            raise ValueError(f"World '{world_name}' does not exist.")

        return self.accessibility_relation.get(world, set())

    def draw_graph(self) -> None:
        """
        Draws the graph of worlds with accessibility relations.
        Vertices are worlds (with their names), edges are accessibility relations.
        The initial world is highlighted with a different color.
        """
        if not VISUALIZATION_AVAILABLE:
            print("Visualization libraries (networkx, matplotlib) not installed.")
            return

        G = nx.DiGraph()

        # Add nodes (worlds)
        for world in self.worlds:
            G.add_node(world.name_short)

        # Add edges (relations)
        for w1, accessible_worlds in self.accessibility_relation.items():
            for w2 in accessible_worlds:
                G.add_edge(w1.name_short, w2.name_short)

        # Define node colors
        node_colors = []
        for node in G.nodes():
            if node == self.initial_state.name_short:
                node_colors.append("red")  # Color initial world red
            else:
                node_colors.append("lightblue")  # Other worlds light blue

        # Draw the graph
        plt.figure(figsize=(8, 6))
        pos = nx.spring_layout(G)  # Layout for positioning
        nx.draw_networkx_nodes(G, pos, node_size=1000, node_color=node_colors, edgecolors="black")
        nx.draw_networkx_edges(G, pos, arrowstyle="->", arrowsize=20, edge_color="gray")
        nx.draw_networkx_labels(G, pos, font_size=12, font_weight="bold")

        plt.title("Model Worlds and Accessibility Relations")
        plt.axis("off")
        plt.show()

    def __repr__(self) -> str:
        return f"{self.name_model}"