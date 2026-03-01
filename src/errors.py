"""
Custom exception hierarchy for C-Lite interpreter errors.
"""

class CLiteError(Exception):
    """Base exception for all C-Lite interpreter errors."""
    pass

class LexerError(CLiteError):
    """
    Raised when the lexical analyzer encounters invalid input.
    Includes source location for precise error reporting.
    """
    def __init__(self, message: str, line: int, column: int):
        self.line = line
        self.column = column
        super().__init__(f"LexerError at line {line}, column {column}: {message}")

class ParserError(CLiteError):
    """
    Raised when the parser encounters invalid syntax.
    Includes source location for precise error reporting.
    """
    def __init__(self, message: str, line: int, column: int):
        self.line = line
        self.column = column
        super().__init__(f"ParserError at line {line}, column {column}: {message}")

class SemanticError(CLiteError):
    """
    Raised when semantic analysis fails.
    Includes source location for precise error reporting.
    """
    def __init__(self, message: str, line: int, column: int):
        self.line = line
        self.column = column
        super().__init__(f"SemanticError at line {line}, column {column}: {message}")