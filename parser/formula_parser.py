"""
Formula Parser Module.

This module handles the tokenization, parsing, and evaluation of logical formulas
in a MLML context. It supports standard operators (~, &, |, ->, <->)
and modal operators ([], <>), with dynamic evaluation based on up/down interpretations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Set, Any, Tuple


# ==========================================
#                 LEXER
# ==========================================

class Lexer:
    """
    Tokenizer for the logic formula string.
    Converts raw text into a stream of tokens (e.g., 'ATOM', 'BOX', 'AND').
    """

    def __init__(self, text: str):
        """
        Initializes the Lexer.

        Args:
            text (str): The raw formula string to tokenize.
        """
        self.text = text
        self.pos = 0
        self.current_char: Optional[str] = self.text[0] if self.text else None

    def advance(self) -> None:
        """Moves the pointer to the next character in the text."""
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def skip_whitespace(self) -> None:
        """Skips over any whitespace characters."""
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def get_atom(self) -> Tuple[str, str]:
        """
        Reads an alphanumeric identifier (proposition).

        Returns:
            Tuple[str, str]: A token tuple ('ATOM', value).
        """
        result = ''
        while self.current_char is not None and self.current_char.isalnum():
            result += self.current_char
            self.advance()
        return ('ATOM', result)

    def get_next_token(self) -> Tuple[str, Optional[str]]:
        """
        Scans the input and returns the next valid token.

        Returns:
            Tuple[str, Optional[str]]: A tuple (TYPE, VALUE).
        
        Raises:
            ValueError: If an unknown or unexpected character is encountered.
        """
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            if self.current_char.isalnum():
                return self.get_atom()
            
            if self.current_char == '~':
                self.advance()
                return ('NOT', '~')
            
            if self.current_char == '[':
                self.advance()
                if self.current_char == ']':
                    self.advance()
                    return ('BOX', '[]')
                raise ValueError("Expected ']' after '['")
            
            if self.current_char == '<':
                self.advance()
                if self.current_char == '>':
                    self.advance()
                    return ('DIAMOND', '<>')
                if self.current_char == '-':
                    self.advance()
                    if self.current_char == '>':
                        self.advance()
                        return ('IFF', '<->')
                    raise ValueError("Expected '>' after '<-'")
                raise ValueError("Expected '>' or '-' after '<'")
            
            if self.current_char == '-':
                self.advance()
                if self.current_char == '>':
                    self.advance()
                    return ('IMPLIES', '->')
                raise ValueError("Expected '>' after '-'")
            
            if self.current_char == '&':
                self.advance()
                return ('AND', '&')
            
            if self.current_char == '|':
                self.advance()
                return ('OR', '|')
            
            if self.current_char == '(':
                self.advance()
                return ('LPAREN', '(')
            
            if self.current_char == ')':
                self.advance()
                return ('RPAREN', ')')
            
            raise ValueError(f"Unknown character: {self.current_char}")
        
        return ('EOF', None)


# ==========================================
#              AST NODES
# ==========================================

class ASTNode(ABC):
    """Abstract Base Class for Abstract Syntax Tree nodes."""

    @abstractmethod
    def evaluate(self, model: Any, world: Any, interpretation: str = "down") -> str:
        """
        Evaluates the formula in the given model at the given world.

        Args:
            model (Model): The model context containing the ManyLattice and structure.
            world (World): The specific world to evaluate in.
            interpretation (str, optional): Logic mode ("up" or "down"). Defaults to "down".

        Returns:
            str: The resulting truth value (element of the world's lattice).
        """
        pass

    @abstractmethod
    def get_atoms(self) -> Set[str]:
        """
        Retrieves all atomic propositions used in this formula.

        Returns:
            Set[str]: A set of proposition names (e.g., {'p', 'q'}).
        """
        pass


class Atom(ASTNode):
    """Represents an atomic proposition (e.g., 'p')."""

    def __init__(self, name: str):
        self.name = name

    def get_atoms(self) -> Set[str]:
        return {self.name}

    def evaluate(self, model: Any, world: Any, interpretation: str = "down") -> str:
        """
        Evaluates the atom by looking up its assignment in the world.

        Raises:
            ValueError: If the proposition is not defined in the world assignments.
        """
        if self.name in world.assignments:
            return world.assignments[self.name]
        
        raise ValueError(f"Proposition '{self.name}' is not defined in world '{world.name_long}'.")


class Not(ASTNode):
    """Represents logical negation (~A)."""

    def __init__(self, child: ASTNode):
        self.child = child

    def get_atoms(self) -> Set[str]:
        return self.child.get_atoms()

    def evaluate(self, model: Any, world: Any, interpretation: str = "down") -> str:
        """
        Evaluates Negation using the Base Lattice map and dynamic interpretation.

        Raises:
            ValueError: If negation is not defined for the value in the Base Lattice.
        """
        val = self.child.evaluate(model, world, interpretation)
        
        # Retrieve raw negation from Base Lattice to allow dynamic interpretation switch
        base_neg_map = model.many_lattice.negation_map
        
        if val in base_neg_map:
            negated_base = base_neg_map[val]
        else:
            raise ValueError(f"Negation not defined for '{val}' in the Base Lattice.")

        if interpretation == "up":
            return model.many_lattice.up_interpretation(world.lattice, negated_base)
        else:
            return model.many_lattice.down_interpretation(world.lattice, negated_base)


class And(ASTNode):
    """Represents logical conjunction (A & B)."""

    def __init__(self, left: ASTNode, right: ASTNode):
        self.left = left
        self.right = right

    def get_atoms(self) -> Set[str]:
        return self.left.get_atoms().union(self.right.get_atoms())

    def evaluate(self, model: Any, world: Any, interpretation: str = "down") -> str:
        val_a = self.left.evaluate(model, world, interpretation)
        val_b = self.right.evaluate(model, world, interpretation)
        return world.lattice.meet(val_a, val_b)


class Or(ASTNode):
    """Represents logical disjunction (A | B)."""

    def __init__(self, left: ASTNode, right: ASTNode):
        self.left = left
        self.right = right

    def get_atoms(self) -> Set[str]:
        return self.left.get_atoms().union(self.right.get_atoms())

    def evaluate(self, model: Any, world: Any, interpretation: str = "down") -> str:
        val_a = self.left.evaluate(model, world, interpretation)
        val_b = self.right.evaluate(model, world, interpretation)
        return world.lattice.join(val_a, val_b)


class Implies(ASTNode):
    """Represents logical implication (A -> B)."""

    def __init__(self, left: ASTNode, right: ASTNode):
        self.left = left
        self.right = right

    def get_atoms(self) -> Set[str]:
        return self.left.get_atoms().union(self.right.get_atoms())

    def evaluate(self, model: Any, world: Any, interpretation: str = "down") -> str:
        """
        Evaluates Implication.
        Strategy:
        1. Look up (a, b) in Base Lattice Implication Map.
        2. If not found, fall back to Material Implication (~A | B).
        """
        val_a = self.left.evaluate(model, world, interpretation)
        val_b = self.right.evaluate(model, world, interpretation)

        # Look up in BASE Lattice map only
        base_imp_map = model.many_lattice.implication_map
        
        if (val_a, val_b) in base_imp_map:
            base_result = base_imp_map[(val_a, val_b)]
            
            if interpretation == "up":
                return model.many_lattice.up_interpretation(world.lattice, base_result)
            else:
                return model.many_lattice.down_interpretation(world.lattice, base_result)
        
        # Fallback: Material Implication (~A | B) using BASE negation map
        base_neg_map = model.many_lattice.negation_map
        if val_a in base_neg_map:
            neg_a_base = base_neg_map[val_a]
        else:
            raise ValueError(f"Negation not defined for '{val_a}' (required for implication fallback).")
        
        if interpretation == "up":
            val_not_a = model.many_lattice.up_interpretation(world.lattice, neg_a_base)
        else:
            val_not_a = model.many_lattice.down_interpretation(world.lattice, neg_a_base)

        return world.lattice.join(val_not_a, val_b)


class Iff(ASTNode):
    """Represents logical equivalence (A <-> B)."""

    def __init__(self, left: ASTNode, right: ASTNode):
        self.left = left
        self.right = right

    def get_atoms(self) -> Set[str]:
        return self.left.get_atoms().union(self.right.get_atoms())

    def evaluate(self, model: Any, world: Any, interpretation: str = "down") -> str:
        # Defined as (A -> B) & (B -> A)
        imp1 = Implies(self.left, self.right)
        imp2 = Implies(self.right, self.left)
        and_node = And(imp1, imp2)
        return and_node.evaluate(model, world, interpretation)


class Box(ASTNode):
    """Represents the Modal Box operator ([]A)."""

    def __init__(self, child: ASTNode):
        self.child = child

    def get_atoms(self) -> Set[str]:
        return self.child.get_atoms()

    def evaluate(self, model: Any, world: Any, interpretation: str = "down") -> str:
        """
        Evaluates Box A: Meet of interpreted values of A in all accessible worlds.
        """
        accessible_worlds = model.accessibility_relation.get(world, set())
        
        if not accessible_worlds:
            return world.lattice.top # Return Top (Vacuously True)

        relativized_values = set()
        for u in accessible_worlds:
            raw_val = self.child.evaluate(model, u, interpretation)
            
            if interpretation == "up":
                interp_val = model.many_lattice.up_interpretation(world.lattice, raw_val)
            else:
                interp_val = model.many_lattice.down_interpretation(world.lattice, raw_val)
                
            relativized_values.add(interp_val)

        return world.lattice.meet_set(relativized_values)


class Diamond(ASTNode):
    """Represents the Modal Diamond operator (<>A)."""

    def __init__(self, child: ASTNode):
        self.child = child

    def get_atoms(self) -> Set[str]:
        return self.child.get_atoms()

    def evaluate(self, model: Any, world: Any, interpretation: str = "down") -> str:
        """
        Evaluates Diamond A: ~[]~A.
        """
        not_child = Not(self.child)
        box_node = Box(not_child)
        final_node = Not(box_node)
        return final_node.evaluate(model, world, interpretation)


# ==========================================
#                 PARSER
# ==========================================

class FormulaParser:
    """
    Recursive Descent Parser for logic formulas.
    Constructs an AST (Abstract Syntax Tree) from a string.
    """

    def __init__(self, text: str):
        """
        Initializes the Parser with the formula text.

        Args:
            text (str): The logic formula string.
        """
        self.lexer = Lexer(text)
        self.current_token = self.lexer.get_next_token()

    def eat(self, token_type: str) -> None:
        """
        Consumes the current token if it matches the expected type.

        Args:
            token_type (str): The expected token type.

        Raises:
            ValueError: If the current token does not match the expected type.
        """
        if self.current_token[0] == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            raise ValueError(f"Expected {token_type}, got {self.current_token[0]}")

    def parse(self) -> ASTNode:
        """
        Parses the entire formula.

        Returns:
            ASTNode: The root node of the abstract syntax tree.

        Raises:
            ValueError: If there are remaining characters after parsing.
        """
        result = self.iff()
        if self.current_token[0] != 'EOF':
            raise ValueError("Unexpected characters at end of formula")
        return result

    def iff(self) -> ASTNode:
        """Parses IFF (Equivalence) expressions."""
        node = self.implies()
        while self.current_token[0] == 'IFF':
            self.eat('IFF')
            node = Iff(node, self.implies())
        return node

    def implies(self) -> ASTNode:
        """Parses IMPLIES expressions."""
        node = self.or_expr()
        while self.current_token[0] == 'IMPLIES':
            self.eat('IMPLIES')
            node = Implies(node, self.or_expr())
        return node

    def or_expr(self) -> ASTNode:
        """Parses OR expressions."""
        node = self.and_expr()
        while self.current_token[0] == 'OR':
            self.eat('OR')
            node = Or(node, self.and_expr())
        return node

    def and_expr(self) -> ASTNode:
        """Parses AND expressions."""
        node = self.unary()
        while self.current_token[0] == 'AND':
            self.eat('AND')
            node = And(node, self.unary())
        return node

    def unary(self) -> ASTNode:
        """Parses Unary operators (NOT, BOX, DIAMOND) and ATOMS/PARENS."""
        token_type = self.current_token[0]
        if token_type == 'NOT':
            self.eat('NOT')
            return Not(self.unary())
        elif token_type == 'BOX':
            self.eat('BOX')
            return Box(self.unary())
        elif token_type == 'DIAMOND':
            self.eat('DIAMOND')
            return Diamond(self.unary())
        elif token_type == 'LPAREN':
            self.eat('LPAREN')
            node = self.iff()
            self.eat('RPAREN')
            return node
        elif token_type == 'ATOM':
            name = self.current_token[1]
            self.eat('ATOM')
            return Atom(name)
        else:
            raise ValueError("Unexpected syntax in formula")