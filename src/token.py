"""
src/token.py
Token and TokenType definitions for C-Lite.
Aligned with CO523 Week 3: Tokens and Lexemes.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any

class TokenType(Enum):
    """
    Enumeration of all valid token types in C-Lite.
    Matches Project Specification Section 3 & 4.1.
    """
    # Keywords
    INT = "int"
    FLOAT = "float"
    IF = "if"
    ELSE = "else"
    PRINTF = "printf"
    
    # Literals
    INT_LITERAL = "integer"
    FLOAT_LITERAL = "float"
    STRING_LITERAL = "string"
    
    # Identifiers
    IDENTIFIER = "identifier"
    
    # Operators
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"
    GT = ">"
    LT = "<"
    EQ = "=="     
    ASSIGN = "="
    
    # Delimiters
    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    SEMICOLON = ";"
    
    # Comments & Meta
    COMMENT = "comment"
    EOF = "eof"

@dataclass(frozen=True)
class Token:
    """
    Immutable token representation with source location.
    Frozen dataclass ensures tokens aren't modified after creation.
    """
    type: TokenType
    value: Any
    line: int
    column: int
    
    def __str__(self) -> str:
        return f"Token({self.type.value}, {self.value}, {self.line}:{self.column})"
    
    def __repr__(self) -> str:
        return self.__str__()