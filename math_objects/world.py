"""
World Module.

This module defines the World class, representing a single state in a modal logic model.
Each world is associated with a specific algebraic structure (Lattice) and holds
truth value assignments for propositional variables.
"""

from typing import Dict, Optional
from math_objects.lattice import Lattice

class World:
    """
    Represents a single world in a many-logic modal structure.

    Each world is assigned a specific lattice (defining the local truth values)
    and contains assignments mapping propositional variables to values within that lattice.
    """

    def __init__(
        self, 
        name_long: str, 
        name_short: str, 
        lattice: Lattice, 
        assignments: Optional[Dict[str, str]] = None
    ):
        """
        Initializes the World.

        Args:
            name_long (str): The unique identifier for the world.
            name_short (str): The short display name (e.g., for graphs).
            lattice (Lattice): The algebraic structure assigned to this world.
            assignments (Optional[Dict[str, str]]): Initial mapping of propositions to values.

        Raises:
            TypeError: If the provided lattice is not an instance of Lattice.
        """
        if not isinstance(lattice, Lattice):
            raise TypeError("The 'lattice' argument must be an instance of the Lattice class.")
            
        self.name_long = name_long
        self.name_short = name_short
        self.lattice = lattice
        self.assignments = assignments if assignments is not None else {}

    def get_assignment(self, variable: str) -> Optional[str]:
        """
        Retrieves the value of a propositional variable in this world.

        Args:
            variable (str): The propositional variable to look up.

        Returns:
            Optional[str]: The value of the variable, or None if not found.
        """
        return self.assignments.get(variable)

    def assign_value(self, variable: str, value: str) -> None:
        """
        Assigns a value from the world's lattice to a propositional variable.

        Args:
            variable (str): The propositional variable.
            value (str): The truth value (must exist in the lattice).

        Raises:
            ValueError: If the value is not an element of the assigned lattice.
        """
        if value not in self.lattice.elements:
            raise ValueError(
                f"Value '{value}' is not in the lattice assigned to world '{self.name_long}'."
            )
        self.assignments[variable] = value

    def __repr__(self) -> str:
        """Returns the short name representation of the world."""
        return f"{self.name_short}"