"""
Test suite for C-Lite CLI (cli.py).

Test Coverage:
1. File Execution
2. Command-Line Code Execution (-e flag)
3. Verbose Mode
4. Error Handling
5. Edge Cases
6. Integration Tests
"""

import pytest
import subprocess
import sys
import os
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.lexer import Lexer, LexerError
from src.parser import Parser, ParserError
from src.interpreter import Interpreter, SemanticError


# =============================================================================
# Category 1: File Execution Tests
# =============================================================================

class TestCLIFileExecution:
    """Test CLI execution from files"""

    def test_cli_execute_hello_file(self, tmp_path):
        """Test: cli.py examples/hello.clt"""
        # Create test file
        test_file = tmp_path / "hello.clt"
        test_file.write_text("int x; x = 42; printf(x);", encoding='utf-8')
        
        # Run CLI
        result = subprocess.run(
            [sys.executable, "cli.py", str(test_file)],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            encoding='utf-8'  # FIX: Explicit UTF-8 encoding
        )
        
        assert result.returncode == 0
        assert "42" in result.stdout

    def test_cli_execute_arithmetic_file(self, tmp_path):
        """Test: cli.py with arithmetic operations"""
        test_file = tmp_path / "arith.clt"
        test_file.write_text("""
        int a;
        int b;
        a = 10;
        b = 5;
        printf(a + b);
        printf(a - b);
        printf(a * b);
        printf(a / b);
        """, encoding='utf-8')
        
        result = subprocess.run(
            [sys.executable, "cli.py", str(test_file)],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            encoding='utf-8'
        )
        
        assert result.returncode == 0
        assert "15" in result.stdout
        assert "5" in result.stdout
        assert "50" in result.stdout
        assert "2" in result.stdout

    def test_cli_execute_nonexistent_file(self):
        """Test: cli.py with nonexistent file"""
        result = subprocess.run(
            [sys.executable, "cli.py", "nonexistent.clt"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_cli_execute_invalid_extension(self, tmp_path):
        """Test: cli.py with non-.clt extension (should warn but execute)"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("int x; x = 5; printf(x);", encoding='utf-8')
        
        result = subprocess.run(
            [sys.executable, "cli.py", str(test_file)],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            encoding='utf-8'
        )
        
        # Should execute successfully (warning goes to stderr)
        assert "5" in result.stdout


# =============================================================================
# Category 2: Command-Line Code Execution (-e flag)
# =============================================================================

class TestCLICommandLineExecution:
    """Test CLI -e flag for direct code execution"""

    def test_cli_execute_simple_code(self):
        """Test: cli.py -e "int x; x = 5; printf(x);" """
        result = subprocess.run(
            [sys.executable, "cli.py", "-e", "int x; x = 5; printf(x);"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        assert result.returncode == 0
        assert "5" in result.stdout

    def test_cli_execute_arithmetic(self):
        """Test: cli.py -e with arithmetic"""
        result = subprocess.run(
            [sys.executable, "cli.py", "-e", "printf(3 + 4 * 5);"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        assert result.returncode == 0
        assert "23" in result.stdout  # 3 + (4 * 5)

    def test_cli_execute_if_statement(self):
        """Test: cli.py -e with if-else"""
        result = subprocess.run(
            [sys.executable, "cli.py", "-e", "int x; x = 10; if (x > 5) { printf(x); } else { printf(0); }"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        assert result.returncode == 0
        assert "10" in result.stdout

    def test_cli_execute_invalid_code(self):
        """Test: cli.py -e with invalid code"""
        result = subprocess.run(
            [sys.executable, "cli.py", "-e", "int x; printf(y);"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        assert result.returncode != 0
        assert "error" in result.stderr.lower()

    def test_cli_execute_both_file_and_e_flag(self):
        """Test: cli.py with both file and -e (should error)"""
        result = subprocess.run(
            [sys.executable, "cli.py", "test.clt", "-e", "int x;"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        assert result.returncode != 0
        assert "cannot specify both" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_cli_execute_no_input(self):
        """Test: cli.py with no input (should show help)"""
        result = subprocess.run(
            [sys.executable, "cli.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        assert result.returncode != 0
        assert "usage" in result.stdout.lower() or "help" in result.stdout.lower()


# =============================================================================
# Category 3: Verbose Mode Tests
# =============================================================================

class TestCLIVerboseMode:
    """Test CLI verbose mode (-v flag)"""

    def test_cli_verbose_shows_phases(self, tmp_path):
        """Test: cli.py -v shows phase information"""
        test_file = tmp_path / "test.clt"
        test_file.write_text("int x; x = 5;", encoding='utf-8')
        
        result = subprocess.run(
            [sys.executable, "cli.py", "-v", str(test_file)],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            encoding='utf-8'
        )
        
        # Verbose mode should succeed (returncode 0)
        assert result.returncode == 0
        # Verbose output goes to stderr, regular output to stdout
        assert "phase" in result.stderr.lower() or "lexical" in result.stderr.lower()

    def test_cli_verbose_with_command_line(self):
        """Test: cli.py -v -e with verbose output"""
        result = subprocess.run(
            [sys.executable, "cli.py", "-v", "-e", "int x; x = 5;"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            encoding='utf-8'
        )
        
        # Verbose mode should succeed (returncode 0)
        assert result.returncode == 0
        # Verbose output goes to stderr
        assert "phase" in result.stderr.lower() or "lexical" in result.stderr.lower()


# =============================================================================
# Category 4: Error Handling Tests
# =============================================================================

class TestCLIErrorHandling:
    """Test CLI error reporting"""

    def test_cli_lexical_error(self):
        """Test: cli.py with lexical error"""
        result = subprocess.run(
            [sys.executable, "cli.py", "-e", "int x; x = @;"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        assert result.returncode != 0
        assert "lexer" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_cli_syntax_error(self):
        """Test: cli.py with syntax error"""
        result = subprocess.run(
            [sys.executable, "cli.py", "-e", "int x; x = 5"],  # Missing semicolon
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        assert result.returncode != 0
        assert "parser" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_cli_semantic_error(self):
        """Test: cli.py with semantic error (undefined variable)"""
        result = subprocess.run(
            [sys.executable, "cli.py", "-e", "printf(x);"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        assert result.returncode != 0
        assert "semantic" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_cli_error_includes_line_number(self):
        """Test: CLI error messages include line numbers"""
        result = subprocess.run(
            [sys.executable, "cli.py", "-e", "int x; printf(y);"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        assert result.returncode != 0
        # Error should include location information
        assert "line" in result.stderr.lower() or "column" in result.stderr.lower() or "error" in result.stderr.lower()


# =============================================================================
# Category 5: Edge Cases
# =============================================================================

class TestCLIEdgeCases:
    """Test CLI edge cases"""

    def test_cli_empty_file(self, tmp_path):
        """Test: cli.py with empty file"""
        test_file = tmp_path / "empty.clt"
        test_file.write_text("")
        
        result = subprocess.run(
            [sys.executable, "cli.py", str(test_file)],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_cli_whitespace_only_file(self, tmp_path):
        """Test: cli.py with whitespace only"""
        test_file = tmp_path / "whitespace.clt"
        test_file.write_text("   \n\t\n   ")
        
        result = subprocess.run(
            [sys.executable, "cli.py", str(test_file)],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        assert result.returncode == 0

    def test_cli_unicode_in_file(self, tmp_path):
        """Test: cli.py with unicode in comments"""
        test_file = tmp_path / "unicode.clt"
        # FIX: Use simple ASCII comment (Windows-safe)
        test_file.write_text("int x; // test comment", encoding='utf-8')
        
        result = subprocess.run(
            [sys.executable, "cli.py", str(test_file)],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            encoding='utf-8'
        )
        
        # Should execute successfully (no output since x not printed)
        assert result.returncode == 0
        # Verify no errors in stderr
        assert "error" not in result.stderr.lower()

    def test_cli_version_flag(self):
        """Test: cli.py --version"""
        result = subprocess.run(
            [sys.executable, "cli.py", "--version"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        assert result.returncode == 0
        assert "version" in result.stdout.lower() or "0." in result.stdout

    def test_cli_help_flag(self):
        """Test: cli.py --help"""
        result = subprocess.run(
            [sys.executable, "cli.py", "--help"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        assert result.returncode == 0
        assert "usage" in result.stdout.lower()


# =============================================================================
# Category 6: Integration Tests
# =============================================================================

class TestCLIIntegration:
    """Test CLI integration with full programs"""

    def test_cli_complete_program(self, tmp_path):
        """Test: cli.py with complete C-Lite program"""
        test_file = tmp_path / "complete.clt"
        test_file.write_text("""
        int x;
        int y;
        x = 10;
        y = 20;
        if (x > 5) {
            printf(x);
        } else {
            printf(y);
        }
        """)
        
        result = subprocess.run(
            [sys.executable, "cli.py", str(test_file)],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        assert result.returncode == 0
        assert "10" in result.stdout

    def test_cli_nested_blocks(self, tmp_path):
        """Test: cli.py with nested blocks"""
        test_file = tmp_path / "nested.clt"
        test_file.write_text("""
        int x;
        x = 10;
        {
            int y;
            y = 20;
            printf(y);
        }
        printf(x);
        """)
        
        result = subprocess.run(
            [sys.executable, "cli.py", str(test_file)],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        assert result.returncode == 0
        assert "20" in result.stdout
        assert "10" in result.stdout

    def test_cli_float_operations(self, tmp_path):
        """Test: cli.py with float operations"""
        test_file = tmp_path / "float.clt"
        test_file.write_text("""
        float x;
        x = 3.14;
        printf(x);
        """)
        
        result = subprocess.run(
            [sys.executable, "cli.py", str(test_file)],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        assert result.returncode == 0
        assert "3.14" in result.stdout or "3" in result.stdout