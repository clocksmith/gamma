# Archive Format `A2F1` (BITS Experiment Card A2)

This specification completely defines the serialized archive bytes for all four arms of
Experiment Card A2 (Flat BITS, Context-Coded AST, Learned Depth-1 Frames, and Learned
Recursive Frames). An independent decoder (`independent_decode.py` + `js_normalize_ast.mjs`)
reconstructs every normalized JavaScript program byte-for-byte from the archive bytes alone.

## 1. Primitives

- **Varint (`uvarint`)**: Unsigned LEB128 (7 bits per byte, least-significant group first; MSB=1
  on all bytes except the last).
- **Length-prefixed UTF-8 string (`ustr`)**: `uvarint(len(utf8_bytes))` followed by `utf8_bytes`.
- **32-bit Integer Arithmetic Coder (`AC32`)**:
  - State: `low = 0`, `high = 0xFFFFFFFF`, `HALF = 0x80000000`, `QUARTER = 0x40000000`,
    `THREE_Q = 0xC0000000`, `MAX_TOTAL = 16384`.
  - Probability table for alphabet size `K`: `K` positive integer weights `w[0..K-1]` with
    `sum(w) <= 16384`. Cumulative counts `cum[0] = 0`, `cum[i+1] = cum[i] + w[i]`, `total = cum[K]`.
  - Encoded bitstream is written MSB-first within each byte, flushed with one disambiguating
    bit plus pending bits, and padded with trailing zero bits to a whole byte.
  - Table serialization: `K` weights encoded as `uvarint(w[i] - 1)` for `i = 0..K-1`.

## 2. Common Envelope

| Field | Encoding | Meaning |
| --- | --- | --- |
| `Magic` | 4 bytes `A2F1` | Archive format magic |
| `CodecKind` | 1 byte | `0` = Flat BITS (Arm 1), `1` = Context-Coded AST + Frames (Arms 2, 3, 4) |
| `MaxDepth` | 1 byte | Maximum frame nesting depth (`0` for Arms 1 & 2, `1` for Arm 3, `3` for Arm 4) |

## 3. `CodecKind = 0` (Arm 1 — Flat BITS)

1. `n = uvarint`: dictionary entry count.
2. Dictionary: `n` entries, each `1 byte length (1..32)` + `length` raw bytes.
3. Symbol table: `n + 2` weights (`0..n-1` = entries, `n` = `ESC`, `n+1` = `EOF`).
4. **End of frozen header** (`header_bytes` = offset here).
5. `file_count = uvarint`.
6. `payload`: `AC32` bitstream of `file_count` files. Each file emits symbols until `EOF`.
   An `ESC` symbol is followed by 1 uniform raw byte (alphabet 256, all weights = 1).

## 4. `CodecKind = 1` (Arms 2, 3, 4 — Context-Coded AST + Optional Recursive Frames)

### 4.1 Literal & Identifier Pools
Five pools serialized in fixed order, each as `uvarint(count)` followed by `count` `ustr` items:
1. `prop_pool` (property identifiers)
2. `free_id_pool` (free/global identifiers)
3. `bind_name_pool` (non-canonical declaration/label identifiers)
4. `num_pool` (numeric literal raw strings)
5. `str_pool` (string literal UTF-8 contents)

### 4.2 Base Context Probability Tables
Serialized in exact canonical order (fixed alphabet sizes defined in section 4.5):
- `FILE_MODE` (2: `AST`, `RAW_FALLBACK`)
- 10 expression-tag contexts (`EXPR_STMT`, `EXPR_TEST`, `EXPR_INIT`, `EXPR_ARG`,
  `EXPR_CALLEE`, `EXPR_LHS`, `EXPR_OBJ`, `EXPR_PROP_IDX`, `EXPR_BIN_L`, `EXPR_BIN_R`,
  `EXPR_OTHER` — 11 contexts total), each with `35` base symbols when `MaxDepth == 0`,
  or `36` symbols (`35 = USE_EXPR_FRAME`) when `MaxDepth >= 1`.
- 3 statement-tag contexts (`STMT_TOP`, `STMT_BLOCK`, `STMT_BRANCH`), each with `25` base
  symbols when `MaxDepth == 0`, or `26` symbols (`25 = USE_STMT_FRAME`) when `MaxDepth >= 1`.
