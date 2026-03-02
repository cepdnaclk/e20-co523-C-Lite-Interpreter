#!/usr/bin/env python3
"""
Interactive Read-Eval-Print Loop (REPL) for C-Lite Interpreter.
Allows interactive experimentation with C-Lite language constructs.

Usage:
    python repl.py

Commands:
    :help     - Show help message
    :clear    - Clear interpreter state (reset all variables)
    :reset    - Alias for :clear
    :exit     - Exit REPL
    :quit     - Alias for :exit
    :version  - Show version information
    :vars     - Show current variables in symbol table
    :ast      - Show AST for last parsed program (verbose mode)
    :tokens   - Show tokens for last parsed program (verbose mode)
"""

import sys
import os
from typing import List, Optional, Tuple

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.lexer import Lexer, LexerError
from src.parser import Parser, ParserError
from src.interpreter import Interpreter, SemanticError
from src.errors import CLiteError
from src.symbol_table import SymbolTable


# =============================================================================
# REPL Configuration
# =============================================================================

class REPLConfig:
    """Configuration constants for REPL."""
    VERSION = "0.4.0"
    COURSE = "CO523 - Programming Languages"
    DEPARTMENT = "Department of Computer Engineering"
    UNIVERSITY = "University of Peradeniya"
    SEMESTER = "Semester 7, 2025-2026"
    
    PROMPT = ">>> "
    CONTINUE_PROMPT = "... "
    
    MAX_HISTORY = 1000  # Maximum lines to keep in history
    VERBOSE = False  # Show phase details by default


# =============================================================================
# REPL State Management
# =============================================================================

class REPLState:
    """
    Manages REPL state including interpreter, history, and configuration.
    
    CO523 Week 13: Language Implementation - State management for interactive execution.
    """
    
    def __init__(self):
        """Initialize REPL state."""
        self.interpreter = Interpreter()
        self.history: List[Tuple[str, int]] = []  # List of (code, start_line_number)
        self.current_line = 1  # Current line number (for error reporting)
        self.verbose = REPLConfig.VERBOSE
        self.running = True
        self.last_tokens = []  # Cache for :tokens command
        self.last_ast = None  # Cache for :ast command
        self.last_output_count = 0  # Track output count for isolation
    
    def add_to_history(self, code: str) -> None:
        """Add code to history and update line number."""
        start_line = self.current_line
        self.history.append((code, start_line))
        if len(self.history) > REPLConfig.MAX_HISTORY:
            self.history.pop(0)
        # Count actual lines in code for accurate line numbers
        self.current_line += code.count('\n') + 1
    
    def reset(self) -> None:
        """Reset interpreter state (clear all variables)."""
        self.interpreter.reset()
        self.last_output_count = 0
        # Keep history, but clear symbol table
    
    def clear_history(self) -> None:
        """Clear input history."""
        self.history.clear()
        self.current_line = 1
    
    def get_error_line(self, error_line: int) -> int:
        """
        Convert error line (relative to current command) to absolute session line.
        
        Args:
            error_line: Line number from error (relative to current command)
        
        Returns:
            Absolute line number in REPL session
        """
        # Find the start line of the current command
        if self.history:
            last_code, last_start_line = self.history[-1]
            return last_start_line + error_line - 1
        return error_line


# =============================================================================
# REPL Commands
# =============================================================================

class REPLCommands:
    """Built-in REPL commands (prefixed with ':')."""
    
    HELP = ":help"
    CLEAR = ":clear"
    RESET = ":reset"
    EXIT = ":exit"
    QUIT = ":quit"
    VERSION = ":version"
    VARS = ":vars"
    AST = ":ast"
    TOKENS = ":tokens"
    VERBOSE = ":verbose"
    QUIET = ":quiet"
    
    ALL = [HELP, CLEAR, RESET, EXIT, QUIT, VERSION, VARS, AST, TOKENS, VERBOSE, QUIET]


# =============================================================================
# REPL Implementation
# =============================================================================

class CLiteREPL:
    """
    Interactive Read-Eval-Print Loop for C-Lite.
    
    CO523 Week 13: Language Implementation - Interactive interpreter for
    experimentation and debugging.
    
    Features:
    - Multi-line input support (detects incomplete statements)
    - State persistence between commands
    - Phase visualization (verbose mode)
    - Error recovery (continue after errors)
    - Built-in commands for debugging
    - Output isolation (each command shows only its own output)
    """
    
    def __init__(self):
        """Initialize REPL."""
        self.state = REPLState()
        self.buffer = ""  # Multi-line input buffer
        self.in_multiline = False  # Track if we're in multi-line mode
    
    def print_banner(self) -> None:
        """Print REPL welcome banner."""
        banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                    C-Lite Interactive REPL                    ║
║                                                               ║
║  {REPLConfig.COURSE:<54} ║
║  {REPLConfig.DEPARTMENT:<54} ║
║  {REPLConfig.UNIVERSITY:<54} ║
║  {REPLConfig.SEMESTER:<54} ║
╠══════════════════════════════════════════════════════════════╣
║  Type C-Lite code and press Enter to execute.                ║
║  Use :help for available commands.                           ║
║  Use :exit or Ctrl+D to quit.                                ║
╚══════════════════════════════════════════════════════════════╝
"""
        print(banner)
    
    def print_help(self) -> None:
        """Print help message."""
        help_text = f"""
