"""
C-Lite Interpreter - Executes AST by traversing nodes and evaluating expressions.
Implements semantic evaluation with type checking and scope management.
"""

from typing import Any, Optional, List
from src.ast import (
    ASTNode, ASTVisitor,
    Program, Declaration, Assignment, IfStatement, Block, PrintfCall, EmptyStatement,
    BinaryOp, UnaryOp, NumberLiteral, Identifier
)
from src.symbol_table import SymbolTable
from src.errors import SemanticError


class Interpreter(ASTVisitor):
    """
    AST Visitor that executes C-Lite programs.
    
    Execution Model:
    - Declarations: Add variable to symbol table
    - Assignments: Evaluate expression, update symbol table
    - Expressions: Recursively evaluate operands, apply operator
    - Control Flow: Conditional execution based on expression values
    """
    
    def __init__(self):
        """
        Initialize interpreter with fresh symbol table.

        """
        self.symbol_table = SymbolTable()
        self.output: List[Any] = []  # Collect printf() output for testing
        self._execution_started = False
        self._execution_completed = False
    
    def reset(self) -> None:
        """
        Reset interpreter state for reuse.
        """
        self.symbol_table = SymbolTable()
        self.output = []
        self._execution_started = False
        self._execution_completed = False
    
    def execute(self, program: Program) -> List[Any]:
        """
        Execute a C-Lite program.
        
        Args:
            program: Program AST node (root)
        
        Returns:
            List of printf() output values
        """
        self._execution_started = True
        
        try:
            program.accept(self)
            self._execution_completed = True
        except SemanticError:
            # GAP 6: State may be partially modified on error
            # Caller should create new interpreter for next execution
            raise
        
        return self.output
    
    # ==================== Visitor Methods ====================
    
    def visit_program(self, node: Program) -> None:
        """
        Execute program: process declarations then statements.
        """
        # Process all declarations first
        for decl in node.declarations:
            decl.accept(self)
        
        # Process all statements in order (GAP 9, 10)
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_declaration(self, node: Declaration) -> None:
        """
        Execute declaration: add variable to symbol table.
        """
        self.symbol_table.declare(
            name=node.name,
            var_type=node.var_type,
            line=node.line,
            column=node.column
        )
        # Note: Value is None until assigned (GAP 5)
    
    def visit_assignment(self, node: Assignment) -> None:
        """
        Execute assignment: evaluate expression, update variable.
        """
        # Evaluate right-hand side expression
        value = node.value.accept(self)
        
        # Get declared type
        var_type = self.symbol_table.get_type(
            node.name,
            line=node.line,
            column=node.column
        )
        
        # GAP 4: Type coercion (C-style)
        if var_type == 'int' and isinstance(value, float):
            # float → int (truncate)
            value = int(value)
        elif var_type == 'float' and isinstance(value, int):
            # int → float (promote)
            value = float(value)
        
        # Update symbol table
        self.symbol_table.update(
            node.name,
            value,
            line=node.line,
            column=node.column
        )
    
    def visit_if_statement(self, node: IfStatement) -> None:
        """
        Execute if-else: evaluate condition, execute appropriate branch.
        """
        # Evaluate condition
        condition_value = node.condition.accept(self)
        
        # GAP 1: Convert to boolean (C-style truthiness)
        is_true = self._to_boolean(condition_value)
        
        # Execute appropriate branch
        if is_true:
            node.then_branch.accept(self)
        elif node.else_branch is not None:
            node.else_branch.accept(self)
    
    def _to_boolean(self, value: Any) -> bool:
        """
        Convert value to boolean using C-style truthiness.
        """
        if isinstance(value, int):
            return value != 0
        elif isinstance(value, float):
            return value != 0.0
        else:
            return bool(value)
    
    def visit_block(self, node: Block) -> None:
        """
        Execute block: enter scope, execute statements, exit scope.
        """
        # Enter new scope
        self.symbol_table.enter_scope()
        
        try:
            # Execute all statements in block
            for stmt in node.statements:
                stmt.accept(self)
        finally:
            # GAP 6: Always exit scope even on exception
            self.symbol_table.exit_scope()
    
    def visit_printf_call(self, node: PrintfCall) -> None:
        """
        Execute printf(): evaluate argument, output value.
        """
        # Evaluate argument
        value = node.argument.accept(self)
        
        # Format output (int without decimal, float with decimal)
        if isinstance(value, int):
            output_value = value
        elif isinstance(value, float):
            # Remove trailing zeros for clean output
            if value.is_integer():
                output_value = int(value)
            else:
                output_value = value
        else:
            output_value = value

        self.output.append(output_value)
        
    def visit_empty_statement(self, node: EmptyStatement) -> None:
        """
        Execute empty statement: no-op.
        """
        pass
    
    def visit_binary_op(self, node: BinaryOp) -> Any:
        """
        Evaluate binary operation: evaluate operands, apply operator.
        """
        # Evaluate operands
        left_value = node.left.accept(self)
        right_value = node.right.accept(self)
        
        # Apply operator
        if node.operator == '+':
            return self._coerce_and_apply(left_value, right_value, lambda a, b: a + b)
        elif node.operator == '-':
            return self._coerce_and_apply(left_value, right_value, lambda a, b: a - b)
        elif node.operator == '*':
            return self._coerce_and_apply(left_value, right_value, lambda a, b: a * b)
        elif node.operator == '/':
            # GAP 13: Division with type checking
            # Check for division by zero
            if right_value == 0 or (isinstance(right_value, float) and abs(right_value) < 1e-10):
                raise SemanticError(
                    "Division by zero",
                    line=node.line,
                    column=node.column
                )
            
            # C-style division: int/int = int, float division otherwise
            if isinstance(left_value, int) and isinstance(right_value, int):
                return left_value // right_value  # Integer division
            return left_value / right_value  # Float division
        
        # GAP 2: Relational operators return 1 or 0 (int)
        elif node.operator == '>':
            return 1 if left_value > right_value else 0
        elif node.operator == '<':
            return 1 if left_value < right_value else 0
        elif node.operator == '==':
            # GAP 3: Mixed-type equality with coercion
            return 1 if left_value == right_value else 0
        else:
            raise SemanticError(
                f"Unknown operator '{node.operator}'",
                line=node.line,
                column=node.column
            )
    
    def _coerce_and_apply(self, left: Any, right: Any, op) -> Any:
        """
        Apply operator with type coercion.
        """
        if isinstance(left, float) or isinstance(right, float):
            # Promote to float
            left_float = float(left) if isinstance(left, int) else left
            right_float = float(right) if isinstance(right, int) else right
            return op(left_float, right_float)
        else:
            # Both int
            return op(left, right)
    
    def visit_unary_op(self, node: UnaryOp) -> Any:
        """
        Evaluate unary operation: evaluate operand, apply operator.
        """
        # Evaluate operand
        operand_value = node.operand.accept(self)
        
        # GAP 11: Apply operator
        if node.operator == '+':
            return +operand_value
        elif node.operator == '-':
            return -operand_value
        else:
            raise SemanticError(
                f"Unknown unary operator '{node.operator}'",
                line=node.line,
                column=node.column
            )
    
    def visit_number_literal(self, node: NumberLiteral) -> Any:
        """
        Evaluate number literal: return value directly.
        """
        return node.value
    
    def visit_identifier(self, node: Identifier) -> Any:
        """
        Evaluate identifier: look up variable value in symbol table.
        """
        return self.symbol_table.get_value(
            node.name,
            line=node.line,
            column=node.column
        )