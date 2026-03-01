"""
Public API for the C-Lite interpreter.
"""

from .lexer import Lexer
from .token import Token, TokenType
from .errors import LexerError, ParserError, SemanticError
from .ast import (
    ASTNode, ASTVisitor,
    Program, Declaration, Assignment, IfStatement, Block, PrintfCall, EmptyStatement,
    BinaryOp, UnaryOp, NumberLiteral, Identifier
)
from .parser import Parser
from .symbol_table import SymbolTable, Symbol
from .interpreter import Interpreter

__all__ = [
    # Lexical Analysis
    'Lexer', 'Token', 'TokenType', 'LexerError',
    
    # Syntax Analysis
    'Parser', 'ParserError',
    'ASTNode', 'ASTVisitor',
    'Program', 'Declaration', 'Assignment', 'IfStatement', 
    'Block', 'PrintfCall', 'EmptyStatement',
    'BinaryOp', 'UnaryOp', 'NumberLiteral', 'Identifier',
    
    # Semantic Evaluation
    'SymbolTable', 'Symbol', 'SemanticError', 'Interpreter'
]