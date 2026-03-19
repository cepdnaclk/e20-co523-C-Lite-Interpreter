# C-Lite Interpreter

![Version](https://img.shields.io/badge/version-0.4.0-blue)
![Python](https://img.shields.io/badge/python-%3E%3D3.8-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-293%20passing-brightgreen)
![Status](https://img.shields.io/badge/status-active-success)
![Course](https://img.shields.io/badge/course-CO523-orange)

A tree-walking interpreter for **C-Lite**, a pedagogical subset of the C programming language.  
Built from scratch in Python - lexer, parser, AST, symbol table, and evaluator - with no external runtime dependencies.

[Quick Start](#quick-start) | [Language Reference](#language-reference) | [Architecture](#architecture) | [Testing](#testing) | [Contributing](#contributing) | [License](#license)

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running a Program](#running-a-program)
  - [Interactive REPL](#interactive-repl)
- [Language Reference](#language-reference)
  - [Data Types](#data-types)
  - [Variables](#variables)
  - [Operators](#operators)
  - [Control Flow](#control-flow)
  - [I/O](#io)
  - [Comments](#comments)
  - [Scoping Rules](#scoping-rules)
  - [Type Coercion](#type-coercion)
  - [Formal Grammar (EBNF)](#formal-grammar-ebnf)
- [Architecture](#architecture)
  - [Pipeline Overview](#pipeline-overview)
  - [Phase 1 -- Lexical Analysis](#phase-1----lexical-analysis)
  - [Phase 2 -- Syntax Analysis](#phase-2----syntax-analysis)
  - [Phase 3 -- Semantic Evaluation](#phase-3----semantic-evaluation)
  - [Error Hierarchy](#error-hierarchy)
  - [AST Node Reference](#ast-node-reference)
  - [Token Type Reference](#token-type-reference)
- [Directory Layout](#directory-layout)
- [Usage](#usage)
  - [CLI Reference](#cli-reference)
  - [REPL Commands](#repl-commands)
  - [Programmatic API](#programmatic-api)
- [Examples](#examples)
- [Testing](#testing)
  - [Running the Test Suite](#running-the-test-suite)
  - [Test Matrix](#test-matrix)
  - [Test Categories](#test-categories)
- [Design Decisions](#design-decisions)
- [Known Limitations](#known-limitations)
- [Performance](#performance)
- [Contributing](#contributing)
- [License](#license)
  
---

## Overview

**C-Lite** is a simplified, statically-typed subset of C designed to demonstrate the full program translation pipeline from raw source text to evaluated output without the complexity of a production C compiler.

The interpreter implements three classical compilation phases:

| Phase | Component | Responsibility |
|-------|-----------|----------------|
| 1 | **Lexer** | Tokenizes source text into a stream of classified tokens |
| 2 | **Parser** | Builds an Abstract Syntax Tree (AST) via recursive-descent parsing |
| 3 | **Interpreter** | Walks the AST using the Visitor pattern to evaluate the program |

### Key Features

- **Zero external runtime dependencies** - only the Python 3.8+ standard library
- **Three-phase pipeline** - lexer, parser, and tree-walking interpreter
- **LL(1) recursive-descent parser** with formal EBNF grammar
- **Visitor-pattern AST evaluation** with type-checked symbol table
- **Nested block scoping** with variable shadowing and lifetime management
- **Implicit type coercion** following C semantics (`int` <-> `float`)
- **Precise error reporting** with line/column source locations
- **Interactive REPL** with multi-line input, state inspection, and history
- **293 passing tests** across 7 test modules covering all interpreter phases

---

## Quick Start

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | >= 3.8 |
| pip | any |

### Installation

```bash
# Clone the repository
git clone https://github.com/ChethiyaB/C-Lite-Interpreter.git
cd C-Lite-Interpreter

# Install development dependencies (pytest)
pip install -r requirements.txt
```

### Running a Program

Create a file `hello.clt`:

```c
int x;
x = 42;
printf(x);
```

Execute it:

```bash
python cli.py hello.clt
```

```
42
```

### Interactive REPL

```bash
python repl.py
```

```
>>> int x;
>>> x = 10;
>>> printf(x);
10
>>> if (x > 5) { printf(1); } else { printf(0); }
1
```

---

## Language Reference

### Data Types

| Type | Description | Literal Examples |
|------|-------------|------------------|
| `int` | Signed integer | `0`, `42`, `1000` |
| `float` | IEEE 754 double-precision floating-point | `3.14`, `.5`, `7.`, `0.0` |

### Variables

Variables **must** be declared before use. Declaration and assignment are separate statements:

```c
int x;          // declaration
x = 42;         // assignment

float pi;
pi = 3.14159;
```

> **Note:** Using a variable before initialization raises a `SemanticError`.

### Operators

#### Arithmetic Operators

| Operator | Description | Example | Result Type |
|----------|-------------|---------|-------------|
| `+` | Addition | `3 + 4` | `int` or `float` |
| `-` | Subtraction | `10 - 3` | `int` or `float` |
| `*` | Multiplication | `5 * 2` | `int` or `float` |
| `/` | Division | `7 / 2` | `int` (truncated) or `float` |

**Division semantics:**
- `int / int` -> integer (floor) division: `7 / 2` = `3`
- `float / int` or `int / float` -> float division: `7.0 / 2` = `3.5`
- Division by zero raises `SemanticError`

#### Relational Operators

| Operator | Description | Returns |
|----------|-------------|---------|
| `>` | Greater than | `1` (true) or `0` (false) |
| `<` | Less than | `1` (true) or `0` (false) |
| `==` | Equal to | `1` (true) or `0` (false) |

Relational operators return **integer** values (`1` or `0`), consistent with C semantics.

#### Unary Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `+` | Unary positive | `+5` |
| `-` | Unary negation | `-x` |

#### Assignment Operator

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Assignment | `x = 5;` |

#### Operator Precedence (highest to lowest)

```
Precedence    Operators        Associativity    Description
─────────────────────────────────────────────────────────────
   1          ( )              N/A              Parentheses (grouping)
   2          + -  (unary)     right            Unary positive / negation
   3          * /              left             Multiplicative
   4          + -  (binary)    left             Additive
   5          > < ==           left             Relational / equality
   6          =                N/A              Assignment (statement-level)
```

### Control Flow

#### `if`-`else` Statement

```c
if (condition) {
    // then-branch
} else {
    // else-branch (optional)
}
```

- **Condition truthiness** follows C rules: `0` and `0.0` are false; all other values are true.
- The `else` clause is optional.
- Dangling `else` binds to the **nearest** `if` (standard C behavior).

### I/O

#### `printf(expression);`

Evaluates the expression and prints the result to standard output:

```c
printf(42);           // prints: 42
printf(3.14);         // prints: 3.14
printf(x + y);        // prints the computed sum
```

- Integer-valued floats are printed without a decimal point (e.g., `6.0` prints as `6`).

### Comments

Single-line comments are supported with `//`:

```c
int x;   // this is a comment
x = 42;  // assign value
// this entire line is a comment
```

### Scoping Rules

Blocks (`{ }`) introduce **new lexical scopes**. Variables declared inside a block are destroyed when the block exits:

```c
int x;
x = 10;

{
    int y;           // y exists only inside this block
    y = 20;
    int x;           // shadows the outer x
    x = 99;
    printf(x);       // prints: 99
}

printf(x);           // prints: 10  (outer x restored)
// printf(y);        // ERROR: y is not accessible here
```

Variable **shadowing** is supported: an inner scope may declare a variable with the same name as an outer scope. The inner variable takes precedence within its scope.

### Type Coercion

C-Lite performs **implicit type coercion** following C semantics:

| Context | Rule | Example |
|---------|------|---------|
| `int` var <- `float` expr | Truncation (toward zero) | `int x; x = 3.14;` -> `x == 3` |
| `float` var <- `int` expr | Promotion | `float y; y = 10;` -> `y == 10.0` |
| Mixed arithmetic | Promote to `float` | `3 + 2.5` -> `5.5` |
| Mixed comparison | Promote to `float` | `3 == 3.0` -> `1` (true) |

### Formal Grammar (EBNF)

The complete grammar specification is available at [`docs/grammar.ebnf`](docs/grammar.ebnf). A summary:

```ebnf
program               = { declaration | statement } ;
declaration           = type_specifier identifier ";" ;
type_specifier        = "int" | "float" ;

statement             = assignment | if_statement | printf_call | block | ";" ;
assignment            = identifier "=" expression ";" ;
if_statement          = "if" "(" expression ")" statement [ "else" statement ] ;
block                 = "{" { declaration | statement } "}" ;
printf_call           = "printf" "(" expression ")" ";" ;

expression            = relational_expression ;
relational_expression = additive_expression [ ( ">" | "<" | "==" ) additive_expression ] ;
additive_expression   = multiplicative_expression { ( "+" | "-" ) multiplicative_expression } ;
multiplicative_expression = primary_expression { ( "*" | "/" ) primary_expression } ;
primary_expression    = number | identifier | "(" expression ")" | unary_expression ;
unary_expression      = ( "+" | "-" ) primary_expression ;
```

**Grammar properties:**
- **LL(1) compatible** -- no left-recursion, disjoint FIRST/FOLLOW sets
- **Suitable for recursive-descent parsing** without backtracking
- Complete FIRST/FOLLOW set analysis available in [`docs/first_follow_sets.md`](docs/first_follow_sets.md)

---

## Architecture

### Pipeline Overview

The interpreter processes source code through three sequential phases, each transforming the input into a progressively higher-level representation:


![Pipeline](docs/C-Lite_Interpreter_Pipeline.png)


### Phase 1 -- Lexical Analysis

**Module:** `src/lexer.py`

The lexer (scanner) converts raw source text into a stream of `Token` objects. Each token carries its type, value, and source location (line and column).

```
Source: "int x = 42;"

Tokens: [
    Token(int, "int",   1:1),
    Token(identifier, "x", 1:5),
    Token(=, "=",       1:7),
    Token(integer, 42,  1:9),
    Token(;, ";",       1:11),
    Token(eof, None,    1:12)
]
```

**Implementation details:**
- Hand-written DFA-based scanner (no parser generators)
- Single-pass `O(n)` tokenization via character-by-character advancement
- Generator-based token emission (`yield`) for memory efficiency
- Infinite-loop guard to prevent runaway scanning
- Escape sequence support in string literals (`\n`, `\t`, `\"`, `\\`)

### Phase 2 -- Syntax Analysis

**Module:** `src/parser.py`

The parser consumes the token stream and constructs an Abstract Syntax Tree (AST). It uses **LL(1) recursive descent** - each grammar production is implemented as a method.

```
Source: "x = 3 + 4 * 5;"

AST:
    Assignment
    ├── name: "x"
    └── value: BinaryOp(+)
              ├── left: NumberLiteral(3)
              └── right: BinaryOp(*)
                        ├── left: NumberLiteral(4)
                        └── right: NumberLiteral(5)
```

**Implementation details:**
- One-token lookahead for all parsing decisions
- Left-associative binary operators via iterative loops (not left-recursion)
- Operator precedence enforced through grammar stratification (4 levels)
- Immutable `@dataclass(frozen=True)` AST nodes

### Phase 3 -- Semantic Evaluation

**Module:** `src/interpreter.py`

The interpreter traverses the AST using the **Visitor pattern** (`ASTVisitor` base class). Each AST node type has a corresponding `visit_*` method.

```
AST Traversal:
    visit_program
    ├── visit_declaration  →  SymbolTable.declare("x", int)
    ├── visit_assignment   →  SymbolTable.update("x", 42)
    │   └── visit_number_literal  →  returns 42
    └── visit_printf_call  →  output.append(42)
        └── visit_identifier  →  SymbolTable.get_value("x") → 42
```

**Implementation details:**
- Stack-based `SymbolTable` with nested scope support (enter/exit scope on block boundaries)
- C-style truthiness for conditionals (`0`/`0.0` = false, non-zero = true)
- Implicit type coercion on assignment and mixed-type arithmetic
- Division-by-zero detection with near-zero float threshold (`1e-10`)
- All `printf()` output collected in a list for testability

### Error Hierarchy

The interpreter uses a structured exception hierarchy with precise source locations:

```
CLiteError (base)
├── LexerError      — invalid characters, malformed literals, unclosed strings
├── ParserError     — syntax errors, unexpected tokens, unmatched delimiters
└── SemanticError   — undefined variables, uninitialized access, division by zero,
                      duplicate declarations in same scope
```

All errors include `line`, `column`, and a human-readable `message`:

```
SemanticError at line 5, column 1: Undefined variable 'y'
ParserError at line 3, column 12: Expected ')' after condition
LexerError at line 1, column 6: Unexpected character '@'
```

### AST Node Reference

The full AST hierarchy is defined in `src/ast.py`:

```
ASTNode (abstract base)
│
├── Program                — root node: declarations[] + statements[]
│
├── Declaration            — variable declaration: type_specifier identifier ;
├── Assignment             — variable assignment: identifier = expression ;
├── IfStatement            — conditional: if (expr) stmt [else stmt]
├── Block                  — scoped block: { declaration | statement }
├── PrintfCall             — output: printf(expression) ;
├── EmptyStatement         — no-op: ;
│
├── BinaryOp              — binary expression: left op right
├── UnaryOp               — unary expression: op operand
├── NumberLiteral         — numeric constant: int or float
└── Identifier            — variable reference: name
```

All nodes are **immutable** (`@dataclass(frozen=True)`) and carry source location (`line`, `column`).

### Token Type Reference

Defined in `src/token.py`:

| Category | Tokens |
|----------|--------|
| **Keywords** | `int`, `float`, `if`, `else`, `printf` |
| **Literals** | `INT_LITERAL`, `FLOAT_LITERAL`, `STRING_LITERAL` |
| **Identifiers** | `IDENTIFIER` |
| **Arithmetic** | `+`, `-`, `*`, `/` |
| **Relational** | `>`, `<`, `==` |
| **Assignment** | `=` |
| **Delimiters** | `(`, `)`, `{`, `}`, `;` |
| **Meta** | `COMMENT`, `EOF` |

---

## Directory Layout

```
C-Lite-Interpreter/
├── cli.py                  # Command-line interface entry point
├── repl.py                 # Interactive REPL entry point
├── requirements.txt        # Development dependencies (pytest)
├── LICENSE                 # MIT License
│
├── src/                    # Interpreter source code
│   ├── __init__.py         #   Public API exports
│   ├── token.py            #   Token and TokenType definitions
│   ├── lexer.py            #   Lexical analyzer (scanner)
│   ├── ast.py              #   AST node definitions + Visitor base class
│   ├── parser.py           #   Recursive descent parser
│   ├── symbol_table.py     #   Stack-based symbol table with scoping
│   ├── interpreter.py      #   Tree-walking evaluator (Visitor pattern)
│   └── errors.py           #   Exception hierarchy (CLiteError family)
│
├── tests/                  # Test suite (293 tests)
│   ├── __init__.py
│   ├── test_lexer.py       #   Lexer tests (33 tests)
│   ├── test_parser.py      #   Parser tests (64 tests)
│   ├── test_interpreter.py #   Interpreter tests (46 tests)
│   ├── test_ast.py         #   AST structure tests (57 tests)
│   ├── test_symbol_table.py#   Symbol table tests (38 tests)
│   ├── test_cli.py         #   CLI integration tests (24 tests)
│   └── test_repl.py        #   REPL integration tests (31 tests)
│
├── examples/               # Example C-Lite programs
│   ├── hello.clt           #   Basic variable and printf
│   ├── arithmetic.clt      #   Arithmetic operations
│   ├── control_flow.clt    #   if-else branching
│   ├── float_operations.clt#   Floating-point arithmetic
│   ├── nested_scopes.clt   #   Nested block scoping
│   └── type_coercion.clt   #   Implicit type conversion
│
└── docs/                   # Design documentation
    ├── grammar.ebnf        #   Formal EBNF grammar specification
    ├── first_follow_sets.md#   FIRST/FOLLOW set analysis
    ├── grammar_validation.md#  Grammar validation examples & parse trees
    └── design_decisions.md #   Architectural rationale (18 decisions)
```

---

## Usage

### CLI Reference

```
usage: cli.py [-h] [-e CODE] [-v] [--version] [source_file]

C-Lite Interpreter

positional arguments:
  source_file           C-Lite source file (.clt extension)

optional arguments:
  -h, --help            show this help message and exit
  -e CODE, --execute CODE
                        Execute C-Lite code directly from command line
  -v, --verbose         Show detailed phase information
  --version             show program's version number and exit
```

**Execute a file:**

```bash
python cli.py examples/hello.clt
# Output: 42
```

**Execute inline code:**

```bash
python cli.py -e "int x; x = 10; printf(x);"
# Output: 10
```

**Verbose mode** (shows lexer tokens, AST, and execution details):

```bash
python cli.py -v examples/control_flow.clt
```

**Supported file extensions:** `.clt` (recommended), `.c`, `.txt`

### REPL Commands

Launch the REPL with `python repl.py`:

| Command | Description |
|---------|-------------|
| `:help` | Show help message with language reference |
| `:vars` | Display all variables in the current symbol table |
| `:tokens` | Show tokens from last parsed input |
| `:ast` | Show AST from last parsed input |
| `:verbose` | Enable verbose mode (show all phases) |
| `:quiet` | Disable verbose mode |
| `:clear` / `:reset` | Clear interpreter state (reset all variables) |
| `:version` | Show version information |
| `:exit` / `:quit` | Exit REPL (also `Ctrl+D`) |

**REPL features:**
- **Multi-line input** -- automatically detects unclosed braces/parentheses and waits for continuation
- **State persistence** -- variables declared in one command are available in subsequent commands
- **Output isolation** -- each command shows only its own `printf` output
- **Error recovery** -- errors do not terminate the session; type the next command to continue

**Example session:**

```
>>> int x;
>>> int y;
>>> x = 10;
>>> y = x * 2;
>>> printf(y);
20
>>> if (y > 15) { printf(1); } else { printf(0); }
1
>>> :vars
Variables in scope:
  Scope 0:
    x (int) = 10
    y (int) = 20
>>> :clear
Interpreter state cleared.
```

### Programmatic API

The interpreter components can be used as a Python library:

```python
from src.lexer import Lexer
from src.parser import Parser
from src.interpreter import Interpreter

# Tokenize
source = "int x; x = 42; printf(x);"
tokens = list(Lexer(source).tokenize())

# Parse
ast = Parser(tokens).parse()

# Execute
interpreter = Interpreter()
output = interpreter.execute(ast)
print(output)  # [42]
```

**Accessing the symbol table after execution:**

```python
interpreter = Interpreter()
interpreter.execute(ast)

# Inspect variables
symbol = interpreter.symbol_table.lookup("x")
print(symbol.name, symbol.var_type, symbol.value)  # x int 42
```

---

## Examples

### Hello World

```c
// examples/hello.clt
int x;
x = 42;
printf(x);
```

```
$ python cli.py examples/hello.clt
42
```

### Arithmetic with Type Coercion

```c
// examples/type_coercion.clt
int a;
float b;
float result;

a = 10;
b = 3.5;

result = a + b;    // int + float → float
printf(result);    // Output: 13.5

a = b;             // float → int truncation
printf(a);         // Output: 3
```

```
$ python cli.py examples/type_coercion.clt
13.5
3
```

### Control Flow

```c
// examples/control_flow.clt
int x;
x = 5;

if (x > 3) {
    printf(x);         // Output: 5
} else {
    x = 1;
    printf(x);
}
```

```
$ python cli.py examples/control_flow.clt
5
```

### Nested Scopes

```c
// examples/nested_scopes.clt
int x;
x = 10;

{
    int y;
    y = 20;

    {
        int z;
        z = x + y;    // accesses outer variables
        printf(z);     // Output: 30
    }
}
```

```
$ python cli.py examples/nested_scopes.clt
30
```

### Float Operations

```c
// examples/float_operations.clt
float x;
float y;
float result;

x = 3.14;
y = 2.86;

result = x + y;
printf(result);    // Output: 6

result = x * y;
printf(result);    // Output: 8.9804
```

```
$ python cli.py examples/float_operations.clt
6
8.9804
```

---

## Testing

### Running the Test Suite

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run a specific test module
python -m pytest tests/test_lexer.py

# Run a specific test class
python -m pytest tests/test_interpreter.py::TestBooleanSemantics

# Run a single test
python -m pytest tests/test_parser.py::TestASTStructuralValidation::test_full_tree_validation_precedence

# Run with short traceback
python -m pytest --tb=short -q
```

### Test Matrix

| Module | Tests | Description |
|--------|------:|-------------|
| `test_lexer.py` | 33 | Token recognition, source location tracking, numeric/string literals, comments, error handling, boundary/stress tests |
| `test_parser.py` | 64 | Syntax error detection, deep nesting, float edge cases, AST structural validation, recovery behavior, operator precedence, fuzzing, EOF edge cases, performance |
| `test_interpreter.py` | 46 | Boolean semantics, relational evaluation, type coercion, uninitialized variables, nested blocks, expression stress, control flow, printf ordering, division edge cases, variable lifetime, isolation |
| `test_ast.py` | 57 | Expression tree composition, block scope nesting, if-statement traversal, visitor contract, equality comparison, immutability, program node edge cases, location integrity |
| `test_symbol_table.py` | 38 | Type enforcement, variable shadowing, deep nesting (50-200 levels), scope re-entrancy, memory integrity, error messages, performance (10,000 declarations), float precision |
| `test_cli.py` | 24 | File execution, inline code, verbose mode, error reporting, file encoding, version flag, edge cases |
| `test_repl.py` | 31 | Statement execution, multi-line input, state persistence, REPL commands, error recovery, output isolation |
| **Total** | **293** | **All passing** |

### Test Categories

The test suite systematically covers the following categories:

**Lexer Tests:**
- Token recognition (keywords, operators, delimiters)
- Source location tracking (line/column across multi-line input)
- Identifier validation (C naming rules, edge cases)
- Numeric literal parsing (integers, floats, edge cases like `.5`, `3.`, errors like `1.2.3`)
- String literal parsing (escape sequences, unclosed strings)
- Comment handling (single-line `//`, empty comments, comments at EOF)
- Error detection (invalid characters with precise location)
- Boundary/stress tests (1000-char identifiers, large integers, repeated operators)

**Parser Tests:**
- Negative path combinatorics (trailing operators, unclosed parens/braces, double operators)
- Boundary conditions (50-level nesting, 1000-term expression chains)
- Float literal behavior (leading/trailing dot, zero, double-dot errors)
- AST structural validation (full tree topology for complex expressions)
- Error recovery behavior (fail-fast, error location quality)
- Declaration rules (missing identifier/semicolon, interleaving with statements)
- Operator precedence (relational vs. additive vs. multiplicative)
- Fuzzing (random characters, whitespace-only, empty input, semicolons-only)
- EOF edge cases (truncated if/printf/assignment/declaration)
- Performance (parsing time scaling, memory usage)

**Interpreter Tests:**
- Boolean semantics (C-style truthiness: `0`, `0.0` = false)
- Relational/equality evaluation (return `1`/`0` as `int`)
- Mixed-type comparisons (int vs. float coercion)
- Type assignment violations (float->int truncation, int->float promotion)
- Uninitialized variable detection
- State integrity after exceptions
- Deep nested block execution (50-100 levels)
- Large expression stress (100-1000 term chains)
- Sequential control flow integrity
- Printf ordering guarantee
- Division edge cases (int/int, float/int, division by zero)
- Variable lifetime after block exit
- Symbol table isolation between runs

---

## Design Decisions

The project documents **18 design decisions** in [`docs/design_decisions.md`](docs/design_decisions.md). 

Key highlights:

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Lexer implementation | Hand-written DFA | Educational transparency, explicit error control |
| 2 | EOF handling | Explicit EOF token | Simplifies parser termination, aligns with FOLLOW sets |
| 4 | Parsing strategy | LL(1) recursive descent | Educational value, easy debugging, no backtracking |
| 5 | Precedence encoding | 4-level expression hierarchy | Matches C semantics, correct AST construction |
| 7 | Interpretation pattern | Visitor pattern | Separates traversal from execution, extensible |
| 8 | Symbol table structure | Stack of scope dictionaries | Efficient enter/exit, matches block scoping |
| 9 | Truthiness | C-style (0 = false) | Matches C semantics |
| 10 | Type coercion | Implicit (int<->float) | Matches C semantics for assignment and arithmetic |
| 11 | Uninitialized variables | Raise SemanticError | Prevents undefined behavior (stricter than C) |
| 12 | Integer division | Floor division for int/int | Matches C semantics |
| 13 | Error strategy | Fail-fast (first error only) | Simpler implementation, standard for educational compilers |
| 15 | Testing approach | Test-driven development (TDD) | Robustness, 293 tests across all components |

---

## Known Limitations

| Limitation | Description | Mitigation |
|------------|-------------|------------|
| **Recursion depth** | Python's default recursion limit (~1000) can be exceeded by deeply nested expressions (>500 levels) | Increase limit with `sys.setrecursionlimit()` or restructure deeply nested code |
| **No loop constructs** | `while` and `for` loops are not supported (per language specification) | Future extension possible |
| **No functions** | User-defined functions are not supported | Only built-in `printf()` is available |
| **No arrays/pointers** | Aggregate types are not supported | Future extension possible |
| **Single-error reporting** | Parser stops on first syntax error (fail-fast) | Re-run after fixing each error |
| **No string variables** | String literals are only supported as `printf()` arguments | Strings cannot be stored in variables |

---

## Performance

| Component | Time Complexity | Space Complexity |
|-----------|-----------------|------------------|
| Lexer | `O(n)` single-pass | `O(n)` token stream |
| Parser | `O(n)` single-pass | `O(n)` AST |
| Interpreter | `O(n)` tree traversal | `O(s)` symbol table (`s` = scope depth) |
| Symbol table lookup | `O(d)` per lookup (`d` = nesting depth) | `O(v)` (`v` = total variables) |

**Benchmarks (tested on the project test suite):**
- 1,000-term expression chain: parses and evaluates in < 15 seconds
- 10,000 variable declarations: symbol table handles in < 2 seconds
- 50-200 levels of nested scopes: no stack overflow, completes in milliseconds
- Full 293-test suite: completes in ~2.5 seconds

---

## Contributing

Contributions are welcome. Please follow these guidelines:

1. **Fork** the repository and create a feature branch.
2. **Write tests** for any new functionality (maintain 100% test pass rate).
3. **Follow existing code style** -- type hints, docstrings, consistent naming.
4. **Run the full test suite** before submitting:
   ```bash
   python -m pytest -v
   ```
5. **Submit a pull request** with a clear description of the changes.

### Development Setup

```bash
git clone https://github.com/ChethiyaB/C-Lite-Interpreter.git
cd C-Lite-Interpreter
pip install -r requirements.txt
python -m pytest  # Verify all 293 tests pass
```

---

## License

This project is licensed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

```
MIT License
Copyright (c) 2026 Chethiya Bandara
```

- **References:**
  - Sebesta, R.W. -- *Concepts of Programming Languages* (12th Edition)
  - Scott, M.L. -- *Programming Language Pragmatics* (4th Edition)
