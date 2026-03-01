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