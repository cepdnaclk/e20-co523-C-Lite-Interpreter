"""
test_lexer.py
Test suite for C-Lite lexical analyzer
"""

import pytest
from src.lexer import Lexer, Token, TokenType, LexerError


# ==================== Module-Level Helper Functions ====================

def assert_token_equals(token: Token, expected_type: TokenType, expected_value, expected_line: int, expected_column: int):
    """Assert a single token's properties."""
    assert token.type == expected_type, f"Expected type {expected_type}, got {token.type}"
    if expected_value is not None:
        assert token.value == expected_value, f"Expected value {expected_value}, got {token.value}"
    assert token.line == expected_line, f"Expected line {expected_line}, got {token.line}"
    assert token.column == expected_column, f"Expected column {expected_column}, got {token.column}"


def assert_tokens_equal(tokens: list, expected: list):
    """Assert a list of tokens matches expected list."""
    assert len(tokens) == len(expected), f"Token count mismatch: expected {len(expected)}, got {len(tokens)}"
    for i, (token, exp) in enumerate(zip(tokens, expected)):
        exp_type, exp_value, exp_line, exp_col = exp
        assert_token_equals(token, exp_type, exp_value, exp_line, exp_col)


# ==================== Test Classes ====================

class TestTokenRecognition:
    """Basic token recognition per C-Lite specification"""

    def test_keywords(self):
        code = "int float if else printf"
        tokens = list(Lexer(code).tokenize())
        
        expected = [
            (TokenType.INT, "int", 1, 1),
            (TokenType.FLOAT, "float", 1, 5),
            (TokenType.IF, "if", 1, 11),
            (TokenType.ELSE, "else", 1, 14),
            (TokenType.PRINTF, "printf", 1, 19),
            (TokenType.EOF, None, 1, 25)
        ]
        assert_tokens_equal(tokens, expected)

    def test_operators(self):
        code = "+ - * / > < == ="
        tokens = list(Lexer(code).tokenize())
        
        expected_types = [
            TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH,
            TokenType.GT, TokenType.LT, TokenType.EQ, TokenType.ASSIGN, TokenType.EOF
        ]
        assert [t.type for t in tokens] == expected_types
        assert tokens[6].value == "=="
        assert tokens[7].value == "="

    def test_delimiters(self):
        code = "( ) { } ;"
        tokens = list(Lexer(code).tokenize())
        
        expected_types = [
            TokenType.LPAREN, TokenType.RPAREN,
            TokenType.LBRACE, TokenType.RBRACE,
            TokenType.SEMICOLON, TokenType.EOF
        ]
        assert [t.type for t in tokens] == expected_types

class TestSourceLocationTracking:
    """Line/column tracking per lexical analysis"""

    def test_basic_locations(self):
        code = "int x;\nfloat y;"
        tokens = list(Lexer(code).tokenize())
        
        assert tokens[0].line == 1 and tokens[0].column == 1
        assert tokens[1].line == 1 and tokens[1].column == 5
        assert tokens[2].line == 1 and tokens[2].column == 6
        
        assert tokens[3].line == 2 and tokens[3].column == 1
        assert tokens[4].line == 2 and tokens[4].column == 7
        assert tokens[5].line == 2 and tokens[5].column == 8
        
        assert tokens[6].line == 2 and tokens[6].column == 9

    def test_tab_and_mixed_whitespace(self):
        code = "int\tx;\n\n  float\ty;"
        tokens = list(Lexer(code).tokenize())
        
        assert tokens[0].line == 1 and tokens[0].column == 1   # 'int'
        assert tokens[1].line == 1 and tokens[1].column == 5   # 'x' (after tab)
        assert tokens[2].line == 1 and tokens[2].column == 6   # ';'
        
        assert tokens[3].line == 3 and tokens[3].column == 3   # 'float' after 2 spaces
        assert tokens[4].line == 3 and tokens[4].column == 9   # 'y' after tab
        assert tokens[5].line == 3 and tokens[5].column == 10  # ';'


