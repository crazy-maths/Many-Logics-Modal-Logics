"""
Lattice and Algebraic Structures Module.

This module defines classes for representing Lattices, Filtered Lattices, 
Many-Lattices, Residuated Lattices, and Twist Structures. It provides methods 
for algebraic operations (meet, join, implication, negation) and visualization.
"""

from typing import Set, Dict, Tuple, Optional, List

# Optional dependencies for visualization
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False


class Lattice:
    """
    Represents a lattice with elements, a partial order, and unary/binary operations.
    """

    def __init__(
        self,
        name: str,
        elements: Set[str],
        relations: Set[Tuple[str, str]],
        negation_map: Optional[Dict[str, str]] = None,
        implication_map: Optional[Dict[Tuple[str, str], str]] = None
    ):
        """
        Initializes the Lattice.

        Args:
            name (str): Unique name of the lattice.
            elements (Set[str]): A set of all elements in the lattice.
            relations (Set[Tuple[str, str]]): A set of tuples (x, y) representing x <= y.
            negation_map (Optional[Dict[str, str]]): Mapping for unary negation.
            implication_map (Optional[Dict[Tuple[str, str], str]]): Mapping for binary implication.

        Raises:
            ValueError: If the structure provided is not a valid lattice (not closed under meet/join).
        """
        self.name = name
        self.elements = set(elements)
        self.relations = set(relations)
        self.negation_map = negation_map if negation_map is not None else {}
        self.implication_map = implication_map if implication_map is not None else {}

        if not self._check_is_lattice():
            raise ValueError(f"The object '{name}' is not a valid lattice.")

        self.bottom = self.meet_set(self.elements)
        self.top = self.join_set(self.elements)

    def is_less_than_or_equal(self, a: str, b: str) -> bool:
        """
        Checks if element 'a' is less than or equal to element 'b'.

        Args:
            a (str): The first element.
            b (str): The second element.

        Returns:
            bool: True if a <= b, False otherwise.
        """
        return (a, b) in self.relations

    def negation(self, variable: str) -> Optional[str]:
        """
        Returns the negation of a variable.

        Args:
            variable (str): The element to negate.

        Returns:
            Optional[str]: The negation of the variable, or None if not defined.
        """
        try:
            return self.negation_map[variable]
        except KeyError:
            print(f"ERROR: Variable '{variable}' has no negation assigned.")
            return None

    def implication(self, variable1: str, variable2: str) -> Optional[str]:
        """
        Returns the implication variable1 -> variable2.

        Args:
            variable1 (str): The antecedent.
            variable2 (str): The consequent.

        Returns:
            Optional[str]: The result of the implication, or None if not defined.
        """
        try:
            return self.implication_map[(variable1, variable2)]
        except KeyError:
            print(f"ERROR: Pair ('{variable1}', '{variable2}') has no implication assigned.")
            return None

    def join(self, a: str, b: str) -> str:
        """
        Computes the join (least upper bound) of two elements.

        Args:
            a (str): The first element.
            b (str): The second element.

        Returns:
            str: The unique least upper bound of a and b.

        Raises:
            ValueError: If elements are not in the lattice or no unique join exists.
        """
        if a not in self.elements or b not in self.elements:
            raise ValueError(f"Elements '{a}' or '{b}' not in the lattice.")

        # Find all common upper bounds
        upper_bounds = {
            x for x in self.elements 
            if self.is_less_than_or_equal(a, x) and self.is_less_than_or_equal(b, x)
        }

        if not upper_bounds:
            raise ValueError(f"No common upper bounds found for '{a}' and '{b}'.")

        # Find the least among the upper bounds
        for x in upper_bounds:
            if all(self.is_less_than_or_equal(x, y) for y in upper_bounds):
                return x

        raise ValueError(f"No unique Join found for '{a}' and '{b}'.")

    def meet(self, a: str, b: str) -> str:
        """
        Computes the meet (greatest lower bound) of two elements.

        Args:
            a (str): The first element.
            b (str): The second element.

        Returns:
            str: The unique greatest lower bound of a and b.

        Raises:
            ValueError: If elements are not in the lattice or no unique meet exists.
        """
        if a not in self.elements or b not in self.elements:
            raise ValueError(f"Elements '{a}' or '{b}' not in the lattice.")

        # Find all common lower bounds
        lower_bounds = {
            x for x in self.elements 
            if self.is_less_than_or_equal(x, a) and self.is_less_than_or_equal(x, b)
        }

        if not lower_bounds:
            raise ValueError(f"No common lower bounds found for '{a}' and '{b}'.")

        # Find the greatest among the lower bounds
        for x in lower_bounds:
            if all(self.is_less_than_or_equal(y, x) for y in lower_bounds):
                return x

        raise ValueError(f"No unique Meet found for '{a}' and '{b}'.")

    def meet_set(self, subset: Optional[Set[str]] = None) -> str:
        """
        Computes the meet of a set of elements.

        Args:
            subset (Optional[Set[str]]): A subset of lattice elements. Defaults to all elements.

        Returns:
            str: The meet of the subset. Returns Top if subset is empty or None.
        """
        if subset is None:
            subset = set()
        
        subset_list = list(subset)
        if not subset_list:
            # If empty subset, return Top
            return self.top

        lower = subset_list[0]
        for element in subset_list:
            lower = self.meet(lower, element)
        return lower

    def join_set(self, subset: Optional[Set[str]] = None) -> str:
        """
        Computes the join of a set of elements.

        Args:
            subset (Optional[Set[str]]): A subset of lattice elements. Defaults to all elements.

        Returns:
            str: The join of the subset. Returns Bottom if subset is empty or None.
        """
        if subset is None:
            subset = set()

        subset_list = list(subset)
        if not subset_list:
            # If empty subset, return Bottom
            return self.bottom

        greatest = subset_list[0]
        for element in subset_list:
            greatest = self.join(greatest, element)
        return greatest

    def _check_is_lattice(self) -> bool:
        """
        Verifies if the structure is a valid lattice by checking closure of operations.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            for x in self.elements:
                for y in self.elements:
                    self.meet(x, y)
                    self.join(x, y)
            return True
        except ValueError as e:
            print(f"Lattice check failed: {e}")
            return False

    def draw_hasse(self) -> None:
        """
        Draws the Hasse Diagram of the lattice using NetworkX.
        It performs a Transitive Reduction and arranges layers vertically.
        """
        if not VISUALIZATION_AVAILABLE:
            print("Visualization libraries (networkx, matplotlib) not installed.")
            return

        if not self.elements:
            print("Lattice is empty.")
            return

        G = nx.DiGraph()
        G.add_nodes_from(self.elements)
        
        edges = [(a, b) for a, b in self.relations if a != b]
        G.add_edges_from(edges)

        # Transitive Reduction
        try:
            TR = nx.transitive_reduction(G)
        except Exception as e:
            print(f"Warning: Transitive reduction failed ({e}). Using full graph.")
            TR = G

        # Vertical Layout Calculation
        try:
            bottom_nodes = [n for n, d in TR.in_degree() if d == 0]
            longest_path = {}
            
            for node in TR.nodes():
                paths = [len(p) for b in bottom_nodes for p in nx.all_simple_paths(TR, b, node)]
                longest_path[node] = max(paths) if paths else 0

            for node, rank in longest_path.items():
                TR.nodes[node]['layer'] = rank
            
            pos = nx.multipartite_layout(TR, subset_key="layer")
            
            # Rotate to vertical
            for node, (x, y) in pos.items():
                pos[node] = (y, x)
            
        except Exception:
            pos = nx.spring_layout(TR)

        plt.figure(figsize=(6, 8))
        plt.title(f"Hasse Diagram: {self.name}")
        nx.draw_networkx_nodes(TR, pos, node_size=700, node_color="#A0CBE2", edgecolors="black")
        nx.draw_networkx_labels(TR, pos, font_size=10, font_weight="bold")
        nx.draw_networkx_edges(TR, pos, arrows=False, width=1.5, edge_color="gray")
        plt.axis("off")
        plt.tight_layout()
        plt.show()

    def __repr__(self) -> str:
        return f"{self.name}"


class FilteredLattice(Lattice):
    """
    Represents a lattice equipped with a Filter (a subset of designated 'True' elements).
    """

    def __init__(
        self,
        name_filtered_lattice: str,
        name_lattice: str,
        elements: Set[str],
        relations: Set[Tuple[str, str]],
        negation_map: Optional[Dict[str, str]] = None,
        implication_map: Optional[Dict[Tuple[str, str], str]] = None,
        filter: Optional[Set[str]] = None
    ):
        """
        Initializes a Filtered Lattice.

        Args:
            name_filtered_lattice (str): Unique name.
            name_lattice (str): Name of the base lattice.
            elements (Set[str]): Elements of the lattice.
            relations (Set[Tuple[str, str]]): Ordering relations.
            negation_map (Optional[Dict[str, str]]): Negation mapping.
            implication_map (Optional[Dict[Tuple[str, str], str]]): Implication mapping.
            filter (Optional[Set[str]]): The subset of elements considered 'True'.

        Raises:
            ValueError: If the filter is not a valid subset of the elements.
        """
        super().__init__(name_lattice, elements, relations, negation_map, implication_map)
        self.name_filtered_lattice = name_filtered_lattice
        self.filter = filter if filter is not None else set()

        if not self._check_filter():
            raise ValueError("The Filter must be a subset of the Lattice elements.")

    def _check_filter(self) -> bool:
        """Checks if the filter is a valid subset of elements."""
        return self.filter.issubset(self.elements)

    def __repr__(self) -> str:
        return f"{self.name_filtered_lattice}"


class ManyLattice(FilteredLattice):
    """
    Represents a Filtered Lattice that serves as a base for a set of complete sublattices.
    Used for models involving multiple contexts.
    """

    def __init__(
        self,
        name_many_lattice: str,
        name_filtered_lattice: str,
        name_lattice: str,
        elements: Set[str],
        relations: Set[Tuple[str, str]],
        comp_sub_lat: List[Lattice],
        negation_map: Optional[Dict[str, str]] = None,
        implication_map: Optional[Dict[Tuple[str, str], str]] = None,
        filter: Optional[Set[str]] = None
    ):
        """
        Initializes a Many-Lattice.

        Args:
            name_many_lattice (str): Unique name.
            name_filtered_lattice (str): Name of the base filtered lattice.
            name_lattice (str): Name of the base lattice.
            elements (Set[str]): Elements of the base lattice.
            relations (Set[Tuple[str, str]]): Ordering relations.
            comp_sub_lat (List[Lattice]): A list of complete sublattices.
            negation_map (Optional[Dict[str, str]]): Negation mapping.
            implication_map (Optional[Dict[Tuple[str, str], str]]): Implication mapping.
            filter (Optional[Set[str]]): The filter set.

        Raises:
            TypeError: If items in comp_sub_lat are not Lattice objects.
        """
        super().__init__(
            name_filtered_lattice, name_lattice, elements, relations, 
            negation_map, implication_map, filter
        )
        
        for lat in comp_sub_lat:
            if not isinstance(lat, Lattice):
                raise TypeError("comp_sub_lat must contain Lattice instances.")

        self.comp_sub_lat = comp_sub_lat
        self.name_many_lattice = name_many_lattice

    def __repr__(self) -> str:
        return f"{self.name_many_lattice}"

    def add_comp_sub_lat(self, lattice: Lattice) -> None:
        """
        Adds a complete sublattice to the collection.

        Args:
            lattice (Lattice): The sublattice to add.

        Raises:
            TypeError: If argument is not a Lattice.
            ValueError: If a lattice with the same name already exists.
        """
        if not isinstance(lattice, Lattice):
            raise TypeError("Argument must be a Lattice instance.")
        
        if self.get_comp_sub_lattice(lattice.name):
            raise ValueError(f"Lattice '{lattice.name}' already exists.")
        
        self.comp_sub_lat.append(lattice)

    def get_comp_sub_lattice(self, name: str) -> Optional[Lattice]:
        """
        Retrieves a sublattice by name.

        Args:
            name (str): The name of the sublattice.

        Returns:
            Optional[Lattice]: The lattice object if found, else None.
        """
        for lattice in self.comp_sub_lat:
            if lattice.name == name:
                return lattice
        return None

    def down_interpretation(self, lattice: Lattice, element_a: str) -> str:
        """
        Computes the Down Interpretation (Floor) of element 'a' into the sublattice.
        Definition: Join of {x in Sublattice | x <= a}.

        Args:
            lattice (Lattice): The target sublattice.
            element_a (str): An element from the base lattice.

        Returns:
            str: The projected element in the sublattice.

        Raises:
            ValueError: If the lattice is not a registered sublattice.
        """
        if not isinstance(lattice, Lattice):
            raise TypeError("Argument 'lattice' must be a Lattice instance.")
        
        if lattice.name not in [lat.name for lat in self.comp_sub_lat]:
            raise ValueError("Lattice must be a registered complete sublattice.")

        if element_a in lattice.elements:
            return element_a

        lower_set = {x for x in lattice.elements if self.is_less_than_or_equal(x, element_a)}

        if not lower_set:
            return lattice.bottom
        return lattice.join_set(lower_set)

    def up_interpretation(self, lattice: Lattice, element_a: str) -> str:
        """
        Computes the Up Interpretation (Ceiling) of element 'a' into the sublattice.
        Definition: Meet of {x in Sublattice | a <= x}.

        Args:
            lattice (Lattice): The target sublattice.
            element_a (str): An element from the base lattice.

        Returns:
            str: The projected element in the sublattice.

        Raises:
            ValueError: If the lattice is not a registered sublattice.
        """
        if not isinstance(lattice, Lattice):
            raise TypeError("Argument 'lattice' must be a Lattice instance.")
        
        if lattice.name not in [lat.name for lat in self.comp_sub_lat]:
            raise ValueError("Lattice must be a registered complete sublattice.")

        if element_a in lattice.elements:
            return element_a

        upper_set = {x for x in lattice.elements if self.is_less_than_or_equal(element_a, x)}

        if not upper_set:
            return lattice.top
        return lattice.meet_set(upper_set)


class ResiduatedLattice(Lattice):
    """
    Represents a Residuated Lattice (Lattice with a Monoid Structure).
    """

    def __init__(
        self,
        name_residuated_lattice: str,
        name_lattice: str,
        elements: Set[str],
        relations: Set[Tuple[str, str]],
        operation: Optional[Dict[Tuple[str, str], str]] = None,
        neutral_elem: Optional[str] = None,
        negation_map: Optional[Dict[str, str]] = None,
        implication_map: Optional[Dict[Tuple[str, str], str]] = None
    ):
        """
        Initializes a Residuated Lattice.

        Args:
            name_residuated_lattice (str): Unique name.
            name_lattice (str): Name of the base lattice structure.
            elements (Set[str]): Elements set.
            relations (Set[Tuple[str, str]]): Ordering relations.
            operation (Optional[Dict]): Binary operation map (Monoid *).
            neutral_elem (Optional[str]): The identity element for the operation.
            negation_map (Optional[Dict]): Unary negation map.
            implication_map (Optional[Dict]): Binary implication map.
        """
        super().__init__(name_lattice, elements, relations, negation_map, implication_map)
        self.name_residuated_lattice = name_residuated_lattice
        self.operation = operation if operation is not None else {}
        self.neutral_elem = neutral_elem


class TwistStructure:
    """
    Represents a Twist Structure (Product Lattice L x L) constructed from a Residuated Lattice.
    Used for Paraconsistent logic (Truth and Information ordering).
    """

    def __init__(self, residuated_lattice: ResiduatedLattice):
        """
        Initializes the Twist Structure.

        Args:
            residuated_lattice (ResiduatedLattice): The base algebraic structure.
        
        Raises:
            TypeError: If argument is not a ResiduatedLattice.
        """
        if not isinstance(residuated_lattice, ResiduatedLattice):
            raise TypeError("Argument must be a ResiduatedLattice.")
        
        self.residuated_lattice = residuated_lattice
        self.elements = self._build_elements()
        self.truth_relation = self._build_truth_order()
        self.qntt_info_relation = self._build_quantity_info_order()

    def _build_elements(self) -> Set[Tuple[str, str]]:
        """
        Builds Cartesian Product elements (x, y).

        Returns:
            Set[Tuple[str, str]]: A set of all pairs (e1, e2) where e1, e2 are in the base lattice.
        """
        return {
            (e1, e2) 
            for e1 in self.residuated_lattice.elements 
            for e2 in self.residuated_lattice.elements
        }

    def _build_truth_order(self) -> Set[Tuple[Tuple[str, str], Tuple[str, str]]]:
        """
        Builds the Truth ordering relation (<=t).
        Definition: (t1, f1) <=t (t2, f2) iff t1 <= t2 AND f2 <= f1.

        Returns:
            Set[Tuple[Tuple[str, str], Tuple[str, str]]]: A set of pairs of elements representing the order.
        """
        relation = set()
        rl = self.residuated_lattice
        for p1 in self.elements:
            for p2 in self.elements:
                if rl.is_less_than_or_equal(p1[0], p2[0]) and rl.is_less_than_or_equal(p2[1], p1[1]):
                    relation.add((p1, p2))
        return relation

    def _build_quantity_info_order(self) -> Set[Tuple[Tuple[str, str], Tuple[str, str]]]:
        """
        Builds the Information ordering relation (<=k).
        Definition: (t1, f1) <=k (t2, f2) iff t1 <= t2 AND f1 <= f2.

        Returns:
            Set[Tuple[Tuple[str, str], Tuple[str, str]]]: A set of pairs of elements representing the order.
        """
        relation = set()
        rl = self.residuated_lattice
        for p1 in self.elements:
            for p2 in self.elements:
                if rl.is_less_than_or_equal(p1[0], p2[0]) and rl.is_less_than_or_equal(p1[1], p2[1]):
                    relation.add((p1, p2))
        return relation

    def is_lq_truth(self, pair1: Tuple[str, str], pair2: Tuple[str, str]) -> bool:
        """
        Checks if pair1 is less than or equal to pair2 in the Truth ordering.

        Args:
            pair1 (Tuple[str, str]): The first element.
            pair2 (Tuple[str, str]): The second element.

        Returns:
            bool: True if pair1 <=t pair2, False otherwise.
        """
        return (pair1, pair2) in self.truth_relation

    def is_lq_qntt_info(self, pair1: Tuple[str, str], pair2: Tuple[str, str]) -> bool:
        """
        Checks if pair1 is less than or equal to pair2 in the Information ordering.

        Args:
            pair1 (Tuple[str, str]): The first element.
            pair2 (Tuple[str, str]): The second element.

        Returns:
            bool: True if pair1 <=k pair2, False otherwise.
        """
        return (pair1, pair2) in self.qntt_info_relation

    def negation(self, pair: Tuple[str, str]) -> Tuple[str, str]:
        """
        Computes the Logical Negation of a pair.
        Definition: //(t, f) = (f, t).

        Args:
            pair (Tuple[str, str]): The element to negate.

        Returns:
            Tuple[str, str]: The negated element.
        """
        return (pair[1], pair[0])

    def weak_meet(self, pair1: Tuple[str, str], pair2: Tuple[str, str]) -> Tuple[str, str]:
        """
        Computes the Weak Meet (AND) in the Truth ordering.
        Definition: (t1, f1) ^ (t2, f2) = (t1 ^ t2, f1 v f2).

        Args:
            pair1 (Tuple[str, str]): The first operand.
            pair2 (Tuple[str, str]): The second operand.

        Returns:
            Tuple[str, str]: The result of the weak meet operation.
        """
        rl = self.residuated_lattice
        return (rl.meet(pair1[0], pair2[0]), rl.join(pair1[1], pair2[1]))

    def weak_join(self, pair1: Tuple[str, str], pair2: Tuple[str, str]) -> Tuple[str, str]:
        """
        Computes the Weak Join (OR) in the Truth ordering.
        Definition: (t1, f1) v (t2, f2) = (t1 v t2, f1 ^ f2).

        Args:
            pair1 (Tuple[str, str]): The first operand.
            pair2 (Tuple[str, str]): The second operand.

        Returns:
            Tuple[str, str]: The result of the weak join operation.
        """
        rl = self.residuated_lattice
        return (rl.join(pair1[0], pair2[0]), rl.meet(pair1[1], pair2[1]))

    def consensus(self, pair1: Tuple[str, str], pair2: Tuple[str, str]) -> Tuple[str, str]:
        """
        Computes the Consensus (Meet) in the Information ordering.

        Args:
            pair1 (Tuple[str, str]): The first operand.
            pair2 (Tuple[str, str]): The second operand.

        Returns:
            Tuple[str, str]: The consensus of the two pairs.

        Raises:
            ValueError: If the base lattice is missing required implication definitions.
        """
        rl = self.residuated_lattice
        
        meet_t = rl.meet(pair1[0], pair2[0])
        imp_t1_f2 = rl.implication(pair1[0], pair2[1])
        imp_t2_f1 = rl.implication(pair2[0], pair1[1])
        
        if imp_t1_f2 is None or imp_t2_f1 is None:
            raise ValueError("Base lattice missing implication definitions required for Consensus.")
            
        meet_imp = rl.meet(imp_t1_f2, imp_t2_f1)
        return (meet_t, meet_imp)

    def accept_all(self, pair1: Tuple[str, str], pair2: Tuple[str, str]) -> Tuple[str, str]:
        """
        Computes the Join in the Information ordering (Accept All).
        Definition: (t1, f1) + (t2, f2) = (t1 v t2, f1 v f2).

        Args:
            pair1 (Tuple[str, str]): The first operand.
            pair2 (Tuple[str, str]): The second operand.

        Returns:
            Tuple[str, str]: The result of the operation.
        """
        rl = self.residuated_lattice
        return (rl.join(pair1[0], pair2[0]), rl.join(pair1[1], pair2[1]))

    def implication(self, pair1: Tuple[str, str], pair2: Tuple[str, str]) -> Tuple[str, str]:
        """
        Computes logical implication in the Twist Structure.

        Args:
            pair1 (Tuple[str, str]): The antecedent pair.
            pair2 (Tuple[str, str]): The consequent pair.

        Returns:
            Tuple[str, str]: The result of the implication.

        Raises:
            ValueError: If the base lattice is missing required implication definitions.
        """
        rl = self.residuated_lattice
        t1, f1 = pair1
        t2, f2 = pair2
        
        imp_t1_t2 = rl.implication(t1, t2)
        imp_f2_f1 = rl.implication(f2, f1)
        
        if imp_t1_t2 is None or imp_f2_f1 is None:
            raise ValueError("Base lattice missing implication definitions.")

        meet_imp = rl.meet(imp_t1_t2, imp_f2_f1)
        meet_t1_f2 = rl.meet(t1, f2)
        
        return (meet_imp, meet_t1_f2)