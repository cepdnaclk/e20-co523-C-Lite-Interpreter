## Lexical Analysis Design

### Tokenization Strategy
- **Hand-written DFA:** Chosen over regex libraries for educational transparency and precise error control.
- **Streaming Generator:** `tokenize()` yields tokens lazily to support large files without loading all tokens into memory.

### Error Handling
- **Fail-Fast:** Lexer raises `LexerError` immediately on invalid characters.
- **Location Tracking:** Every token and error includes 1-indexed line/column for precise reporting.

### Trade-offs
- **Performance:** O(n) single-pass scanning.
- **Extensibility:** Adding new tokens requires updating `TokenType` enum and `tokenize()` dispatch logic.
- **Unicode:** Currently ASCII-only per C-Lite spec. Unicode support would require UTF-8 decoding logic.

## Symbol Table Design

### Design Decisions:
- Stack-based nested scopes (matches C block scoping)
- Type information stored per variable (int/float)
- Shadowing allowed (inner scope can redeclare same name)
- Type enforcement on assignment (static typing)
- Implicit coercion rules (int←float truncates, float←int promotes)

## Interpreter Design

### Design Decisions:
- Visitor Pattern for AST traversal (separates execution from structure)
- Dynamic type checking at assignment (int/float validation)
- Type coercion for mixed arithmetic (int + float → float)
- printf() outputs to console (Project Spec §3: Standard I/O)