class TestIdentifierValidation:
    """C identifier rules: [a-zA-Z_][a-zA-Z0-9_]*"""

    @pytest.mark.parametrize("valid_ident", [
        "x", "_temp", "__", "_", "x1", "var_name123", "MAX_VALUE"
    ])
    def test_valid_identifiers(self, valid_ident):
        tokens = list(Lexer(valid_ident).tokenize())
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == valid_ident

    @pytest.mark.parametrize("invalid_ident,expected_behavior", [
        ("var@name", "error"),      # @ is invalid character
        ("class!", "error"),        # ! is invalid character
        ("1x", "number"),           # Lexed as INT_LITERAL + IDENTIFIER
        ("123", "number"),          # Lexed as INT_LITERAL
        ("my-var", "three_tokens"), # Lexed as IDENTIFIER - IDENTIFIER
    ])
    def test_invalid_identifiers(self, invalid_ident, expected_behavior):
        """
        Differentiate between lexer errors and valid tokenization.
        - Invalid chars (@, !) raise LexerError
        - Numbers starting with digit are valid INT_LITERAL
        - my-var is valid: identifier MINUS identifier
        """
        if expected_behavior == "error":
            with pytest.raises(LexerError) as exc:
                list(Lexer(invalid_ident).tokenize())
            assert "unexpected character" in str(exc.value).lower()
        elif expected_behavior == "number":
            # Should tokenize as number(s), not raise error
            tokens = list(Lexer(invalid_ident).tokenize())
            assert tokens[0].type == TokenType.INT_LITERAL
        elif expected_behavior == "three_tokens":
            # my-var = IDENTIFIER - IDENTIFIER
            tokens = list(Lexer(invalid_ident).tokenize())
            assert len(tokens) == 4  # IDENTIFIER, MINUS, IDENTIFIER, EOF
            assert tokens[0].type == TokenType.IDENTIFIER
            assert tokens[1].type == TokenType.MINUS


class TestNumericLiterals:
    """C numeric literal rules"""

    def test_integer_literals(self):
        tokens = list(Lexer("0 42 1000").tokenize())

        assert tokens[0].type == TokenType.INT_LITERAL and tokens[0].value == 0
        assert tokens[1].type == TokenType.INT_LITERAL and tokens[1].value == 42
        assert tokens[2].type == TokenType.INT_LITERAL and tokens[2].value == 1000 

    def test_float_literals_valid(self):
        cases = [
            ("3.14", 3.14),
            ("0.5", 0.5),
            (".7", 0.7),
            ("3.", 3.0),
            ("123.456", 123.456)
        ]
        for code, expected_value in cases:
            token = Lexer(code).tokenize_one()
            assert token.type == TokenType.FLOAT_LITERAL
            assert abs(token.value - expected_value) < 1e-9

    def test_float_literals_invalid(self):
        invalid_cases = [".", "..", "1.2.3", ".1.2"]
        for code in invalid_cases:
            with pytest.raises(LexerError) as exc:
                Lexer(code).tokenize_one()
            # Accept both "invalid" and "unexpected" in error message
            assert "invalid" in str(exc.value).lower() or "unexpected" in str(exc.value).lower()


class TestStringLiterals:
    """String literals for printf()"""

    def test_basic_string(self):
        code = 'printf("result: ");'
        tokens = list(Lexer(code).tokenize())
        
        assert tokens[2].type == TokenType.STRING_LITERAL
        assert tokens[2].value == "result: "

    def test_escaped_quotes(self):
        code = r'printf("he said \"hi\"");'
        tokens = list(Lexer(code).tokenize())
        assert tokens[2].value == 'he said "hi"'

    def test_invalid_unclosed_string(self):
        with pytest.raises(LexerError) as exc:
            list(Lexer('printf("unclosed').tokenize())
        assert "unclosed string" in str(exc.value).lower()