- `PAT_DECL` (6), `PAT_PARAM` (6), `REG_SLOT` (8), `VAR_KIND` (3), `BIN_OP` (22),
  `LOG_OP` (3), `UN_OP` (7), `UPD_OP` (4), `ASN_OP` (16), `LIST_LEN_STMT` (17),
  `LIST_LEN_ARGS` (9), `LIST_LEN_DECL` (4), `OPT_ELSE` (2), `OPT_INIT` (2),
  `OPT_RET_ARG` (2), `OPT_CHAIN` (2), `OPT_FLAG` (2), `FOR_INIT_KIND` (3),
  `OBJ_PROP_KIND` (5), `ARROW_FLAGS` (4), `FUNC_FLAGS` (4), `CLASS_MEM_KIND` (4),
  `EXPORT_DEF_KIND` (3), `IMPORT_SPEC_KIND` (3), `META_KIND` (2), `INT_ESC_NIBBLE` (17),
  `PROP_NAME` (`len(prop_pool) + 1`), `FREE_ID` (`len(free_id_pool) + 1`),
  `BIND_NAME` (`len(bind_name_pool) + 1`), `NUM_LIT` (`len(num_pool) + 1`),
  `STR_LIT` (`len(str_pool) + 1`), `INLINE_BYTE` (256).

### 4.3 Frame Tables & Recursive Frame Definitions (present iff `MaxDepth >= 1`)
1. `F_E = uvarint` (expression frame count), `F_S = uvarint` (statement frame count).
2. If `F_E > 0`: `EXPR_FRAME_ID` table (`F_E` weights).
3. If `F_S > 0`: `STMT_FRAME_ID` table (`F_S` weights).
4. `REG_SHIFT` table (8 weights for cyclic shifts `0..7`).
5. `DEF_MODE` table (present iff `MaxDepth >= 1`): `2` weights (`NODE`, `HOLE`) when `MaxDepth == 1`,
   or `3` weights (`NODE`, `HOLE`, `DEF_CALL`) when `MaxDepth >= 2`. Used to arithmetic-code
   frame-definition node choices cleanly without uniform-mode waste.
6. `def_order`: `F_E + F_S` frame records encoded via a single `AC32` byte-block
   (`uvarint(def_bytes_len)` + `def_bytes`):
   - Each frame record starts with 1 bit/symbol (`group`: `0 = EXPR`, `1 = STMT`, uniform 2-way)
     followed by its template tree encoded using the base AST context tables + `DEF_MODE`:
     - At root (`allow_hole = false`) when `MaxDepth == 1` or no eligible earlier frames: always `NODE` (0 mode bits).
     - At root when `MaxDepth >= 2` and eligible earlier frames exist: binary choice `NODE` vs `DEF_CALL` using `[DEF_MODE[0], DEF_MODE[2]]`.
     - At non-root (`allow_hole = true`) when `MaxDepth == 1` or no eligible earlier frames: binary choice `NODE` vs `HOLE` using `[DEF_MODE[0], DEF_MODE[1]]`.
     - At non-root when `MaxDepth >= 2` and eligible earlier frames exist: 3-way choice `NODE` / `HOLE` / `DEF_CALL` using `DEF_MODE`.
     - On `DEF_CALL`: uniform index `j` over previously defined frames of the matching `group`
       whose `def_depth < MaxDepth`, followed by uniform `sub_shift in 0..7` if `frame_j.has_regs`,
       followed by `len(frame_j.holes)` child argument templates in `frame_j`'s hole contexts.
   - **Strict decoder validation**:
     - Count of decoded `EXPR` frames must equal `F_E`, `STMT` frames must equal `F_S`.
     - Every `DEF_CALL_FRAME` must reference an already-defined frame `j` of matching `group`
       with `frame_j.def_depth < MaxDepth`.
     - Computed `def_depth = 1` (if no sub-frame call) or `1 + max(frame_j.def_depth)` MUST
       satisfy `1 <= def_depth <= MaxDepth`.

### 4.4 Payload Section
- **End of frozen header** (`header_bytes` = offset here).
- `file_count = uvarint`.
- `payload`: `AC32` bitstream of `file_count` files:
  - Each file starts with `FILE_MODE`:
    - `RAW_FALLBACK (1)`: `length` (coded via `INT_ESC_NIBBLE`) + `length` bytes via `INLINE_BYTE`.
    - `AST (0)`: `Program` statement list (`LIST_LEN_STMT` + statements in `STMT_TOP` context)
      maintaining the deterministic scope-register stack `env` and `canon_counter`.
  - On `USE_EXPR_FRAME` (legal ONLY in `EXPR_*` contexts when `MaxDepth >= 1` and `F_E > 0`)
    or `USE_STMT_FRAME` (legal ONLY in `STMT_*` contexts when `MaxDepth >= 1` and `F_S > 0`):
    - Read `frame_id` from `EXPR_FRAME_ID` / `STMT_FRAME_ID`.
    - If `frame.has_regs`: read `shift` from `REG_SHIFT` (`0..7`), else `shift = 0`.
    - Expand `frame` at `depth = 1` with cyclic register shift `shift`.
    - Any nested `DEF_CALL_FRAME(sub, sub_shift, args)` expands `sub` at
      `effective_shift = (cur_shift + sub_shift) % 8` and `depth + 1`.
    - **Strict runtime validation**: `depth > MaxDepth`, invalid `frame_id`, mismatched `group`,
      or resolved register index `(r + cur_shift) % 8 >= len(env)` MUST raise `FormatError`.
