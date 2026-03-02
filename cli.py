#!/usr/bin/env python3
"""
Command-Line Interface for C-Lite Interpreter.
End-user entry point for executing C-Lite programs.
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.lexer import Lexer, LexerError
from src.parser import Parser, ParserError
from src.interpreter import Interpreter, SemanticError
from src.errors import CLiteError


def run_clite(source_code: str, source_name: str = "<stdin>", verbose: bool = False) -> int:
    """
    Execute C-Lite source code through all phases.
    """
    try:
        # ==================== Phase 1: Lexical Analysis ====================
        if verbose:
            print(f"[Phase 1] Lexical Analysis: {source_name}", file=sys.stderr)
        
        lexer = Lexer(source_code)
        tokens = list(lexer.tokenize())
        
        if verbose:
            print(f"  ✓ Generated {len(tokens)} tokens", file=sys.stderr)
            if len(tokens) <= 20:
                for token in tokens:
                    print(f"    {token}", file=sys.stderr)
        
        # ==================== Phase 2: Syntax Analysis ====================
        if verbose:
            print(f"[Phase 2] Syntax Analysis: Building AST", file=sys.stderr)
        
        parser = Parser(tokens)
        ast = parser.parse()
        
        if verbose:
            print(f"AST constructed: {ast}", file=sys.stderr)
        
        # ==================== Phase 3: Semantic Evaluation ====================
        if verbose:
            print(f"[Phase 3] Semantic Evaluation: Executing program", file=sys.stderr)
        
        interpreter = Interpreter()
        output = interpreter.execute(ast)
        
        if verbose:
            print(f"Execution complete", file=sys.stderr)
            print(f"printf() outputs: {output}", file=sys.stderr)
        
        # Print output (stdout for actual program output)
        for value in output:
            print(value)
        
        return 0
    
    except LexerError as e:
        print(f"Lexer Error in {source_name}: {e}", file=sys.stderr)
        return 1
    
    except ParserError as e:
        print(f"Parser Error in {source_name}: {e}", file=sys.stderr)
        return 1
    
    except SemanticError as e:
        print(f"Semantic Error in {source_name}: {e}", file=sys.stderr)
        return 1
    
    except CLiteError as e:
        print(f"C-Lite Error in {source_name}: {e}", file=sys.stderr)
        return 1
    
    except Exception as e:
        print(f"Internal Error in {source_name}: {type(e).__name__}: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


def main():
    """Main entry point for C-Lite CLI."""
    # Set UTF-8 encoding for Windows console compatibility
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    parser = argparse.ArgumentParser(
        description='C-Lite Interpreter',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'source_file',
        nargs='?',
        type=Path,
        help='C-Lite source file (.clt extension)'
    )
    
    parser.add_argument(
        '-e', '--execute',
        type=str,
        metavar='CODE',
        help='Execute C-Lite code directly from command line'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed phase information'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='C-Lite Interpreter v0.4.0 (CO523 Project)'
    )
    
    args = parser.parse_args()
    
    # Validate input
    if not args.source_file and not args.execute:
        parser.print_help()
        print("\nError: Either provide a source file or use -e/--execute option", file=sys.stderr)
        return 1
    
    if args.source_file and args.execute:
        print("Error: Cannot specify both source file and -e option", file=sys.stderr)
        return 1
    
    # Execute from command line code
    if args.execute:
        return run_clite(args.execute, source_name="<command-line>", verbose=args.verbose)
    
    # Execute from file
    if args.source_file:
        if not args.source_file.exists():
            print(f"Error: File not found: {args.source_file}", file=sys.stderr)
            return 1
        
        if not args.source_file.suffix in ['.clt', '.c', '.txt']:
            print(f"Warning: File extension '{args.source_file.suffix}' is not standard (.clt recommended)", 
                  file=sys.stderr)
        
        try:
            source_code = args.source_file.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                source_code = args.source_file.read_text(encoding='latin-1')
            except Exception as e:
                print(f"Error: Cannot read file (encoding issue): {e}", file=sys.stderr)
                return 1
        except Exception as e:
            print(f"Error: Cannot read file: {e}", file=sys.stderr)
            return 1
        
        return run_clite(source_code, source_name=str(args.source_file), verbose=args.verbose)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())