class TestComments:
    """Comment handling per lexical analysis best practices"""

    def test_single_line_comment(self):
        code = "int x; // variable declaration\nfloat y;"
        tokens = [t for t in Lexer(code).tokenize() if t.type != TokenType.COMMENT]
        
        # FIX: Corrected token indices after filtering
        assert tokens[0].type == TokenType.INT
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[2].type == TokenType.SEMICOLON
        assert tokens[3].type == TokenType.FLOAT  # After comment
        assert tokens[4].type == TokenType.IDENTIFIER
        assert tokens[5].type == TokenType.SEMICOLON

    def test_comment_at_eof(self):
        code = "int x; // comment at end"
        tokens = [t for t in Lexer(code).tokenize() if t.type != TokenType.COMMENT]
        assert tokens[-2].type == TokenType.SEMICOLON
        assert tokens[-1].type == TokenType.EOF

    def test_empty_comment(self):
        code = "int x;//\nfloat y;"
        tokens = [t for t in Lexer(code).tokenize() if t.type != TokenType.COMMENT]
        assert tokens[0].type == TokenType.INT


class TestErrorHandling:
    """Error detection per lexical analysis"""

    def test_invalid_character(self):
        code = "int x@;"
        with pytest.raises(LexerError) as exc:
            list(Lexer(code).tokenize())
        assert "@" in str(exc.value)
        assert "line 1" in str(exc.value).lower()
        assert "column 6" in str(exc.value).lower()

    def test_invalid_number_format(self):
        # Test full tokenization
        with pytest.raises(LexerError):
            list(Lexer("12.34.56").tokenize())


class TestBoundaryStressTests:
    """Stress test"""

    def test_very_long_identifier(self):
        ident = "a" * 1000
        tokens = list(Lexer(f"int {ident};").tokenize())
        assert tokens[1].value == ident
        assert len(tokens[1].value) == 1000

    def test_large_integer(self):
        tokens = list(Lexer("12345678901234567890;").tokenize())
        assert tokens[0].value == 12345678901234567890

    def test_repeated_operators(self):
        code = "+++ --- *** ///"
        tokens = list(Lexer(code).tokenize())
        assert [t.type for t in tokens[:6]] == [
            TokenType.PLUS, TokenType.PLUS, TokenType.PLUS,
            TokenType.MINUS, TokenType.MINUS, TokenType.MINUS
        ]


class TestIntegration:
    """Lexer validation with complete C-Lite programs"""

    def test_complete_program_1(self):
        code = """
        int x;
        float y = 3.14;
        if (x > 5) {
            printf(y);
        }
        """
        tokens = list(Lexer(code).tokenize())
        
        types = [t.type for t in tokens if t.type != TokenType.COMMENT]
        expected_sequence = [
            TokenType.INT, TokenType.IDENTIFIER, TokenType.SEMICOLON,
            TokenType.FLOAT, TokenType.IDENTIFIER, TokenType.ASSIGN,
            TokenType.FLOAT_LITERAL, TokenType.SEMICOLON,
            TokenType.IF, TokenType.LPAREN, TokenType.IDENTIFIER,
            TokenType.GT, TokenType.INT_LITERAL, TokenType.RPAREN,
            TokenType.LBRACE, TokenType.PRINTF, TokenType.LPAREN,
            TokenType.IDENTIFIER, TokenType.RPAREN, TokenType.SEMICOLON,
            TokenType.RBRACE, TokenType.EOF
        ]
        assert types == expected_sequence

    def test_nested_scopes_with_whitespace_variations(self):
        code = "int a;\t\n  if(a<10){\n\tfloat b; b=3.14; }"
        tokens = list(Lexer(code).tokenize())
        assert any(t.type == TokenType.LBRACE for t in tokens)
        assert any(t.type == TokenType.RBRACE for t in tokens)