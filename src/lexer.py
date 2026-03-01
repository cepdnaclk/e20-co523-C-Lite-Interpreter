"""
Lexical Analyzer for C-Lite.
Implements DFA-based token recognition with source location tracking.
"""

from typing import Generator, Optional, Any
from .token import Token, TokenType
from .errors import LexerError

class Lexer:
    """
    Lexical Analyzer (Scanner) for C-Lite.
    Converts raw source code into a stream of Token objects.
    """
    
    def __init__(self, code: str):
        self.code = code
        self.length = len(code)
        self.position = 0
        
        # Source location tracking (1-indexed for error reporting)
        self.line = 1
        self.column = 1
        
        # Initialize current_char safely
        if self.length > 0:
            self.current_char: Optional[str] = self.code[0]
        else:
            self.current_char: Optional[str] = None

    def advance(self) -> None:
        """
        Move to the next character in the source code.
        """
        if self.current_char is None:
            return
            
        if self.current_char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
            
        self.position += 1
        
        if self.position < self.length:
            self.current_char = self.code[self.position]
        else:
            self.current_char = None

    def peek(self) -> Optional[str]:
        """Look at the next character without advancing."""
        next_pos = self.position + 1
        if next_pos < self.length:
            return self.code[next_pos]
        return None

    def match(self, expected: str) -> bool:
        """Check if next character matches expected, and advance if so."""
        if self.current_char is None:
            return False
            
        if self.current_char != expected:
            return False
            
        self.advance()
        return True

    def tokenize(self) -> Generator[Token, None, None]:
        """Main generator loop. Yields tokens one by one."""
        max_iterations = self.length * 2 + 100
        iteration_count = 0
        
        while self.current_char is not None:
            iteration_count += 1
            if iteration_count > max_iterations:
                raise LexerError(
                    f"Lexer infinite loop detected at line {self.line}, column {self.column}",
                    self.line,
                    self.column
                )
            
            # Skip whitespace
            if self.current_char in ' \t\n\r':
                self.advance()
                continue
            
            # Record start location BEFORE consuming token
            start_line = self.line
            start_column = self.column
            
            # Dispatch based on current character
            if self.current_char.isalpha() or self.current_char == '_':
                yield self._scan_identifier(start_line, start_column)
            elif self.current_char.isdigit() or self.current_char == '.':
                # Handle both digit and leading dot for floats
                yield self._scan_number(start_line, start_column)
            elif self.current_char == '"':
                yield self._scan_string(start_line, start_column)
            elif self.current_char == '/':
                if self.peek() == '/':
                    yield self._scan_comment(start_line, start_column)
                else:
                    self.advance()
                    yield self._make_token(TokenType.SLASH, '/', start_line, start_column)
            elif self.current_char == '=':
                if self.peek() == '=':
                    self.advance()
                    self.advance()
                    yield self._make_token(TokenType.EQ, '==', start_line, start_column)
                else:
                    self.advance()
                    yield self._make_token(TokenType.ASSIGN, '=', start_line, start_column)
            elif self.current_char == '+':
                self.advance()
                yield self._make_token(TokenType.PLUS, '+', start_line, start_column)
            elif self.current_char == '-':
                self.advance()
                yield self._make_token(TokenType.MINUS, '-', start_line, start_column)
            elif self.current_char == '*':
                self.advance()
                yield self._make_token(TokenType.STAR, '*', start_line, start_column)
            elif self.current_char == '>':
                self.advance()
                yield self._make_token(TokenType.GT, '>', start_line, start_column)
            elif self.current_char == '<':
                self.advance()
                yield self._make_token(TokenType.LT, '<', start_line, start_column)
            elif self.current_char == '(':
                self.advance()
                yield self._make_token(TokenType.LPAREN, '(', start_line, start_column)
            elif self.current_char == ')':
                self.advance()
                yield self._make_token(TokenType.RPAREN, ')', start_line, start_column)
            elif self.current_char == '{':
                self.advance()
                yield self._make_token(TokenType.LBRACE, '{', start_line, start_column)
            elif self.current_char == '}':
                self.advance()
                yield self._make_token(TokenType.RBRACE, '}', start_line, start_column)
            elif self.current_char == ';':
                self.advance()
                yield self._make_token(TokenType.SEMICOLON, ';', start_line, start_column)
            else:
                raise LexerError(
                    f"Unexpected character '{self.current_char}'",
                    start_line,
                    start_column
                )
        
        # Emit explicit EOF token
        yield self._make_token(TokenType.EOF, None, self.line, self.column)

    def tokenize_one(self) -> Token:
        """Helper for testing: returns the first token only."""
        return next(self.tokenize())

    def _make_token(self, type: TokenType, value: Any, line: int, column: int) -> Token:
        """Factory method for creating tokens."""
        return Token(type=type, value=value, line=line, column=column)

    def _scan_identifier(self, line: int, column: int) -> Token:
        """Scan identifiers and keywords."""
        start_pos = self.position
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            self.advance()
        
        lexeme = self.code[start_pos:self.position]
        
        keywords = {
            'int': TokenType.INT,
            'float': TokenType.FLOAT,
            'if': TokenType.IF,
            'else': TokenType.ELSE,
            'printf': TokenType.PRINTF
        }
        
        token_type = keywords.get(lexeme, TokenType.IDENTIFIER)
        return self._make_token(token_type, lexeme, line, column)

    def _scan_number(self, line: int, column: int) -> Token:
        """
        Scan integer and float literals.
        Handles: 3, 3.14, .7, 3.
        Rejects: ., .., 1.2.3, .1.2
        """
        start_pos = self.position
        has_dot = False
        has_digit = False
        
        # Consume all potential number characters
        while self.current_char is not None:
            if self.current_char.isdigit():
                has_digit = True
                self.advance()
            elif self.current_char == '.':
                if has_dot:
                    # Multiple dots detected
                    # Consume this dot to include it in the error message
                    self.advance()
                    lexeme = self.code[start_pos:self.position]
                    raise LexerError(f"Invalid number format '{lexeme}' (multiple decimal points)", line, column)
                else:
                    # First dot encountered
                    next_char = self.peek()
                    
                    # Valid cases: 3. or .7 or 3.14
                    # Invalid case: . followed by non-digit (standalone dot)
                    if has_digit or (next_char is not None and next_char.isdigit()):
                        has_dot = True
                        self.advance()
                    else:
                        # Standalone dot with no digits before or after
                        # Consume the dot to include it in error
                        self.advance()
                        lexeme = self.code[start_pos:self.position]
                        raise LexerError(f"Invalid number format '{lexeme}' (no digits)", line, column)
            else:
                # End of number (whitespace, operator, etc.)
                break
        
        # Validate collected lexeme
        lexeme = self.code[start_pos:self.position]
        
        # Must have at least one digit
        if not has_digit:
            raise LexerError(f"Invalid number format '{lexeme}' (no digits)", line, column)
        
        # No multiple dots
        if lexeme.count('.') > 1:
            raise LexerError(f"Invalid number format '{lexeme}' (multiple decimal points)", line, column)
        
        # Create appropriate token
        if has_dot:
            try:
                value = float(lexeme)
                return self._make_token(TokenType.FLOAT_LITERAL, value, line, column)
            except ValueError:
                raise LexerError(f"Invalid float literal '{lexeme}'", line, column)
        else:
            try:
                value = int(lexeme)
                return self._make_token(TokenType.INT_LITERAL, value, line, column)
            except ValueError:
                raise LexerError(f"Invalid integer literal '{lexeme}'", line, column)

    def _scan_string(self, line: int, column: int) -> Token:
        """Scan string literals with escape sequence support."""
        self.advance()  # Consume opening quote
        start_pos = self.position
        chars = []
        
        while self.current_char is not None and self.current_char != '"':
            if self.current_char == '\n':
                raise LexerError("Unclosed string literal (newline found)", line, column)
            
            if self.current_char == '\\':
                self.advance()
                if self.current_char is None:
                    raise LexerError("Unclosed string literal (escape at EOF)", line, column)
                
                escape_map = {'n': '\n', 't': '\t', '"': '"', '\\': '\\'}
                chars.append(escape_map.get(self.current_char, self.current_char))
            else:
                chars.append(self.current_char)
            
            self.advance()
        
        if self.current_char is None:
            raise LexerError("Unclosed string literal", line, column)
        
        self.advance()  # Consume closing quote
        value = ''.join(chars)
        return self._make_token(TokenType.STRING_LITERAL, value, line, column)

    def _scan_comment(self, line: int, column: int) -> Token:
        """Scan single-line comments (//)."""
        self.advance()  # Consume first /
        self.advance()  # Consume second /
        start_pos = self.position
        
        while self.current_char is not None and self.current_char != '\n':
            self.advance()
        
        value = self.code[start_pos:self.position]
        return self._make_token(TokenType.COMMENT, value, line, column)