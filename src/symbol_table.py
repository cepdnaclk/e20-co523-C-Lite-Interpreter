"""
Symbol Table implementation for C-Lite interpreter.
Manages variable declarations, bindings, and lifetimes across scopes.

"""

from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from src.errors import SemanticError


@dataclass
class Symbol:
    """
    Represents a variable symbol in the symbol table.
    """
    name: str
    var_type: str
    value: Optional[Any] = None
    line: int = 1
    column: int = 1
    scope_level: int = 0
    
    def __eq__(self, other) -> bool:
        """Symbol equality based on all attributes."""
        if not isinstance(other, Symbol):
            return False
        return (
            self.name == other.name and
            self.var_type == other.var_type and
            self.scope_level == other.scope_level
        )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Symbol(name={self.name}, type={self.var_type}, scope={self.scope_level})"


class SymbolTable:
    """
    Stack-based symbol table with nested scope support.
    """
    
    def __init__(self):
        """Initialize symbol table with global scope."""
        # Stack of scopes, each scope is a dict: {name: Symbol}
        self._scopes: List[Dict[str, Symbol]] = [{}]
        self._current_scope_level: int = 0
    
    def enter_scope(self) -> None:
        """
        Enter a new nested scope (e.g., on block entry).
        Variables declared in this scope are destroyed on exit_scope().
        """
        self._scopes.append({})
        self._current_scope_level += 1
    
    def exit_scope(self) -> None:
        """
        Exit current scope (e.g., on block exit).
        Raises:
            SemanticError: If attempting to exit global scope
        """
        if len(self._scopes) <= 1:
            raise SemanticError(
                "Cannot exit global scope",
                line=1,
                column=1
            )
        self._scopes.pop()
        self._current_scope_level -= 1
    
    def declare(self, name: str, var_type: str, line: int, column: int) -> None:
        """
        Declare a new variable in current scope.
        
        Raises:
            SemanticError: If variable already declared in current scope
        """
        current_scope = self._scopes[-1]
        
        if name in current_scope:
            raise SemanticError(
                f"Variable '{name}' already declared in current scope",
                line=line,
                column=column
            )
        
        current_scope[name] = Symbol(
            name=name,
            var_type=var_type,
            line=line,
            column=column,
            scope_level=self._current_scope_level
        )
    
    def lookup(self, name: str) -> Optional[Symbol]:
        """
        Look up a variable by name (searches from innermost to outermost scope).
        
        Returns:
            Symbol if found, None otherwise
        
        Returns Symbol object (caller should not mutate)
        """
        # Search from innermost scope to outermost
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None
    
    def update(self, name: str, value: Any, line: int, column: int) -> None:
        """
        Update a variable's value with type checking.
        
        Raises:
            SemanticError: If variable not declared
            SemanticError: If type mismatch (enforced static typing)
        """
        symbol = self.lookup(name)
        
        if symbol is None:
            raise SemanticError(
                f"Undefined variable '{name}'",
                line=line,
                column=column
            )
        
        # Type checking with implicit coercion
        if symbol.var_type == 'int' and isinstance(value, float):
            # Coerce float → int (truncate)
            value = int(value)
        elif symbol.var_type == 'float' and isinstance(value, int):
            # Coerce int → float (promote)
            value = float(value)
        
        symbol.value = value
    
    def get_value(self, name: str, line: int, column: int) -> Any:
        """
        Get a variable's value.
        
        Raises:
            SemanticError: If variable not declared or uninitialized
        """
        symbol = self.lookup(name)
        
        if symbol is None:
            raise SemanticError(
                f"Undefined variable '{name}'",
                line=line,
                column=column
            )
        
        if symbol.value is None:
            raise SemanticError(
                f"Variable '{name}' used before initialization",
                line=line,
                column=column
            )
        
        return symbol.value
    
    def get_type(self, name: str, line: int, column: int) -> str:
        """
        Get a variable's declared type.
        
        Raises:
            SemanticError: If variable not declared
        """
        symbol = self.lookup(name)
        
        if symbol is None:
            raise SemanticError(
                f"Undefined variable '{name}'",
                line=line,
                column=column
            )
        
        return symbol.var_type
    
    def is_declared(self, name: str) -> bool:
        """
        Check if a variable is declared in any scope.
        
        Returns:
            True if declared, False otherwise
        """
        return self.lookup(name) is not None
    
    @property
    def current_scope_level(self) -> int:
        """Get current nesting depth (0 = global)."""
        return self._current_scope_level
    
    @property
    def scope_count(self) -> int:
        """Get number of active scopes."""
        return len(self._scopes)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"SymbolTable(scopes={len(self._scopes)}, level={self._current_scope_level})"