╔══════════════════════════════════════════════════════════════╗
║                      C-Lite REPL Help                        ║
╠══════════════════════════════════════════════════════════════╣
║  REPL Commands:                                              ║
║    :help     - Show this help message                        ║
║    :clear    - Clear interpreter state (reset variables)     ║
║    :reset    - Alias for :clear                              ║
║    :exit     - Exit REPL                                     ║
║    :quit     - Alias for :exit                               ║
║    :version  - Show version information                      ║
║    :vars     - Show current variables in symbol table        ║
║    :ast      - Show AST for last parsed program              ║
║    :tokens   - Show tokens for last parsed program           ║
║    :verbose  - Enable verbose mode (show all phases)         ║
║    :quiet    - Disable verbose mode                          ║
╠══════════════════════════════════════════════════════════════╣
║  C-Lite Language Support (Project Spec §3):                  ║
║    Data Types: int, float                                    ║
║    Operators: +, -, *, /, >, <, ==                           ║
║    Control: if-else, blocks {{ }}                            ║
║    I/O: printf(expression)                                   ║
║    Variables: Must be declared before use                    ║
╠══════════════════════════════════════════════════════════════╣
║  Example Code:                                               ║
║    >>> int x;                                                ║
║    >>> x = 42;                                               ║
║    >>> printf(x);                                            ║
║    42                                                        ║
║    >>> if (x > 10) {{ printf(x); }} else {{ printf(0); }}       ║
║    42                                                        ║
╚══════════════════════════════════════════════════════════════╝
"""
        print(help_text)
    
    def print_version(self) -> None:
        """Print version information."""
        print(f"""
C-Lite Interpreter v{REPLConfig.VERSION}
{REPLConfig.COURSE}
{REPLConfig.DEPARTMENT}
{REPLConfig.UNIVERSITY}
{REPLConfig.SEMESTER}

Phases Implemented:
  ✓ Phase 1: Lexical Analysis (Lexer)
  ✓ Phase 2: Syntax Analysis (Parser)
  ✓ Phase 3: Semantic Evaluation (Interpreter)

Test Coverage: 237 tests (100% passing)
""")
    
    def print_variables(self) -> None:
        """Print current variables in symbol table."""
        print("\nVariables in scope:")
        
        # Access symbol table internals (for debugging)
        for i, scope in enumerate(self.state.interpreter.symbol_table._scopes):
            if scope:  # Only print non-empty scopes
                print(f"  Scope {i}:")
                for name, symbol in scope.items():
                    value = symbol.value if symbol.value is not None else "(uninitialized)"
                    print(f"    {name} ({symbol.var_type}) = {value}")
        
        if not any(scope for scope in self.state.interpreter.symbol_table._scopes):
            print("  (no variables declared)")
        print()
    
    def print_tokens(self) -> None:
        """Print tokens from last parsed program."""
        if not self.state.last_tokens:
            print("No tokens cached. Execute some code first.\n")
            return
        
        print(f"\nTokens ({len(self.state.last_tokens)} total):")
        for i, token in enumerate(self.state.last_tokens):
            print(f"  [{i:3d}] {token}")
        print()
    
    def print_ast(self) -> None:
        """Print AST from last parsed program."""
        if self.state.last_ast is None:
            print("No AST cached. Execute some code first.\n")
            return
        
        print(f"\nAST:")
        print(f"  {self.state.last_ast}")
        print()
    
    def is_complete_statement(self, code: str) -> bool:
        """
        Check if code is a complete statement (not requiring continuation).
        
        CO523 Week 3: Syntax Analysis - Detect incomplete constructs.
        
        Heuristics:
        - Unclosed braces {{ → needs continuation
        - Unclosed parentheses ( → needs continuation
        - Ends with if/else without block → might be complete
        """
        # Count braces
        open_braces = code.count('{')
        close_braces = code.count('}')
        
        # Count parentheses
        open_parens = code.count('(')
        close_parens = code.count(')')
        
        # Check if braces are balanced
        if open_braces > close_braces:
            return False
        
        # Check if parentheses are balanced
        if open_parens > close_parens:
            return False
        
        # Check for incomplete if statement
        stripped = code.strip()
        if stripped.startswith('if') and stripped.endswith('('):
            return False
        
        if stripped.startswith('if') and '(' in stripped and ')' not in stripped:
            return False
        
        return True
    
    def execute(self, code: str) -> bool:
        """
        Execute C-Lite code through all phases.
        
        Args:
            code: C-Lite source code
        
        Returns:
            True if execution succeeded, False otherwise
        """
        try:
            # Save current output count for isolation
            previous_output_count = len(self.state.interpreter.output)
            
            # ==================== Lexical Analysis ====================
            if self.state.verbose:
                print("Lexical Analysis")
            
            lexer = Lexer(code)
            tokens = list(lexer.tokenize())
            self.state.last_tokens = tokens
            
            if self.state.verbose:
                print(f"Generated {len(tokens)} tokens")
                if len(tokens) <= 15:
                    for token in tokens:
                        print(f"    {token}")
            
            # ==================== Syntax Analysis ====================
            if self.state.verbose:
                print("Syntax Analysis")
            
            parser = Parser(tokens)
            ast = parser.parse()
            self.state.last_ast = ast
            
            if self.state.verbose:
                print(f"AST: {ast}")
            
            # ==================== Semantic Evaluation ====================
            if self.state.verbose:
                print("Semantic Evaluation")
            
            output = self.state.interpreter.execute(ast)
            
            #  Only print NEW outputs (isolation from previous commands)
            new_outputs = output[previous_output_count:]
            
            if self.state.verbose:
                print(f"Output: {new_outputs}")
            
            # FIX 1: Print only new outputs (one per printf call)
            if not self.state.verbose:
                for value in new_outputs:
                    print(value)
            
            return True
        
        except LexerError as e:
            # FIX 2: Convert to absolute line number
            abs_line = self.state.get_error_line(e.line)
            print(f"Lexer Error at line {abs_line}: {e.message}", file=sys.stderr)
            return False
        
        except ParserError as e:
            # FIX 2: Convert to absolute line number
            abs_line = self.state.get_error_line(e.line)
            print(f"Parser Error at line {abs_line}: {e.message}", file=sys.stderr)
            return False
        
        except SemanticError as e:
            # FIX 2: Convert to absolute line number
            abs_line = self.state.get_error_line(e.line)
            print(f"Semantic Error at line {abs_line}: {e.message}", file=sys.stderr)
            return False
        
        except CLiteError as e:
            abs_line = self.state.get_error_line(e.line)
            print(f"C-Lite Error at line {abs_line}: {str(e)}", file=sys.stderr)
            return False
        
        except Exception as e:
            print(f"Internal Error: {type(e).__name__}: {e}", file=sys.stderr)
            if self.state.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def handle_command(self, command: str) -> bool:
        """
        Handle REPL command (prefixed with ':').
        
        Args:
            command: Command string (e.g., ":help")
        
        Returns:
            True if REPL should continue, False to exit
        """
        cmd = command.strip().lower()
        
        if cmd == REPLCommands.HELP:
            self.print_help()
            return True
        
        elif cmd in [REPLCommands.CLEAR, REPLCommands.RESET]:
            self.state.reset()
            print("Interpreter state cleared.\n")
            return True
        
        elif cmd in [REPLCommands.EXIT, REPLCommands.QUIT]:
            print("Goodbye!")
            return False
        
        elif cmd == REPLCommands.VERSION:
            self.print_version()
            return True
        
        elif cmd == REPLCommands.VARS:
            self.print_variables()
            return True
        
        elif cmd == REPLCommands.AST:
            self.print_ast()
            return True
        
        elif cmd == REPLCommands.TOKENS:
            self.print_tokens()
            return True
        
        elif cmd == REPLCommands.VERBOSE:
            self.state.verbose = True
            print("Verbose mode enabled.\n")
            return True
        
        elif cmd == REPLCommands.QUIET:
            self.state.verbose = False
            print("Verbose mode disabled.\n")
            return True
        
        else:
            print(f"Unknown command: {command}")
            print("Type :help for available commands.\n")
            return True
    
    def get_input(self) -> Optional[str]:
        """
        Get input from user with proper prompt.
        
        Returns:
            Input string, or None on EOF
        """
        try:
            if self.in_multiline:
                prompt = REPLConfig.CONTINUE_PROMPT
            else:
                prompt = REPLConfig.PROMPT
            
            line = input(prompt)
            return line
        
        except EOFError:
            return None
        
        except KeyboardInterrupt:
            print()  # Newline after ^C
            return ""
    
    def run(self) -> None:
        """
        Main REPL loop.
        
        CO523 Week 13: Interactive language experimentation.
        """
        self.print_banner()
        
        while self.state.running:
            # Get input
            line = self.get_input()
            
            # Handle EOF (Ctrl+D)
            if line is None:
                print("\nGoodbye!")
                break
            
            # Strip whitespace
            line = line.strip()
            
            # Skip empty lines (but stay in multiline mode if active)
            if not line and not self.in_multiline:
                continue
            
            # Handle commands (only in single-line mode)
            if line.startswith(':') and not self.in_multiline:
                self.state.running = self.handle_command(line)
                continue
            
            # Accumulate multi-line input
            if self.in_multiline:
                self.buffer += "\n" + line
            else:
                self.buffer = line
            
            # Check if statement is complete
            if self.is_complete_statement(self.buffer):
                # Execute accumulated code
                self.execute(self.buffer)
                
                # Add to history with line number tracking
                self.state.add_to_history(self.buffer)
                
                # Reset buffer
                self.buffer = ""
                self.in_multiline = False
            else:
                # Continue accumulating
                self.in_multiline = True


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Main entry point for C-Lite REPL."""
    try:
        repl = CLiteREPL()
        repl.run()
    except Exception as e:
        print(f"Fatal Error: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()