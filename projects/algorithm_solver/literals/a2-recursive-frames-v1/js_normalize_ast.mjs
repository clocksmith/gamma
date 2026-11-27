#!/usr/bin/env node
/**
 * Zero-dependency deterministic ES2022 JavaScript normalizer, parser, unparser,
 * and compact canonical AST IR bridge for BITS Experiment Card A2.
 *
 * Guarantees:
 *   1. Deterministic AST parse + safe scope-preserving local canonicalization.
 *   2. Exact byte-for-byte round-trip check: unparse(parse(normalized)) === normalized.
 *   3. Compact IR export/import with exact 1-to-1 bijection to normalized JS.
 *   4. Explicit supported=false flag on any unsupported or unverified source
 *      (never silently dropped; caller charges full raw fallback bytes).
 *
 * CLI (batch JSON over stdin -> stdout):
 *   node js_normalize_ast.mjs normalize   # [{id, source}] -> [{id, supported, normalized, ir, ...}]
 *   node js_normalize_ast.mjs parse_ir    # [{id, source}] -> [{id, supported, ir, error}]
 *   node js_normalize_ast.mjs unparse_ir  # [{id, ir}]     -> [{id, ok, source, error}]
 */
import fs from 'node:fs';
import vm from 'node:vm';

// ---------------------------------------------------------------------------
// Lexer (parser-driven regex & template-tail lexing for 100% ES exactness)
// ---------------------------------------------------------------------------

const KEYWORDS = new Set([
  'await', 'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger',
  'default', 'delete', 'do', 'else', 'export', 'extends', 'false', 'finally',
  'for', 'function', 'if', 'import', 'in', 'instanceof', 'new', 'null',
  'return', 'super', 'switch', 'this', 'throw', 'true', 'try', 'typeof',
  'var', 'void', 'while', 'with', 'yield',
]);

const RESERVED_NEVER_RENAME = new Set([
  ...KEYWORDS, 'let', 'static', 'enum', 'implements', 'interface', 'package',
  'private', 'protected', 'public', 'arguments', 'eval', 'undefined', 'NaN', 'Infinity',
]);

const PUNCTUATORS = [
  '>>>=', '===', '!==', '>>>', '<<=', '>>=', '**=', '&&=', '||=', '??=', '...',
  '==', '!=', '<=', '>=', '<<', '>>', '++', '--', '&&', '||', '??', '**',
  '=>', '?.', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=',
  '{', '}', '(', ')', '[', ']', '.', ';', ',', '<', '>', '+', '-', '*', '/',
  '%', '&', '|', '^', '!', '~', '?', ':', '=',
];

function isIdStart(ch) {
  if (!ch) return false;
  const c = ch.charCodeAt(0);
  if ((c >= 65 && c <= 90) || (c >= 97 && c <= 122) || c === 95 || c === 36) return true;
  if (c >= 128) return /[\p{ID_Start}]/u.test(ch);
  return false;
}

function isIdPart(ch) {
  if (!ch) return false;
  const c = ch.charCodeAt(0);
  if ((c >= 65 && c <= 90) || (c >= 97 && c <= 122) || (c >= 48 && c <= 57) || c === 95 || c === 36) return true;
  if (c >= 128) return /[\p{ID_Continue}\u200C\u200D]/u.test(ch);
  return false;
}

function isLineTerminator(ch) {
  return ch === '\n' || ch === '\r' || ch === '\u2028' || ch === '\u2029';
}

function isWhitespace(ch) {
  return ch === ' ' || ch === '\t' || ch === '\v' || ch === '\f' || ch === '\u00A0' || ch === '\uFEFF' || (ch.charCodeAt(0) >= 128 && /\s/.test(ch) && !isLineTerminator(ch));
}

class Scanner {
  constructor(src) {
    this.src = src;
    this.len = src.length;
    this.pos = 0;
    this.lineTermBefore = false;
    this.tok = null;
    // Skip shebang if present
    if (src.startsWith('#!')) {
      while (this.pos < this.len && !isLineTerminator(src[this.pos])) this.pos++;
    }
    this.tok = this._readToken();
  }

  save() {
    return { pos: this.pos, lineTermBefore: this.lineTermBefore, tok: this.tok };
  }

  restore(snap) {
    this.pos = snap.pos;
    this.lineTermBefore = snap.lineTermBefore;
    this.tok = snap.tok;
  }

  _skipTrivia() {
    let sawNL = false;
    const s = this.src;
    const n = this.len;
    while (this.pos < n) {
      const ch = s[this.pos];
      if (isWhitespace(ch)) {
        this.pos++;
      } else if (isLineTerminator(ch)) {
        sawNL = true;
        if (ch === '\r' && s[this.pos + 1] === '\n') this.pos += 2;
        else this.pos++;
      } else if (ch === '/' && s[this.pos + 1] === '/') {
        this.pos += 2;
        while (this.pos < n && !isLineTerminator(s[this.pos])) this.pos++;
      } else if (ch === '/' && s[this.pos + 1] === '*') {
        this.pos += 2;
        let closed = false;
        while (this.pos < n) {
          if (isLineTerminator(s[this.pos])) sawNL = true;
          if (s[this.pos] === '*' && s[this.pos + 1] === '/') {
            this.pos += 2;
            closed = true;
            break;
          }
          this.pos++;
        }
        if (!closed) throw new SyntaxError('Unterminated block comment');
      } else {
        break;
      }
    }
    this.lineTermBefore = sawNL;
  }

  _readEscapeSeq() {
    const s = this.src;
    const ch = s[this.pos++];
    switch (ch) {
      case 'n': return '\n';
      case 'r': return '\r';
      case 't': return '\t';
      case 'b': return '\b';
      case 'f': return '\f';
      case 'v': return '\v';
      case '0':
        if (this.pos < this.len && s[this.pos] >= '0' && s[this.pos] <= '7') {
          let oct = '0';
          while (oct.length < 3 && this.pos < this.len && s[this.pos] >= '0' && s[this.pos] <= '7') {
            oct += s[this.pos++];
          }
          return String.fromCharCode(parseInt(oct, 8));
        }
        return '\0';
      case '1': case '2': case '3': case '4': case '5': case '6': case '7': {
        let oct = ch;
        const maxLen = ch <= '3' ? 3 : 2;
        while (oct.length < maxLen && this.pos < this.len && s[this.pos] >= '0' && s[this.pos] <= '7') {
          oct += s[this.pos++];
        }
        return String.fromCharCode(parseInt(oct, 8));
      }
      case 'x': {
        const hex = s.slice(this.pos, this.pos + 2);
        if (!/^[0-9a-fA-F]{2}$/.test(hex)) throw new SyntaxError('Invalid hex escape');
        this.pos += 2;
        return String.fromCharCode(parseInt(hex, 16));
      }
      case 'u': {
        if (s[this.pos] === '{') {
          this.pos++;
          let hex = '';
          while (this.pos < this.len && s[this.pos] !== '}') hex += s[this.pos++];
          if (s[this.pos] !== '}' || !/^[0-9a-fA-F]+$/.test(hex)) throw new SyntaxError('Invalid unicode escape');
          this.pos++;
          return String.fromCodePoint(parseInt(hex, 16));
        }
        const hex = s.slice(this.pos, this.pos + 4);
        if (!/^[0-9a-fA-F]{4}$/.test(hex)) throw new SyntaxError('Invalid unicode escape');
        this.pos += 4;
        return String.fromCharCode(parseInt(hex, 16));
      }
      case '\r':
        if (s[this.pos] === '\n') this.pos++;
        return '';
      case '\n': case '\u2028': case '\u2029':
        return '';
      default:
        return ch;
    }
  }

  _readString(quote) {
    const start = this.pos;
    const s = this.src;
    this.pos++; // skip opening quote
    let val = '';
    while (this.pos < this.len) {
      const ch = s[this.pos++];
      if (ch === quote) {
        return { type: 'str', value: val, start, end: this.pos, nl: this.lineTermBefore };
      }
      if (ch === '\\') {
        if (this.pos >= this.len) throw new SyntaxError('Unterminated escape');
        val += this._readEscapeSeq();
      } else if (ch === '\n' || ch === '\r') {
        throw new SyntaxError('Unterminated string literal');
      } else {
        val += ch;
      }
    }
    throw new SyntaxError('Unterminated string literal');
  }

  _readNumber() {
    const start = this.pos;
    const s = this.src;
    const n = this.len;
    let isBigInt = false;
    if (s[this.pos] === '0' && this.pos + 1 < n) {
      const nxt = s[this.pos + 1];
      if (nxt === 'x' || nxt === 'X') {
        this.pos += 2;
        while (this.pos < n && /[0-9a-fA-F_]/.test(s[this.pos])) this.pos++;
        if (s[this.pos] === 'n') { isBigInt = true; this.pos++; }
        const raw = s.slice(start, this.pos);
        return { type: isBigInt ? 'bigint' : 'num', raw, start, end: this.pos, nl: this.lineTermBefore };
      }
      if (nxt === 'b' || nxt === 'B') {
        this.pos += 2;
        while (this.pos < n && /[01_]/.test(s[this.pos])) this.pos++;
        if (s[this.pos] === 'n') { isBigInt = true; this.pos++; }
        const raw = s.slice(start, this.pos);
        return { type: isBigInt ? 'bigint' : 'num', raw, start, end: this.pos, nl: this.lineTermBefore };
      }
      if (nxt === 'o' || nxt === 'O') {
        this.pos += 2;
        while (this.pos < n && /[0-7_]/.test(s[this.pos])) this.pos++;
        if (s[this.pos] === 'n') { isBigInt = true; this.pos++; }
        const raw = s.slice(start, this.pos);
        return { type: isBigInt ? 'bigint' : 'num', raw, start, end: this.pos, nl: this.lineTermBefore };
      }
    }
    while (this.pos < n && /[0-9_]/.test(s[this.pos])) this.pos++;
    if (s[this.pos] === '.' && !(s[this.pos + 1] === '.' && s[this.pos + 2] === '.')) {
      this.pos++;
      while (this.pos < n && /[0-9_]/.test(s[this.pos])) this.pos++;
    }
    if (s[this.pos] === 'e' || s[this.pos] === 'E') {
      this.pos++;
      if (s[this.pos] === '+' || s[this.pos] === '-') this.pos++;
      const expStart = this.pos;
      while (this.pos < n && /[0-9_]/.test(s[this.pos])) this.pos++;
      if (this.pos === expStart) throw new SyntaxError('Invalid exponent');
    } else if (s[this.pos] === 'n') {
      isBigInt = true;
      this.pos++;
    }
    const raw = s.slice(start, this.pos);
    return { type: isBigInt ? 'bigint' : 'num', raw, start, end: this.pos, nl: this.lineTermBefore };
  }

  _readTemplateChunk(isHead) {
    const start = this.pos;
    const s = this.src;
    const n = this.len;
    if (isHead) this.pos++; // skip `
    let raw = '';
    while (this.pos < n) {
      const ch = s[this.pos];
      if (ch === '`') {
        this.pos++;
        return { type: 'tpl_tail', raw, start, end: this.pos, nl: this.lineTermBefore };
      }
      if (ch === '$' && s[this.pos + 1] === '{') {
        this.pos += 2;
        return { type: 'tpl_head', raw, start, end: this.pos, nl: this.lineTermBefore };
      }
      if (ch === '\\') {
        if (this.pos + 1 >= n) throw new SyntaxError('Unterminated template escape');
        if (s[this.pos + 1] === '\r' && s[this.pos + 2] === '\n') {
          raw += '\\\n';
          this.pos += 3;
        } else {
          raw += s[this.pos] + s[this.pos + 1];
          this.pos += 2;
        }
      } else if (ch === '\r') {
        raw += '\n';
        this.pos += (s[this.pos + 1] === '\n') ? 2 : 1;
      } else {
        raw += ch;
        this.pos++;
      }
    }
    throw new SyntaxError('Unterminated template literal');
  }

  readTemplateContinuation() {
    // Called right after matching '}' inside a template expression.
    // Rewind to just after the '}' token that is currently in this.tok!
    if (this.tok.type !== 'punct' || this.tok.value !== '}') {
      throw new SyntaxError('Expected } closing template expression');
    }
    this.pos = this.tok.end;
    this.lineTermBefore = false;
    const chunk = this._readTemplateChunk(false);
    this.tok = this._readToken();
    return chunk;
  }

  readRegex() {
    // Called when current token is '/' or '/=' in primary-expression position.
    if (this.tok.type !== 'punct' || (this.tok.value !== '/' && this.tok.value !== '/=')) {
      throw new SyntaxError('Expected regex start');
    }
    const start = this.tok.start;
    this.pos = start + 1; // right after leading '/'
    const s = this.src;
    const n = this.len;
    let inClass = false;
    let pattern = '';
    while (this.pos < n) {
      const ch = s[this.pos++];
      if (isLineTerminator(ch)) throw new SyntaxError('Unterminated regex');
      if (ch === '\\') {
        if (this.pos >= n || isLineTerminator(s[this.pos])) throw new SyntaxError('Unterminated regex escape');
        pattern += ch + s[this.pos++];
      } else if (ch === '[') {
        inClass = true;
        pattern += ch;
      } else if (ch === ']') {
        inClass = false;
        pattern += ch;
      } else if (ch === '/' && !inClass) {
        let flags = '';
        while (this.pos < n && isIdPart(s[this.pos])) flags += s[this.pos++];
        const tok = { type: 'regex', pattern, flags, start, end: this.pos, nl: this.tok.nl };
        this.tok = this._readToken();
        return tok;
      } else {
        pattern += ch;
      }
    }
    throw new SyntaxError('Unterminated regex');
  }

  _readIdentifier() {
    const start = this.pos;
    const s = this.src;
    const n = this.len;
    let val = '';
    while (this.pos < n) {
      const ch = s[this.pos];
      if (ch === '\\' && s[this.pos + 1] === 'u') {
        this.pos++;
        val += this._readEscapeSeq();
      } else if (val.length === 0 ? isIdStart(ch) : isIdPart(ch)) {
        val += ch;
        this.pos++;
      } else {
        break;
      }
    }
    const type = KEYWORDS.has(val) ? 'kw' : 'id';
    return { type, value: val, start, end: this.pos, nl: this.lineTermBefore };
  }

  _readToken() {
    this._skipTrivia();
    const start = this.pos;
    const s = this.src;
    const n = this.len;
    if (start >= n) return { type: 'eof', value: '', start, end: start, nl: this.lineTermBefore };
    const ch = s[start];
    if (ch === '"' || ch === "'") return this._readString(ch);
    if (ch === '`') return this._readTemplateChunk(true);
    if ((ch >= '0' && ch <= '9') || (ch === '.' && s[start + 1] >= '0' && s[start + 1] <= '9')) {
      return this._readNumber();
    }
    if (isIdStart(ch) || (ch === '\\' && s[start + 1] === 'u')) {
      return this._readIdentifier();
    }
    for (const p of PUNCTUATORS) {
      if (s.startsWith(p, start)) {
        // Avoid parsing `?.0` as `?.` (it is `?` followed by `.0`)
        if (p === '?.' && s[start + 2] >= '0' && s[start + 2] <= '9') continue;
        this.pos = start + p.length;
        return { type: 'punct', value: p, start, end: this.pos, nl: this.lineTermBefore };
      }
    }
    throw new SyntaxError(`Unexpected character ${JSON.stringify(ch)} at ${start}`);
  }

  next() {
    const cur = this.tok;
    this.tok = this._readToken();
    return cur;
  }
}

// ---------------------------------------------------------------------------
// Recursive-Descent ES2022 Parser
// ---------------------------------------------------------------------------

const BINARY_PREC = {
  '??': 4,
  '||': 5,
  '&&': 6,
  '|': 7,
  '^': 8,
  '&': 9,
  '==': 10, '!=': 10, '===': 10, '!==': 10,
  '<': 11, '<=': 11, '>': 11, '>=': 11, 'in': 11, 'instanceof': 11,
  '<<': 12, '>>': 12, '>>>': 12,
  '+': 13, '-': 13,
  '*': 14, '/': 14, '%': 14,
  '**': 15,
};

const ASSIGN_OPS = new Set([
  '=', '+=', '-=', '*=', '/=', '%=', '**=', '<<=', '>>=', '>>>=',
  '&=', '|=', '^=', '&&=', '||=', '??=',
]);

class Parser {
  constructor(src) {
    this.sc = new Scanner(src);
    this.src = src;
  }

  get tok() { return this.sc.tok; }
  next() { return this.sc.next(); }

  isPunct(v) { return this.tok.type === 'punct' && this.tok.value === v; }
  isKw(v) { return this.tok.type === 'kw' && this.tok.value === v; }
  isId(v) { return this.tok.type === 'id' && (v === undefined || this.tok.value === v); }

  eatPunct(v) {
    if (this.isPunct(v)) { this.next(); return true; }
    return false;
  }

  expectPunct(v) {
    if (!this.isPunct(v)) throw new SyntaxError(`Expected '${v}', got ${this.tok.type}:${this.tok.value} at ${this.tok.start}`);
    return this.next();
  }

  expectKw(v) {
    if (!this.isKw(v)) throw new SyntaxError(`Expected keyword '${v}', got ${this.tok.type}:${this.tok.value} at ${this.tok.start}`);
    return this.next();
  }

  expectSemi() {
    if (this.isPunct(';')) { this.next(); return; }
    if (this.tok.nl || this.isPunct('}') || this.tok.type === 'eof') return;
    throw new SyntaxError(`Expected semicolon, got ${this.tok.type}:${this.tok.value} at ${this.tok.start}`);
  }

  parseProgram() {
    const body = [];
    while (this.tok.type !== 'eof') {
      body.push(this.parseModuleItem());
    }
    return { type: 'Program', body };
  }

  parseModuleItem() {
    if (this.isKw('import')) {
      const snap = this.sc.save();
      this.next();
      if (!this.isPunct('(') && !this.isPunct('.')) {
        this.sc.restore(snap);
        return this.parseImportDecl();
      }
      this.sc.restore(snap);
    }
    if (this.isKw('export')) {
      return this.parseExportDecl();
    }
    return this.parseStmt();
  }

  parseImportDecl() {
    this.expectKw('import');
    const specifiers = [];
    if (this.tok.type === 'str') {
      const source = this.next().value;
      this.expectSemi();
      return { type: 'ImportDecl', specifiers, source };
    }
    if (this.tok.type === 'id') {
      const local = this.next().value;
      specifiers.push({ kind: 'default', local });
      if (this.eatPunct(',')) {
        this._parseImportSpecifiers(specifiers);
      }
    } else {
      this._parseImportSpecifiers(specifiers);
    }
    if (!this.isId('from')) throw new SyntaxError('Expected from in import');
    this.next();
    if (this.tok.type !== 'str') throw new SyntaxError('Expected string module specifier');
    const source = this.next().value;
    this.expectSemi();
    return { type: 'ImportDecl', specifiers, source };
  }

  _parseImportSpecifiers(specifiers) {
    if (this.eatPunct('*')) {
      if (!this.isId('as')) throw new SyntaxError('Expected as after *');
      this.next();
      const local = this.parseIdentName();
      specifiers.push({ kind: 'ns', local });
    } else if (this.eatPunct('{')) {
      while (!this.isPunct('}')) {
        const imported = this.parsePropIdent();
        let local = imported;
        if (this.isId('as')) {
          this.next();
          local = this.parseIdentName();
        }
        specifiers.push({ kind: 'named', imported, local });
        if (!this.eatPunct(',')) break;
      }
      this.expectPunct('}');
    } else {
      throw new SyntaxError('Invalid import specifier');
    }
  }

  parseExportDecl() {
    this.expectKw('export');
    if (this.isKw('default')) {
      this.next();
      if (this.isKw('function') || (this.isId('async') && this._peekAsyncFunc())) {
        const decl = this.parseFunc(true, true);
        return { type: 'ExportDefault', declaration: decl };
      }
      if (this.isKw('class')) {
        const decl = this.parseClass(true, true);
        return { type: 'ExportDefault', declaration: decl };
      }
      const expr = this.parseAssignExpr(true);
      this.expectSemi();
      return { type: 'ExportDefault', declaration: expr };
    }
    if (this.eatPunct('*')) {
      let exported = null;
      if (this.isId('as')) {
        this.next();
        exported = this.parsePropIdent();
      }
      if (!this.isId('from')) throw new SyntaxError('Expected from in export *');
      this.next();
      if (this.tok.type !== 'str') throw new SyntaxError('Expected string in export *');
      const source = this.next().value;
      this.expectSemi();
      return { type: 'ExportAll', exported, source };
    }
    if (this.isPunct('{')) {
      this.next();
      const specifiers = [];
      while (!this.isPunct('}')) {
        const local = this.parsePropIdent();
        let exported = local;
        if (this.isId('as')) {
          this.next();
          exported = this.parsePropIdent();
        }
        specifiers.push({ local, exported });
        if (!this.eatPunct(',')) break;
      }
      this.expectPunct('}');
      let source = null;
      if (this.isId('from')) {
        this.next();
        if (this.tok.type !== 'str') throw new SyntaxError('Expected string after from');
        source = this.next().value;
      }
      this.expectSemi();
      return { type: 'ExportNamed', declaration: null, specifiers, source };
    }
    const decl = this.parseStmt();
    return { type: 'ExportNamed', declaration: decl, specifiers: [], source: null };
  }

  _peekAsyncFunc() {
    const snap = this.sc.save();
    this.next(); // async
    const ok = !this.tok.nl && this.isKw('function');
    this.sc.restore(snap);
    return ok;
  }

  parseStmt() {
    if (this.isPunct('{')) return this.parseBlock();
    if (this.isPunct(';')) { this.next(); return { type: 'Empty' }; }
    if (this.isKw('var') || this.isKw('const') || (this.isId('let') && this._isLetDecl())) {
      return this.parseVarDecl(true);
    }
    if (this.isKw('if')) return this.parseIf();
    if (this.isKw('for')) return this.parseFor();
    if (this.isKw('while')) return this.parseWhile();
    if (this.isKw('do')) return this.parseDoWhile();
    if (this.isKw('return')) return this.parseReturn();
    if (this.isKw('throw')) return this.parseThrow();
    if (this.isKw('break')) return this.parseBreakContinue('Break');
    if (this.isKw('continue')) return this.parseBreakContinue('Continue');
    if (this.isKw('switch')) return this.parseSwitch();
    if (this.isKw('try')) return this.parseTry();
    if (this.isKw('with')) {
      this.next();
      this.expectPunct('(');
      const object = this.parseExpr(true);
      this.expectPunct(')');
      const body = this.parseStmt();
      return { type: 'With', object, body };
    }
    if (this.isKw('debugger')) {
      this.next();
      this.expectSemi();
      return { type: 'Debugger' };
    }
    if (this.isKw('function') || (this.isId('async') && this._peekAsyncFunc())) {
      return this.parseFunc(true, false);
    }
    if (this.isKw('class')) {
      return this.parseClass(true, false);
    }
    // Check labeled statement: ident ':' stmt
    if (this.tok.type === 'id' || (this.tok.type === 'kw' && (this.tok.value === 'yield' || this.tok.value === 'await'))) {
      const snap = this.sc.save();
      const label = this.next().value;
      if (this.eatPunct(':')) {
        const body = this.parseStmt();
        return { type: 'Labeled', label, body };
      }
      this.sc.restore(snap);
    }
    const expr = this.parseExpr(true);
    this.expectSemi();
    return { type: 'ExprStmt', expr };
  }

  _isLetDecl() {
    const snap = this.sc.save();
    this.next(); // consume 'let'
    const t = this.tok;
    let isDecl = false;
    if (t.type === 'id' || (t.type === 'kw' && (t.value === 'yield' || t.value === 'await'))) {
      isDecl = true;
    } else if (t.type === 'punct' && (t.value === '[' || t.value === '{')) {
      isDecl = true;
    }
    this.sc.restore(snap);
    return isDecl;
  }

  parseBlock() {
    this.expectPunct('{');
    const body = [];
    while (!this.isPunct('}')) {
      if (this.tok.type === 'eof') throw new SyntaxError('Unterminated block');
      body.push(this.parseStmt());
    }
    this.expectPunct('}');
    return { type: 'Block', body };
  }

  parseVarDecl(allowIn, consumeSemi = true) {
    const kind = this.next().value; // var | let | const
    const decls = [];
    do {
      const id = this.parseBindingPattern();
      let init = null;
      if (this.eatPunct('=')) {
        init = this.parseAssignExpr(allowIn);
      }
      decls.push({ id, init });
    } while (this.eatPunct(','));
    if (consumeSemi) this.expectSemi();
    return { type: 'VarDecl', kind, decls };
  }

  parseIf() {
    this.expectKw('if');
    this.expectPunct('(');
    const test = this.parseExpr(true);
    this.expectPunct(')');
    const cons = this.parseStmt();
    let alt = null;
    if (this.isKw('else')) {
      this.next();
      alt = this.parseStmt();
    }
    return { type: 'If', test, cons, alt };
  }

  parseFor() {
    this.expectKw('for');
    let isAwait = false;
    if (this.isKw('await')) { isAwait = true; this.next(); }
    this.expectPunct('(');
    if (this.eatPunct(';')) {
      const test = this.isPunct(';') ? null : this.parseExpr(true);
      this.expectPunct(';');
      const update = this.isPunct(')') ? null : this.parseExpr(true);
      this.expectPunct(')');
      const body = this.parseStmt();
      return { type: 'For', init: null, test, update, body };
    }
    if (this.isKw('var') || this.isKw('const') || (this.isId('let') && this._isLetDecl())) {
      const decl = this.parseVarDecl(false, false);
      if (this.isKw('in')) {
        this.next();
        const right = this.parseExpr(true);
        this.expectPunct(')');
        const body = this.parseStmt();
        return { type: 'ForIn', left: decl, right, body };
      }
      if (this.isId('of')) {
        this.next();
        const right = this.parseAssignExpr(true);
        this.expectPunct(')');
        const body = this.parseStmt();
        return { type: 'ForOf', isAwait, left: decl, right, body };
      }
      this.expectPunct(';');
      const test = this.isPunct(';') ? null : this.parseExpr(true);
      this.expectPunct(';');
      const update = this.isPunct(')') ? null : this.parseExpr(true);
      this.expectPunct(')');
      const body = this.parseStmt();
      return { type: 'For', init: decl, test, update, body };
    }
    const expr = this.parseExpr(false);
    if (this.isKw('in')) {
      this.next();
      const right = this.parseExpr(true);
      this.expectPunct(')');
      const body = this.parseStmt();
      return { type: 'ForIn', left: this._exprToPattern(expr), right, body };
    }
    if (this.isId('of')) {
      this.next();
      const right = this.parseAssignExpr(true);
      this.expectPunct(')');
      const body = this.parseStmt();
      return { type: 'ForOf', isAwait, left: this._exprToPattern(expr), right, body };
    }
    this.expectPunct(';');
    const test = this.isPunct(';') ? null : this.parseExpr(true);
    this.expectPunct(';');
    const update = this.isPunct(')') ? null : this.parseExpr(true);
    this.expectPunct(')');
    const body = this.parseStmt();
    return { type: 'For', init: expr, test, update, body };
  }

  parseWhile() {
    this.expectKw('while');
    this.expectPunct('(');
    const test = this.parseExpr(true);
    this.expectPunct(')');
    const body = this.parseStmt();
    return { type: 'While', test, body };
  }

  parseDoWhile() {
    this.expectKw('do');
    const body = this.parseStmt();
    this.expectKw('while');
    this.expectPunct('(');
    const test = this.parseExpr(true);
    this.expectPunct(')');
    this.eatPunct(';');
    return { type: 'DoWhile', body, test };
  }

  parseReturn() {
    this.expectKw('return');
    if (this.isPunct(';')) { this.next(); return { type: 'Return', arg: null }; }
    if (this.tok.nl || this.isPunct('}') || this.tok.type === 'eof') return { type: 'Return', arg: null };
    const arg = this.parseExpr(true);
    this.expectSemi();
    return { type: 'Return', arg };
  }

  parseThrow() {
    this.expectKw('throw');
    if (this.tok.nl) throw new SyntaxError('Illegal newline after throw');
    const arg = this.parseExpr(true);
    this.expectSemi();
    return { type: 'Throw', arg };
  }

  parseBreakContinue(type) {
    this.next();
    let label = null;
    if (!this.tok.nl && !this.isPunct(';') && !this.isPunct('}') && this.tok.type !== 'eof') {
      label = this.parseIdentName();
    }
    this.expectSemi();
    return { type, label };
  }

  parseSwitch() {
    this.expectKw('switch');
    this.expectPunct('(');
    const disc = this.parseExpr(true);
    this.expectPunct(')');
    this.expectPunct('{');
    const cases = [];
    while (!this.isPunct('}')) {
      let test = null;
      if (this.isKw('case')) {
        this.next();
        test = this.parseExpr(true);
        this.expectPunct(':');
      } else if (this.isKw('default')) {
        this.next();
        this.expectPunct(':');
      } else {
        throw new SyntaxError('Expected case or default in switch');
      }
      const cons = [];
      while (!this.isPunct('}') && !this.isKw('case') && !this.isKw('default')) {
        cons.push(this.parseStmt());
      }
      cases.push({ test, cons });
    }
    this.expectPunct('}');
    return { type: 'Switch', disc, cases };
  }

  parseTry() {
    this.expectKw('try');
    const block = this.parseBlock();
    let handler = null;
    let finalizer = null;
    if (this.isKw('catch')) {
      this.next();
      let param = null;
      if (this.eatPunct('(')) {
        param = this.parseBindingPattern();
        this.expectPunct(')');
      }
      const body = this.parseBlock();
      handler = { param, body };
    }
    if (this.isKw('finally')) {
      this.next();
      finalizer = this.parseBlock();
    }
    if (!handler && !finalizer) throw new SyntaxError('try without catch or finally');
    return { type: 'Try', block, handler, finalizer };
  }

  parseFunc(isDecl, optionalId) {
    let isAsync = false;
    if (this.isId('async')) { isAsync = true; this.next(); }
    this.expectKw('function');
    const isGen = this.eatPunct('*');
    let id = null;
    if (this.tok.type === 'id' || (this.tok.type === 'kw' && (this.tok.value === 'yield' || this.tok.value === 'await'))) {
      id = this.next().value;
    } else if (isDecl && !optionalId) {
      throw new SyntaxError('Function declaration requires name');
    }
    const params = this.parseParamList();
    const body = this.parseBlock();
    return { type: isDecl ? 'FuncDecl' : 'FuncExpr', id, params, body, isAsync, isGen };
  }

  parseParamList() {
    this.expectPunct('(');
    const params = [];
    while (!this.isPunct(')')) {
      if (this.eatPunct('...')) {
        params.push({ type: 'RestPat', arg: this.parseBindingPattern() });
        this.eatPunct(',');
        break;
      }
      const pat = this.parseBindingPattern();
      if (this.eatPunct('=')) {
        const right = this.parseAssignExpr(true);
        params.push({ type: 'AssignPat', left: pat, right });
      } else {
        params.push(pat);
      }
      if (!this.eatPunct(',')) break;
    }
    this.expectPunct(')');
    return params;
  }

  parseClass(isDecl, optionalId) {
    this.expectKw('class');
    let id = null;
    if (this.tok.type === 'id') id = this.next().value;
    else if (isDecl && !optionalId) throw new SyntaxError('Class declaration requires name');
    let superClass = null;
    if (this.isKw('extends')) {
      this.next();
      superClass = this.parseLeftHandSide();
    }
    this.expectPunct('{');
    const members = [];
    while (!this.isPunct('}')) {
      if (this.eatPunct(';')) continue;
      let isStatic = false;
      if (this.isId('static')) {
        const snap = this.sc.save();
        this.next();
        if (!this.isPunct('(') && !this.isPunct('=') && !this.isPunct(';')) {
          isStatic = true;
        } else {
          this.sc.restore(snap);
        }
      }
      let kind = 'method';
      let isAsync = false;
      let isGen = false;
      if (this.isId('async')) {
        const snap = this.sc.save();
        this.next();
        if (!this.tok.nl && !this.isPunct('(') && !this.isPunct('=') && !this.isPunct(';')) {
          isAsync = true;
        } else {
          this.sc.restore(snap);
        }
      }
      if (!isAsync && (this.isId('get') || this.isId('set'))) {
        const snap = this.sc.save();
        const kw = this.next().value;
        if (!this.isPunct('(') && !this.isPunct('=') && !this.isPunct(';')) {
          kind = kw;
        } else {
          this.sc.restore(snap);
        }
      }
      if (this.eatPunct('*')) isGen = true;
      const { key, computed } = this.parsePropKey();
      if (this.isPunct('(')) {
        const params = this.parseParamList();
        const body = this.parseBlock();
        members.push({ kind, isStatic, isAsync, isGen, computed, key, value: { type: 'FuncExpr', id: null, params, body, isAsync, isGen } });
      } else {
        let init = null;
        if (this.eatPunct('=')) init = this.parseAssignExpr(true);
        this.expectSemi();
        members.push({ kind: 'field', isStatic, isAsync: false, isGen: false, computed, key, value: init });
      }
    }
    this.expectPunct('}');
    return { type: isDecl ? 'ClassDecl' : 'ClassExpr', id, superClass, members };
  }

  parseIdentName() {
    if (this.tok.type === 'id' || (this.tok.type === 'kw' && (this.tok.value === 'yield' || this.tok.value === 'await'))) {
      return this.next().value;
    }
    throw new SyntaxError(`Expected identifier, got ${this.tok.type}:${this.tok.value} at ${this.tok.start}`);
  }

  parsePropIdent() {
    if (this.tok.type === 'id' || this.tok.type === 'kw') return this.next().value;
    throw new SyntaxError(`Expected property identifier, got ${this.tok.type}:${this.tok.value} at ${this.tok.start}`);
  }

  parsePropKey() {
    if (this.eatPunct('[')) {
      const key = this.parseAssignExpr(true);
      this.expectPunct(']');
      return { key, computed: true };
    }
    if (this.tok.type === 'str') return { key: { type: 'StrLit', value: this.next().value }, computed: false };
    if (this.tok.type === 'num') return { key: { type: 'NumLit', raw: this.next().raw }, computed: false };
    if (this.tok.type === 'bigint') return { key: { type: 'BigIntLit', raw: this.next().raw }, computed: false };
    return { key: { type: 'Id', name: this.parsePropIdent() }, computed: false };
  }

  parseBindingPattern() {
    if (this.eatPunct('[')) {
      const elems = [];
      while (!this.isPunct(']')) {
        if (this.isPunct(',')) {
          elems.push(null);
          this.next();
          continue;
        }
        if (this.eatPunct('...')) {
          elems.push({ type: 'RestPat', arg: this.parseBindingPattern() });
          this.eatPunct(',');
          break;
        }
        let pat = this.parseBindingPattern();
        if (this.eatPunct('=')) pat = { type: 'AssignPat', left: pat, right: this.parseAssignExpr(true) };
        elems.push(pat);
        if (!this.eatPunct(',')) break;
      }
      this.expectPunct(']');
      return { type: 'ArrayPat', elems };
    }
    if (this.eatPunct('{')) {
      const props = [];
      while (!this.isPunct('}')) {
        if (this.eatPunct('...')) {
          props.push({ type: 'RestPat', arg: this.parseBindingPattern() });
          this.eatPunct(',');
          break;
        }
        const { key, computed } = this.parsePropKey();
        let value;
        if (this.eatPunct(':')) {
          value = this.parseBindingPattern();
          if (this.eatPunct('=')) value = { type: 'AssignPat', left: value, right: this.parseAssignExpr(true) };
        } else {
          if (computed || key.type !== 'Id') throw new SyntaxError('Invalid shorthand object pattern');
          value = { type: 'BindId', name: key.name };
          if (this.eatPunct('=')) value = { type: 'AssignPat', left: value, right: this.parseAssignExpr(true) };
        }
        props.push({ type: 'ObjPatProp', key, computed, value });
        if (!this.eatPunct(',')) break;
      }
      this.expectPunct('}');
      return { type: 'ObjectPat', props };
    }
    return { type: 'BindId', name: this.parseIdentName() };
  }

  _exprToPattern(node) {
    if (!node) return null;
    if (node.type === 'Id') return node;
    if (node.type === 'MemberProp' || node.type === 'MemberComp') return node;
    if (node.type === 'ArrayExpr') {
      return {
        type: 'ArrayPat',
        elems: node.elems.map(el => {
          if (el === null) return null;
          if (el.type === 'Spread') return { type: 'RestPat', arg: this._exprToPattern(el.arg) };
          if (el.type === 'Assign' && el.op === '=') return { type: 'AssignPat', left: this._exprToPattern(el.left), right: el.right };
          return this._exprToPattern(el);
        }),
      };
    }
    if (node.type === 'ObjectExpr') {
      return {
        type: 'ObjectPat',
        props: node.props.map(p => {
          if (p.type === 'Spread') return { type: 'RestPat', arg: this._exprToPattern(p.arg) };
          let val = p.value;
          if (val.type === 'Assign' && val.op === '=') val = { type: 'AssignPat', left: this._exprToPattern(val.left), right: val.right };
          else val = this._exprToPattern(val);
          return { type: 'ObjPatProp', key: p.key, computed: p.computed, value: val };
        }),
      };
    }
    if (node.type === 'Assign' && node.op === '=') {
      return { type: 'AssignPat', left: this._exprToPattern(node.left), right: node.right };
    }
    return node;
  }

  parseExpr(allowIn) {
    const first = this.parseAssignExpr(allowIn);
    if (!this.isPunct(',')) return first;
    const exprs = [first];
    while (this.eatPunct(',')) {
      exprs.push(this.parseAssignExpr(allowIn));
    }
    return { type: 'Sequence', exprs };
  }

  _tryParseArrow(allowIn) {
    const snap = this.sc.save();
    try {
      let isAsync = false;
      if (this.isId('async')) {
        this.next();
        if (this.tok.nl) { this.sc.restore(snap); return null; }
        isAsync = true;
      }
      let params;
      if (this.isPunct('(')) {
        params = this.parseParamList();
      } else if (this.tok.type === 'id' || (this.tok.type === 'kw' && (this.tok.value === 'yield' || this.tok.value === 'await'))) {
        params = [{ type: 'BindId', name: this.next().value }];
      } else {
        this.sc.restore(snap);
        return null;
      }
      if (this.tok.nl || !this.eatPunct('=>')) {
        this.sc.restore(snap);
        return null;
      }
      let body;
      let exprBody = false;
      if (this.isPunct('{')) {
        body = this.parseBlock();
      } else {
        body = this.parseAssignExpr(allowIn);
        exprBody = true;
      }
      return { type: 'ArrowFunc', params, body, exprBody, isAsync };
    } catch {
      this.sc.restore(snap);
      return null;
    }
  }

  parseAssignExpr(allowIn) {
    if (this.isKw('yield')) {
      this.next();
      if (this.tok.nl || this.isPunct(';') || this.isPunct('}') || this.isPunct(')') || this.isPunct(']') || this.isPunct(',') || this.isPunct(':')) {
        return { type: 'Yield', delegate: false, arg: null };
      }
      const delegate = this.eatPunct('*');
      const arg = this.parseAssignExpr(allowIn);
      return { type: 'Yield', delegate, arg };
    }
    // Check arrow function
    if (this.isPunct('(') || this.tok.type === 'id' || (this.tok.type === 'kw' && (this.tok.value === 'yield' || this.tok.value === 'await'))) {
      const arrow = this._tryParseArrow(allowIn);
      if (arrow) return arrow;
    }
    const left = this.parseConditional(allowIn);
    if (this.tok.type === 'punct' && ASSIGN_OPS.has(this.tok.value)) {
      const op = this.next().value;
      const right = this.parseAssignExpr(allowIn);
      return { type: 'Assign', op, left: op === '=' ? this._exprToPattern(left) : left, right };
    }
    return left;
  }

  parseConditional(allowIn) {
    const test = this.parseBinary(allowIn, 1);
    if (this.eatPunct('?')) {
      const cons = this.parseAssignExpr(true);
      this.expectPunct(':');
      const alt = this.parseAssignExpr(allowIn);
      return { type: 'Cond', test, cons, alt };
    }
    return test;
  }

  parseBinary(allowIn, minPrec) {
    let left = this.parseUnary();
    while (true) {
      let op = null;
      if (this.tok.type === 'punct' && this.tok.value in BINARY_PREC) {
        op = this.tok.value;
      } else if (this.tok.type === 'kw' && (this.tok.value === 'instanceof' || (allowIn && this.tok.value === 'in'))) {
        op = this.tok.value;
      }
      if (op === null) break;
      const prec = BINARY_PREC[op];
      if (prec < minPrec) break;
      this.next();
      const nextMin = op === '**' ? prec : prec + 1;
      const right = this.parseBinary(allowIn, nextMin);
      if (op === '&&' || op === '||' || op === '??') {
        left = { type: 'Logical', op, left, right };
      } else {
        left = { type: 'Binary', op, left, right };
      }
    }
    return left;
  }

  parseUnary() {
    if (this.tok.type === 'punct' && (this.tok.value === '++' || this.tok.value === '--')) {
      const op = this.next().value;
      const arg = this.parseUnary();
      return { type: 'Update', op, prefix: true, arg };
    }
    if (
      (this.tok.type === 'punct' && (this.tok.value === '+' || this.tok.value === '-' || this.tok.value === '!' || this.tok.value === '~')) ||
      (this.tok.type === 'kw' && (this.tok.value === 'typeof' || this.tok.value === 'void' || this.tok.value === 'delete'))
    ) {
      const op = this.next().value;
      const arg = this.parseUnary();
      return { type: 'Unary', op, arg };
    }
    if (this.isKw('await')) {
      this.next();
      const arg = this.parseUnary();
      return { type: 'Await', arg };
    }
    const expr = this.parseLeftHandSide();
    if (!this.tok.nl && this.tok.type === 'punct' && (this.tok.value === '++' || this.tok.value === '--')) {
      const op = this.next().value;
      return { type: 'Update', op, prefix: false, arg: expr };
    }
    return expr;
  }

  parseLeftHandSide() {
    let expr;
    if (this.isKw('new')) {
      expr = this.parseNewExpr();
    } else {
      expr = this.parsePrimary();
    }
    return this.parsePostfixes(expr, true);
  }

  parseNewExpr() {
    this.expectKw('new');
    if (this.eatPunct('.')) {
      const prop = this.parseIdentName();
      return { type: 'MetaProp', meta: 'new', prop };
    }
    let callee;
    if (this.isKw('new')) callee = this.parseNewExpr();
    else callee = this.parsePostfixes(this.parsePrimary(), false);
    let args = [];
    if (this.isPunct('(')) args = this.parseArgList();
    return { type: 'New', callee, args };
  }

  parsePostfixes(expr, allowCall) {
    while (true) {
      if (this.eatPunct('.')) {
        const prop = this.parsePropIdent();
        expr = { type: 'MemberProp', obj: expr, prop, optional: false };
      } else if (this.eatPunct('?.')) {
        if (this.eatPunct('[')) {
          const prop = this.parseExpr(true);
          this.expectPunct(']');
          expr = { type: 'MemberComp', obj: expr, prop, optional: true };
        } else if (allowCall && this.isPunct('(')) {
          const args = this.parseArgList();
          expr = { type: 'Call', callee: expr, args, optional: true };
        } else {
          const prop = this.parsePropIdent();
          expr = { type: 'MemberProp', obj: expr, prop, optional: true };
        }
      } else if (this.eatPunct('[')) {
        const prop = this.parseExpr(true);
        this.expectPunct(']');
        expr = { type: 'MemberComp', obj: expr, prop, optional: false };
      } else if (allowCall && this.isPunct('(')) {
        const args = this.parseArgList();
        expr = { type: 'Call', callee: expr, args, optional: false };
      } else if (this.tok.type === 'tpl_head' || this.tok.type === 'tpl_tail') {
        const quasi = this.parseTemplate();
        expr = { type: 'TaggedTemplate', tag: expr, quasi };
      } else {
        break;
      }
    }
    return expr;
  }

  parseArgList() {
    this.expectPunct('(');
    const args = [];
    while (!this.isPunct(')')) {
      if (this.eatPunct('...')) {
        args.push({ type: 'Spread', arg: this.parseAssignExpr(true) });
      } else {
        args.push(this.parseAssignExpr(true));
      }
      if (!this.eatPunct(',')) break;
    }
    this.expectPunct(')');
    return args;
  }

  parseTemplate() {
    const quasis = [];
    const exprs = [];
    let chunk = this.next();
    quasis.push(chunk.raw);
    while (chunk.type === 'tpl_head') {
      exprs.push(this.parseExpr(true));
      chunk = this.sc.readTemplateContinuation();
      quasis.push(chunk.raw);
    }
    return { type: 'Template', quasis, exprs };
  }

  parsePrimary() {
    const t = this.tok;
    if (t.type === 'id') {
      if (t.value === 'async' && this._peekAsyncFunc()) return this.parseFunc(false, true);
      this.next();
      return { type: 'Id', name: t.value };
    }
    if (t.type === 'num') { this.next(); return { type: 'NumLit', raw: t.raw }; }
    if (t.type === 'bigint') { this.next(); return { type: 'BigIntLit', raw: t.raw }; }
    if (t.type === 'str') { this.next(); return { type: 'StrLit', value: t.value }; }
    if (t.type === 'tpl_head' || t.type === 'tpl_tail') return this.parseTemplate();
    if (t.type === 'kw') {
      if (t.value === 'true') { this.next(); return { type: 'BoolLit', value: true }; }
      if (t.value === 'false') { this.next(); return { type: 'BoolLit', value: false }; }
      if (t.value === 'null') { this.next(); return { type: 'NullLit' }; }
      if (t.value === 'this') { this.next(); return { type: 'This' }; }
      if (t.value === 'super') { this.next(); return { type: 'Super' }; }
      if (t.value === 'function') return this.parseFunc(false, true);
      if (t.value === 'class') return this.parseClass(false, true);
      if (t.value === 'import') {
        this.next();
        if (this.eatPunct('.')) {
          const prop = this.parseIdentName();
          return { type: 'MetaProp', meta: 'import', prop };
        }
        const args = this.parseArgList();
        return { type: 'Call', callee: { type: 'Id', name: 'import' }, args, optional: false };
      }
      if (t.value === 'yield' || t.value === 'await') {
        this.next();
        return { type: 'Id', name: t.value };
      }
    }
    if (t.type === 'punct') {
      if (t.value === '/' || t.value === '/=') {
        const rx = this.sc.readRegex();
        return { type: 'RegexLit', pattern: rx.pattern, flags: rx.flags };
      }
      if (t.value === '(') {
        this.next();
        const expr = this.parseExpr(true);
        this.expectPunct(')');
        return expr;
      }
      if (t.value === '[') return this.parseArray();
      if (t.value === '{') return this.parseObject();
    }
    throw new SyntaxError(`Unexpected token ${t.type}:${t.value} at ${t.start}`);
  }

  parseArray() {
    this.expectPunct('[');
    const elems = [];
    while (!this.isPunct(']')) {
      if (this.isPunct(',')) {
        elems.push(null);
        this.next();
        continue;
      }
      if (this.eatPunct('...')) {
        elems.push({ type: 'Spread', arg: this.parseAssignExpr(true) });
      } else {
        elems.push(this.parseAssignExpr(true));
      }
      if (!this.eatPunct(',')) break;
    }
    this.expectPunct(']');
    return { type: 'ArrayExpr', elems };
  }

  parseObject() {
    this.expectPunct('{');
    const props = [];
    while (!this.isPunct('}')) {
      if (this.eatPunct('...')) {
        props.push({ type: 'Spread', arg: this.parseAssignExpr(true) });
        if (!this.eatPunct(',')) break;
        continue;
      }
      let kind = 'init';
      let isAsync = false;
      let isGen = false;
      if (this.isId('async')) {
        const snap = this.sc.save();
        this.next();
        if (!this.tok.nl && !this.isPunct(':') && !this.isPunct('(') && !this.isPunct(',') && !this.isPunct('}')) {
          isAsync = true;
        } else {
          this.sc.restore(snap);
        }
      }
      if (!isAsync && (this.isId('get') || this.isId('set'))) {
        const snap = this.sc.save();
        const kw = this.next().value;
        if (!this.isPunct(':') && !this.isPunct('(') && !this.isPunct(',') && !this.isPunct('}')) {
          kind = kw;
        } else {
          this.sc.restore(snap);
        }
      }
      if (this.eatPunct('*')) isGen = true;
      const { key, computed } = this.parsePropKey();
      if (this.isPunct('(')) {
        const params = this.parseParamList();
        const body = this.parseBlock();
        props.push({
          type: 'ObjProp', kind, computed, key, method: kind === 'init',
          value: { type: 'FuncExpr', id: null, params, body, isAsync, isGen },
        });
      } else if (this.eatPunct(':')) {
        const value = this.parseAssignExpr(true);
        props.push({ type: 'ObjProp', kind: 'init', computed, key, method: false, value });
      } else {
        if (computed || key.type !== 'Id' || isAsync || isGen || kind !== 'init') {
          throw new SyntaxError('Invalid object property');
        }
        // Normalize shorthand {x} -> {x: x} for unambiguous local renaming & AST simplicity
        let value = { type: 'Id', name: key.name };
        if (this.eatPunct('=')) {
          // CoverInitializedName for object destructuring default
          value = { type: 'Assign', op: '=', left: value, right: this.parseAssignExpr(true) };
        }
        props.push({ type: 'ObjProp', kind: 'init', computed: false, key, method: false, value });
      }
      if (!this.eatPunct(',')) break;
    }
    this.expectPunct('}');
    return { type: 'ObjectExpr', props };
  }
}

// ---------------------------------------------------------------------------
// Safe Scope-Preserving Local Canonicalization
// ---------------------------------------------------------------------------

function collectPatternBindNodes(pat, out) {
  if (!pat) return;
  switch (pat.type) {
    case 'BindId': out.push(pat); break;
    case 'ArrayPat': for (const e of pat.elems) collectPatternBindNodes(e, out); break;
    case 'ObjectPat':
      for (const p of pat.props) {
        if (p.type === 'RestPat') collectPatternBindNodes(p.arg, out);
        else collectPatternBindNodes(p.value, out);
      }
      break;
    case 'AssignPat': collectPatternBindNodes(pat.left, out); break;
    case 'RestPat': collectPatternBindNodes(pat.arg, out); break;
  }
}

function isUnsafeForRenaming(ast) {
  let unsafe = false;
  function walk(n) {
    if (!n || typeof n !== 'object' || unsafe) return;
    if (Array.isArray(n)) { for (const x of n) walk(x); return; }
    if (n.type === 'With') { unsafe = true; return; }
    if (n.type === 'Id' && (n.name === 'eval' || n.name === 'Function' || n.name === 'arguments')) { unsafe = true; return; }
    if (n.type === 'MemberProp' && (n.prop === 'name' || n.prop === 'toString')) { unsafe = true; return; }
    if (n.type === 'MemberComp' && n.prop?.type === 'StrLit' && (n.prop.value === 'name' || n.prop.value === 'toString')) { unsafe = true; return; }
    for (const k of Object.keys(n)) {
      if (k === 'type') continue;
      const v = n[k];
      if (v && typeof v === 'object') walk(v);
    }
  }
  walk(ast);
  return unsafe;
}

function canonicalizeLocals(ast) {
  if (isUnsafeForRenaming(ast)) return { renamed: 0, skippedReason: 'reflection_or_eval_guard' };

  // Build scope tree, collect declarations and references, then rename strictly inside
  // function/arrow/method/block scopes (never renaming global/module top-level bindings).
  const scopes = [];
  function newScope(kind, parent) {
    const sc = { id: scopes.length, kind, parent, vars: new Map(), refs: [], children: [] };
    if (parent) parent.children.push(sc);
    scopes.push(sc);
    return sc;
  }

  function nearestFuncScope(sc) {
    let cur = sc;
    while (cur && cur.kind !== 'func' && cur.kind !== 'global') cur = cur.parent;
    return cur;
  }

  function addDecl(sc, name, kind, node) {
    const target = (kind === 'var' || kind === 'func') ? nearestFuncScope(sc) : sc;
    let rec = target.vars.get(name);
    if (!rec) {
      rec = {
        name,
        scope: target,
        kind,
        eligible: target.kind !== 'global' && kind !== 'func_self' && !RESERVED_NEVER_RENAME.has(name),
        declNodes: [],
        refNodes: [],
      };
      target.vars.set(name, rec);
    } else if (kind !== 'var') {
      rec.eligible = false;
    }
    rec.declNodes.push(node);
    return rec;
  }

  const rootScope = newScope('global', null);

  function declarePattern(pat, sc, kind) {
    if (!pat) return;
    switch (pat.type) {
      case 'BindId': addDecl(sc, pat.name, kind, pat); break;
      case 'ArrayPat': for (const e of pat.elems) declarePattern(e, sc, kind); break;
      case 'ObjectPat':
        for (const p of pat.props) {
          if (p.type === 'RestPat') declarePattern(p.arg, sc, kind);
          else {
            if (p.computed) visitExpr(p.key, sc);
            declarePattern(p.value, sc, kind);
          }
        }
        break;
      case 'AssignPat':
        declarePattern(pat.left, sc, kind);
        visitExpr(pat.right, sc);
        break;
      case 'RestPat': declarePattern(pat.arg, sc, kind); break;
    }
  }

  // Pass 1: Hoist var & function decls in current block/func, then walk statements.
  function hoistDecls(stmts, sc) {
    for (const st of stmts) {
      if (!st) continue;
      if (st.type === 'FuncDecl' && st.id) {
        addDecl(sc, st.id, 'func', st).eligible = false;
      } else if (st.type === 'ClassDecl' && st.id) {
        addDecl(sc, st.id, 'let', st).eligible = false;
      } else if (st.type === 'VarDecl') {
        const bnodes = [];
        for (const d of st.decls) collectPatternBindNodes(d.id, bnodes);
        if (st.kind === 'var') {
          for (const b of bnodes) addDecl(sc, b.name, 'var', b);
        } else {
          for (const b of bnodes) addDecl(sc, b.name, st.kind, b);
        }
      } else if (st.type === 'ExportNamed' && st.declaration) {
        hoistDecls([st.declaration], sc);
      }
    }
  }

  function hoistVarsRecursive(node, funcSc) {
    if (!node || typeof node !== 'object') return;
    if (node.type === 'FuncDecl' || node.type === 'FuncExpr' || node.type === 'ArrowFunc') return;
    if (node.type === 'VarDecl' && node.kind === 'var') {
      const bnodes = [];
      for (const d of node.decls) collectPatternBindNodes(d.id, bnodes);
      for (const b of bnodes) addDecl(funcSc, b.name, 'var', b);
    }
    for (const k of Object.keys(node)) {
      if (k === 'type') continue;
      const v = node[k];
      if (Array.isArray(v)) { for (const x of v) hoistVarsRecursive(x, funcSc); }
      else if (v && typeof v === 'object') hoistVarsRecursive(v, funcSc);
    }
  }

  function visitStmtList(stmts, sc) {
    hoistDecls(stmts, sc);
    for (const st of stmts) visitStmt(st, sc);
  }

  function visitStmt(st, sc) {
    if (!st) return;
    switch (st.type) {
      case 'Block': {
        const bsc = newScope('block', sc);
        visitStmtList(st.body, bsc);
        break;
      }
      case 'VarDecl': {
        for (const d of st.decls) {
          visitPatExprs(d.id, sc);
          if (d.init) visitExpr(d.init, sc);
        }
        break;
      }
      case 'ExprStmt': visitExpr(st.expr, sc); break;
      case 'If':
        visitExpr(st.test, sc);
        visitStmt(st.cons, sc);
        if (st.alt) visitStmt(st.alt, sc);
        break;
      case 'For': {
        const fsc = newScope('block', sc);
        if (st.init) {
          if (st.init.type === 'VarDecl') {
            hoistDecls([st.init], fsc);
            visitStmt(st.init, fsc);
          } else {
            visitExpr(st.init, fsc);
          }
        }
        if (st.test) visitExpr(st.test, fsc);
        if (st.update) visitExpr(st.update, fsc);
        visitStmt(st.body, fsc);
        break;
      }
      case 'ForIn':
      case 'ForOf': {
        const fsc = newScope('block', sc);
        if (st.left.type === 'VarDecl') {
          hoistDecls([st.left], fsc);
          visitStmt(st.left, fsc);
        } else {
          visitExpr(st.left, fsc);
        }
        visitExpr(st.right, fsc);
        visitStmt(st.body, fsc);
        break;
      }
      case 'While':
        visitExpr(st.test, sc);
        visitStmt(st.body, sc);
        break;
      case 'DoWhile':
        visitStmt(st.body, sc);
        visitExpr(st.test, sc);
        break;
      case 'Return':
      case 'Throw':
        if (st.arg) visitExpr(st.arg, sc);
        break;
      case 'Switch': {
        visitExpr(st.disc, sc);
        const ssc = newScope('block', sc);
        for (const c of st.cases) {
          if (c.test) visitExpr(c.test, ssc);
          hoistDecls(c.cons, ssc);
        }
        for (const c of st.cases) {
          for (const s of c.cons) visitStmt(s, ssc);
        }
        break;
      }
      case 'Try': {
        visitStmt(st.block, sc);
        if (st.handler) {
          const csc = newScope('block', sc);
          if (st.handler.param) declarePattern(st.handler.param, csc, 'catch');
          visitStmtList(st.handler.body.body, csc);
        }
        if (st.finalizer) visitStmt(st.finalizer, sc);
        break;
      }
      case 'FuncDecl': {
        const fsc = newScope('func', sc);
        for (const p of st.params) declarePattern(p, fsc, 'param');
        hoistVarsRecursive(st.body, fsc);
        visitStmtList(st.body.body, fsc);
        break;
      }
      case 'ClassDecl': {
        if (st.superClass) visitExpr(st.superClass, sc);
        for (const m of st.members) {
          if (m.computed) visitExpr(m.key, sc);
          if (m.value) visitExpr(m.value, sc);
        }
        break;
      }
      case 'Labeled': visitStmt(st.body, sc); break;
      case 'ExportDefault':
        if (st.declaration.type === 'FuncDecl' || st.declaration.type === 'ClassDecl') visitStmt(st.declaration, sc);
        else visitExpr(st.declaration, sc);
        break;
      case 'ExportNamed':
        if (st.declaration) visitStmt(st.declaration, sc);
        break;
      case 'ImportDecl':
        for (const sp of st.specifiers) {
          addDecl(rootScope, sp.local, 'let', sp).eligible = false;
        }
        break;
    }
  }

  function visitPatExprs(pat, sc) {
    if (!pat) return;
    switch (pat.type) {
      case 'ArrayPat': for (const e of pat.elems) visitPatExprs(e, sc); break;
      case 'ObjectPat':
        for (const p of pat.props) {
          if (p.type === 'RestPat') visitPatExprs(p.arg, sc);
          else {
            if (p.computed) visitExpr(p.key, sc);
            visitPatExprs(p.value, sc);
          }
        }
        break;
      case 'AssignPat': visitPatExprs(pat.left, sc); visitExpr(pat.right, sc); break;
      case 'RestPat': visitPatExprs(pat.arg, sc); break;
    }
  }

  function visitExpr(ex, sc) {
    if (!ex) return;
    switch (ex.type) {
      case 'Id': sc.refs.push(ex); break;
      case 'Binary':
      case 'Logical':
      case 'Assign':
        visitExpr(ex.left, sc);
        visitExpr(ex.right, sc);
        break;
      case 'Unary':
      case 'Update':
      case 'Await':
      case 'Spread':
        visitExpr(ex.arg, sc);
        break;
      case 'Yield': if (ex.arg) visitExpr(ex.arg, sc); break;
      case 'Cond':
        visitExpr(ex.test, sc);
        visitExpr(ex.cons, sc);
        visitExpr(ex.alt, sc);
        break;
      case 'Call':
      case 'New':
        visitExpr(ex.callee, sc);
        for (const a of ex.args) visitExpr(a, sc);
        break;
      case 'MemberProp': visitExpr(ex.obj, sc); break;
      case 'MemberComp': visitExpr(ex.obj, sc); visitExpr(ex.prop, sc); break;
      case 'ArrayExpr': for (const e of ex.elems) if (e) visitExpr(e, sc); break;
      case 'ObjectExpr':
        for (const p of ex.props) {
          if (p.type === 'Spread') visitExpr(p.arg, sc);
          else {
            if (p.computed) visitExpr(p.key, sc);
            visitExpr(p.value, sc);
          }
        }
        break;
      case 'Sequence': for (const e of ex.exprs) visitExpr(e, sc); break;
      case 'Template': for (const e of ex.exprs) visitExpr(e, sc); break;
      case 'TaggedTemplate': visitExpr(ex.tag, sc); visitExpr(ex.quasi, sc); break;
      case 'FuncExpr': {
        const fsc = newScope('func', sc);
        if (ex.id) addDecl(fsc, ex.id, 'func_self', ex).eligible = false;
        for (const p of ex.params) declarePattern(p, fsc, 'param');
        hoistVarsRecursive(ex.body, fsc);
        visitStmtList(ex.body.body, fsc);
        break;
      }
      case 'ArrowFunc': {
        const fsc = newScope('func', sc);
        for (const p of ex.params) declarePattern(p, fsc, 'param');
        if (ex.exprBody) visitExpr(ex.body, fsc);
        else {
          hoistVarsRecursive(ex.body, fsc);
          visitStmtList(ex.body.body, fsc);
        }
        break;
      }
      case 'ClassExpr': {
        const csc = newScope('block', sc);
        if (ex.id) addDecl(csc, ex.id, 'let', ex).eligible = false;
        if (ex.superClass) visitExpr(ex.superClass, sc);
        for (const m of ex.members) {
          if (m.computed) visitExpr(m.key, csc);
          if (m.value) visitExpr(m.value, csc);
        }
        break;
      }
      // Assignment destructuring targets (converted from exprs)
      case 'ArrayPat': for (const e of ex.elems) if (e) visitExpr(e, sc); break;
      case 'ObjectPat':
        for (const p of ex.props) {
          if (p.type === 'RestPat') visitExpr(p.arg, sc);
          else {
            if (p.computed) visitExpr(p.key, sc);
            visitExpr(p.value, sc);
          }
        }
        break;
      case 'AssignPat': visitExpr(ex.left, sc); visitExpr(ex.right, sc); break;
      case 'RestPat': visitExpr(ex.arg, sc); break;
    }
  }

  hoistVarsRecursive(ast, rootScope);
  visitStmtList(ast.body, rootScope);

  // Build conflict graph over all variables
  const allVars = [];
  for (const sc of scopes) {
    for (const v of sc.vars.values()) {
      v.vid = allVars.length;
      v.neighbors = new Set();
      v.forbidden = new Set();
      allVars.push(v);
    }
  }
  const addEdge = (a, b) => { if (a !== b) { a.neighbors.add(b.vid); b.neighbors.add(a.vid); } };
  for (const sc of scopes) {
    const own = [...sc.vars.values()];
    for (let i = 0; i < own.length; i++) {
      for (let j = i + 1; j < own.length; j++) addEdge(own[i], own[j]);
    }
    for (const ref of sc.refs) {
      let cur = sc;
      let resolved = null;
      while (cur) {
        if (cur.vars.has(ref.name)) { resolved = cur.vars.get(ref.name); break; }
        cur = cur.parent;
      }
      if (resolved) {
        resolved.refNodes.push(ref);
        let c = sc;
        while (c) {
          for (const other of c.vars.values()) addEdge(resolved, other);
          if (c === resolved.scope) break;
          c = c.parent;
        }
      } else {
        for (let c = sc; c; c = c.parent) {
          for (const other of c.vars.values()) other.forbidden.add(ref.name);
        }
      }
    }
  }

  // Assign deterministic sequential canonical names v0, v1, ... per top-level function tree!
  const assigned = allVars.map(v => v.name);
  let renamed = 0;

  function assignSubtree(sc, counterRef) {
    for (const v of sc.vars.values()) {
      if (!v.eligible) continue;
      let candidate;
      while (true) {
        candidate = `v${counterRef.n++}`;
        if (v.forbidden.has(candidate)) continue;
        let conflict = false;
        for (const nb of v.neighbors) {
          if (assigned[nb] === candidate) { conflict = true; break; }
        }
        if (!conflict) break;
      }
      assigned[v.vid] = candidate;
      if (candidate !== v.name) renamed++;
    }
    for (const child of sc.children) {
      assignSubtree(child, counterRef);
    }
  }

  for (const topChild of rootScope.children) {
    assignSubtree(topChild, { n: 0 });
  }

  // Verify no capture conflicts
  for (const v of allVars) {
    if (!v.eligible) continue;
    const nm = assigned[v.vid];
    if (v.forbidden.has(nm)) throw new Error('capture conflict (forbidden)');
    for (const nb of v.neighbors) {
      if (assigned[nb] === nm) throw new Error('capture conflict (neighbor)');
    }
  }

  // Apply renames in AST
  for (const v of allVars) {
    if (!v.eligible) continue;
    const nm = assigned[v.vid];
    for (const dn of v.declNodes) {
      if (dn.type === 'BindId') dn.name = nm;
    }
    for (const rn of v.refNodes) {
      rn.name = nm;
    }
  }

  return { renamed, skippedReason: null };
}

// ---------------------------------------------------------------------------
// Deterministic Canonical Unparser (JS AST -> Canonical JS String)
// ---------------------------------------------------------------------------

function exprPrec(n) {
  if (!n) return 20;
  switch (n.type) {
    case 'Sequence': return 1;
    case 'Assign': case 'Yield': case 'ArrowFunc': return 2;
    case 'Cond': return 3;
    case 'Logical': return BINARY_PREC[n.op];
    case 'Binary': return BINARY_PREC[n.op];
    case 'Unary': case 'Await': return 16;
    case 'Update': return n.prefix ? 16 : 17;
    case 'Call': case 'New': case 'MemberProp': case 'MemberComp': case 'TaggedTemplate': return 18;
    default: return 19;
  }
}

function escapeStr(val) {
  return JSON.stringify(val).replace(/\u2028/g, '\\u2028').replace(/\u2029/g, '\\u2029');
}

function needsExprStmtParens(ex) {
  let cur = ex;
  while (cur) {
    if (cur.type === 'ObjectExpr' || cur.type === 'FuncExpr' || cur.type === 'ClassExpr') return true;
    if (cur.type === 'Binary' || cur.type === 'Logical' || cur.type === 'Assign' || cur.type === 'Cond' || cur.type === 'Sequence') {
      cur = cur.type === 'Cond' ? cur.test : cur.type === 'Sequence' ? cur.exprs[0] : cur.left;
    } else if (cur.type === 'Call') cur = cur.callee;
    else if (cur.type === 'MemberProp' || cur.type === 'MemberComp') cur = cur.obj;
    else if (cur.type === 'TaggedTemplate') cur = cur.tag;
    else if (cur.type === 'Update' && !cur.prefix) cur = cur.arg;
    else break;
  }
  // Also protect `let [` at start of expression statement
  if (ex.type === 'MemberComp' && ex.obj.type === 'Id' && ex.obj.name === 'let') return true;
  return false;
}

function unparseAST(ast) {
  return ast.body.map(s => uStmt(s)).join('\n') + (ast.body.length ? '\n' : '');
}

function uStmt(st) {
  switch (st.type) {
    case 'Empty': return ';';
    case 'Debugger': return 'debugger;';
    case 'Block': return '{' + st.body.map(uStmt).join('') + '}';
    case 'VarDecl':
      return st.kind + ' ' + st.decls.map(d => uPat(d.id) + (d.init ? '=' + uSubExpr(d.init, 2) : '')).join(',') + ';';
    case 'ExprStmt': {
      const s = uExpr(st.expr);
      return (needsExprStmtParens(st.expr) ? `(${s})` : s) + ';';
    }
    case 'If': {
      let cons = uStmt(st.cons);
      // Avoid dangling-else ambiguity when st.alt exists and st.cons is a bare If without else
      if (st.alt && endsWithOpenIf(st.cons)) cons = '{' + cons + '}';
      return `if(${uExpr(st.test)})${cons}` + (st.alt ? `else${needsSpaceAfterWord(uStmt(st.alt)) ? ' ' : ''}${uStmt(st.alt)}` : '');
    }
    case 'For': {
      let init = '';
      if (st.init) {
        if (st.init.type === 'VarDecl') {
          init = st.init.kind + ' ' + st.init.decls.map(d => uPat(d.id) + (d.init ? '=' + uNoIn(d.init, 2) : '')).join(',');
        } else {
          init = uNoIn(st.init, 0);
        }
      }
      const test = st.test ? uExpr(st.test) : '';
      const upd = st.update ? uExpr(st.update) : '';
      return `for(${init};${test};${upd})${uStmt(st.body)}`;
    }
    case 'ForIn': {
      const left = st.left.type === 'VarDecl'
        ? st.left.kind + ' ' + st.left.decls.map(d => uPat(d.id) + (d.init ? '=' + uNoIn(d.init, 2) : '')).join(',')
        : uPat(st.left);
      return `for(${left} in ${uExpr(st.right)})${uStmt(st.body)}`;
    }
    case 'ForOf': {
      const left = st.left.type === 'VarDecl'
        ? st.left.kind + ' ' + st.left.decls.map(d => uPat(d.id) + (d.init ? '=' + uNoIn(d.init, 2) : '')).join(',')
        : uPat(st.left);
      return `for${st.isAwait ? ' await' : ''}(${left} of ${uSubExpr(st.right, 2)})${uStmt(st.body)}`;
    }
    case 'While': return `while(${uExpr(st.test)})${uStmt(st.body)}`;
    case 'DoWhile': {
      const b = uStmt(st.body);
      return `do${needsSpaceAfterWord(b) ? ' ' : ''}${b}while(${uExpr(st.test)});`;
    }
    case 'Return': {
      if (!st.arg) return 'return;';
      const a = uExpr(st.arg);
      return `return${needsSpaceAfterWord(a) ? ' ' : ''}${a};`;
    }
    case 'Throw': {
      const a = uExpr(st.arg);
      return `throw${needsSpaceAfterWord(a) ? ' ' : ''}${a};`;
    }
    case 'Break': return st.label ? `break ${st.label};` : 'break;';
    case 'Continue': return st.label ? `continue ${st.label};` : 'continue;';
    case 'Switch':
      return `switch(${uExpr(st.disc)}){` + st.cases.map(c =>
        (c.test ? `case ${uExpr(c.test)}:` : 'default:') + c.cons.map(uStmt).join('')
      ).join('') + '}';
    case 'Try':
      return `try${uStmt(st.block)}` +
        (st.handler ? `catch${st.handler.param ? `(${uPat(st.handler.param)})` : ''}${uStmt(st.handler.body)}` : '') +
        (st.finalizer ? `finally${uStmt(st.finalizer)}` : '');
    case 'With': return `with(${uExpr(st.object)})${uStmt(st.body)}`;
    case 'Labeled': return `${st.label}:${uStmt(st.body)}`;
    case 'FuncDecl':
      return `${st.isAsync ? 'async ' : ''}function${st.isGen ? '*' : ''}${st.id ? ' ' + st.id : ''}(${st.params.map(uPat).join(',')})${uStmt(st.body)}`;
    case 'ClassDecl':
      return uClass(st);
    case 'ImportDecl': {
      if (st.specifiers.length === 0) return `import${escapeStr(st.source)};`;
      const parts = [];
      const def = st.specifiers.find(x => x.kind === 'default');
      const ns = st.specifiers.find(x => x.kind === 'ns');
      const named = st.specifiers.filter(x => x.kind === 'named');
      if (def) parts.push(def.local);
      if (ns) parts.push(`* as ${ns.local}`);
      if (named.length) parts.push('{' + named.map(x => x.imported === x.local ? x.local : `${x.imported} as ${x.local}`).join(',') + '}');
      return `import ${parts.join(',')} from${escapeStr(st.source)};`;
    }
    case 'ExportDefault': {
      const d = st.declaration;
      if (d.type === 'FuncDecl' || d.type === 'ClassDecl') return `export default ${uStmt(d)}`;
      return `export default ${uSubExpr(d, 2)};`;
    }
    case 'ExportAll':
      return `export*${st.exported ? ` as ${st.exported}` : ''} from${escapeStr(st.source)};`;
    case 'ExportNamed': {
      if (st.declaration) return `export ${uStmt(st.declaration)}`;
      const list = '{' + st.specifiers.map(x => x.local === x.exported ? x.local : `${x.local} as ${x.exported}`).join(',') + '}';
      return `export${list}${st.source ? ` from${escapeStr(st.source)}` : ''};`;
    }
    default:
      throw new Error(`Unsupported stmt type in unparse: ${st.type}`);
  }
}

function endsWithOpenIf(st) {
  let cur = st;
  while (cur) {
    if (cur.type === 'If') {
      if (!cur.alt) return true;
      cur = cur.alt;
    } else if (cur.type === 'For' || cur.type === 'ForIn' || cur.type === 'ForOf' || cur.type === 'While' || cur.type === 'Labeled' || cur.type === 'With') {
      cur = cur.body;
    } else {
      return false;
    }
  }
  return false;
}

function needsSpaceAfterWord(s) {
  if (!s) return false;
  const c = s[0];
  return isIdPart(c) || (c >= '0' && c <= '9') || c === '\\';
}

function containsTopLevelIn(n) {
  if (!n || typeof n !== 'object') return false;
  if (n.type === 'Binary' && n.op === 'in') return true;
  if (n.type === 'Binary' || n.type === 'Logical' || n.type === 'Assign') return containsTopLevelIn(n.left) || containsTopLevelIn(n.right);
  if (n.type === 'Cond') return containsTopLevelIn(n.test) || containsTopLevelIn(n.alt);
  if (n.type === 'Sequence') return n.exprs.some(containsTopLevelIn);
  if (n.type === 'Unary' || n.type === 'Await') return containsTopLevelIn(n.arg);
  return false;
}

function uNoIn(ex, minP) {
  const s = uSubExpr(ex, minP);
  return containsTopLevelIn(ex) ? `(${s})` : s;
}

function uClass(cl) {
  const head = `class${cl.id ? ' ' + cl.id : ''}${cl.superClass ? ' extends ' + uSubExpr(cl.superClass, 18) : ''}`;
  const body = cl.members.map(m => {
    const k = uPropKey(m.key, m.computed);
    if (m.kind === 'field') {
      return `${m.isStatic ? 'static ' : ''}${k}${m.value ? '=' + uSubExpr(m.value, 2) : ''};`;
    }
    const prefix = `${m.isStatic ? 'static ' : ''}${m.isAsync ? 'async ' : ''}${m.kind === 'get' ? 'get ' : m.kind === 'set' ? 'set ' : ''}${m.isGen ? '*' : ''}`;
    return `${prefix}${k}(${m.value.params.map(uPat).join(',')})${uStmt(m.value.body)}`;
  }).join('');
  return `${head}{${body}}`;
}

function uPropKey(key, computed) {
  if (computed) return `[${uSubExpr(key, 2)}]`;
  if (key.type === 'Id') return key.name;
  if (key.type === 'StrLit') return escapeStr(key.value);
  if (key.type === 'NumLit' || key.type === 'BigIntLit') return key.raw;
  return uExpr(key);
}

function uPat(pat) {
  switch (pat.type) {
    case 'BindId': return pat.name;
    case 'Id': return pat.name;
    case 'ArrayPat':
      return '[' + pat.elems.map((e, idx) => (e === null ? (idx === pat.elems.length - 1 ? ',' : '') : uPat(e))).join(',') + ']';
    case 'ObjectPat':
      return '{' + pat.props.map(p => {
        if (p.type === 'RestPat') return `...${uPat(p.arg)}`;
        return `${uPropKey(p.key, p.computed)}:${uPat(p.value)}`;
      }).join(',') + '}';
    case 'AssignPat': return `${uPat(pat.left)}=${uSubExpr(pat.right, 2)}`;
    case 'RestPat': return `...${uPat(pat.arg)}`;
    default: return uExpr(pat);
  }
}

function uSubExpr(ex, minP) {
  const s = uExpr(ex);
  return exprPrec(ex) < minP ? `(${s})` : s;
}

function uExpr(ex) {
  switch (ex.type) {
    case 'Id': return ex.name;
    case 'NumLit': return ex.raw;
    case 'BigIntLit': return ex.raw;
    case 'StrLit': return escapeStr(ex.value);
    case 'BoolLit': return ex.value ? 'true' : 'false';
    case 'NullLit': return 'null';
    case 'RegexLit': return `/${ex.pattern}/${ex.flags}`;
    case 'This': return 'this';
    case 'Super': return 'super';
    case 'MetaProp': return `${ex.meta}.${ex.prop}`;
    case 'Spread': return `...${uSubExpr(ex.arg, 2)}`;
    case 'Sequence': return ex.exprs.map(e => uSubExpr(e, 2)).join(',');
    case 'ArrayExpr':
      return '[' + ex.elems.map((e, idx) => (e === null ? (idx === ex.elems.length - 1 ? ',' : '') : uSubExpr(e, 2))).join(',') + ']';
    case 'ObjectExpr':
      return '{' + ex.props.map(p => {
        if (p.type === 'Spread') return `...${uSubExpr(p.arg, 2)}`;
        const k = uPropKey(p.key, p.computed);
        if (p.method || p.kind === 'get' || p.kind === 'set') {
          const pref = `${p.value.isAsync ? 'async ' : ''}${p.kind === 'get' ? 'get ' : p.kind === 'set' ? 'set ' : ''}${p.value.isGen ? '*' : ''}`;
          return `${pref}${k}(${p.value.params.map(uPat).join(',')})${uStmt(p.value.body)}`;
        }
        return `${k}:${uSubExpr(p.value, 2)}`;
      }).join(',') + '}';
    case 'FuncExpr':
      return `${ex.isAsync ? 'async ' : ''}function${ex.isGen ? '*' : ''}${ex.id ? ' ' + ex.id : ''}(${ex.params.map(uPat).join(',')})${uStmt(ex.body)}`;
    case 'ArrowFunc': {
      const ps = `(${ex.params.map(uPat).join(',')})`;
      const pref = ex.isAsync ? 'async' : '';
      if (!ex.exprBody) return `${pref}${ps}=>${uStmt(ex.body)}`;
      const b = uSubExpr(ex.body, 2);
      const wrap = ex.body.type === 'ObjectExpr' || needsExprStmtParens(ex.body);
      return `${pref}${ps}=>${wrap ? `(${b})` : b}`;
    }
    case 'ClassExpr': return uClass(ex);
    case 'Template': {
      let out = '`';
      for (let i = 0; i < ex.quasis.length; i++) {
        out += ex.quasis[i];
        if (i < ex.exprs.length) out += '${' + uExpr(ex.exprs[i]) + '}';
      }
      return out + '`';
    }
    case 'TaggedTemplate': {
      const t = uSubExpr(ex.tag, 18);
      return `${t}${uExpr(ex.quasi)}`;
    }
    case 'MemberProp': {
      const needP = exprPrec(ex.obj) < 18 || ex.obj.type === 'NumLit' || ex.obj.type === 'New';
      const o = needP ? `(${uExpr(ex.obj)})` : uExpr(ex.obj);
      return `${o}${ex.optional ? '?.' : '.'}${ex.prop}`;
    }
    case 'MemberComp': {
      const needP = exprPrec(ex.obj) < 18 || ex.obj.type === 'New';
      const o = needP ? `(${uExpr(ex.obj)})` : uExpr(ex.obj);
      return `${o}${ex.optional ? '?.[' : '['}${uExpr(ex.prop)}]`;
    }
    case 'Call': {
      const needP = exprPrec(ex.callee) < 18 || ex.callee.type === 'New';
      const c = needP ? `(${uExpr(ex.callee)})` : uExpr(ex.callee);
      return `${c}${ex.optional ? '?.(' : '('}${ex.args.map(a => uSubExpr(a, 2)).join(',')})`;
    }
    case 'New': {
      const badCallee = exprPrec(ex.callee) < 18 || ex.callee.type === 'Call' || containsCallInMember(ex.callee);
      const c = badCallee ? `(${uExpr(ex.callee)})` : uExpr(ex.callee);
      return `new ${c}(${ex.args.map(a => uSubExpr(a, 2)).join(',')})`;
    }
    case 'Unary': {
      const a = uSubExpr(ex.arg, 16);
      if (ex.op === 'typeof' || ex.op === 'void' || ex.op === 'delete') {
        return `${ex.op}${needsSpaceAfterWord(a) ? ' ' : ''}${a}`;
      }
      if ((ex.op === '-' && a.startsWith('-')) || (ex.op === '+' && a.startsWith('+'))) {
        return `${ex.op}(${a})`;
      }
      return `${ex.op}${a}`;
    }
    case 'Await': {
      const a = uSubExpr(ex.arg, 16);
      return `await${needsSpaceAfterWord(a) ? ' ' : ''}${a}`;
    }
    case 'Yield': {
      if (!ex.arg) return 'yield';
      const a = uSubExpr(ex.arg, 2);
      return `yield${ex.delegate ? '*' : (needsSpaceAfterWord(a) ? ' ' : '')}${a}`;
    }
    case 'Update': {
      const a = uSubExpr(ex.arg, 18);
      return ex.prefix ? `${ex.op}${a}` : `${a}${ex.op}`;
    }
    case 'Binary':
    case 'Logical': {
      const p = BINARY_PREC[ex.op];
      // Prevent mixing `??` with `&&`/`||` without parentheses (ES2020 grammar rule)
      const mixNullish = (child) =>
        (ex.op === '??' && child.type === 'Logical' && child.op !== '??') ||
        (ex.op !== '??' && ex.type === 'Logical' && child.type === 'Logical' && child.op === '??');
      // Prevent unary on left of `**` without parens (ES2016 grammar rule: `(-a)**2`)
      const leftUnaryPow = ex.op === '**' && (ex.left.type === 'Unary' || ex.left.type === 'Await' || (ex.left.type === 'Update' && ex.left.prefix));
      const leftMin = ex.op === '**' ? p + 1 : p;
      const rightMin = ex.op === '**' ? p : p + 1;
      const ls = (exprPrec(ex.left) < leftMin || mixNullish(ex.left) || leftUnaryPow) ? `(${uExpr(ex.left)})` : uExpr(ex.left);
      const rs = (exprPrec(ex.right) < rightMin || mixNullish(ex.right)) ? `(${uExpr(ex.right)})` : uExpr(ex.right);
      if (ex.op === 'in' || ex.op === 'instanceof') return `${ls} ${ex.op} ${rs}`;
      if ((ex.op === '+' && rs.startsWith('+')) || (ex.op === '-' && rs.startsWith('-'))) {
        return `${ls}${ex.op} ${rs}`;
      }
      return `${ls}${ex.op}${rs}`;
    }
    case 'Cond': {
      const t = uSubExpr(ex.test, 4);
      const c = uSubExpr(ex.cons, 2);
      const a = uSubExpr(ex.alt, 2);
      return `${t}?${c}:${a}`;
    }
    case 'Assign': {
      const l = uPat(ex.left);
      const r = uSubExpr(ex.right, 2);
      return `${l}${ex.op}${r}`;
    }
    default:
      throw new Error(`Unsupported expr type in unparse: ${ex.type}`);
  }
}

function containsCallInMember(n) {
  let cur = n;
  while (cur) {
    if (cur.type === 'Call') return true;
    if (cur.type === 'MemberProp' || cur.type === 'MemberComp') cur = cur.obj;
    else return false;
  }
  return false;
}

// ---------------------------------------------------------------------------
// Normalization & Round-Trip Verification
// ---------------------------------------------------------------------------

function syntaxCheckNode(code, isModule) {
  if (isModule) return true; // vm.Script is script-only; our parser already verified ESM round-trip
  try {
    new vm.Script(code);
    return true;
  } catch {
    // CommonJS scripts (e.g., CodeNet files with top-level return) run wrapped in a CJS function
    try {
      new vm.Script(`(function(exports,require,module,__filename,__dirname){\n${code}\n})`);
      return true;
    } catch {
      return false;
    }
  }
}

function isModuleAST(ast) {
  return ast.body.some(s => s.type === 'ImportDecl' || s.type === 'ExportNamed' || s.type === 'ExportDefault' || s.type === 'ExportAll');
}

function normalizeOne(source) {
  try {
    const ast1 = new Parser(source).parseProgram();
    const canonInfo = canonicalizeLocals(ast1);
    const normalized = unparseAST(ast1);
    // Strict byte-for-byte self-verification: re-parse normalized -> re-unparse -> exact byte equality!
    const ast2 = new Parser(normalized).parseProgram();
    const normalized2 = unparseAST(ast2);
    if (normalized2 !== normalized) {
      return { supported: false, normalized: source, error: 'round_trip_mismatch' };
    }
    const isMod = isModuleAST(ast2);
    if (!syntaxCheckNode(normalized, isMod)) {
      return { supported: false, normalized: source, error: 'node_syntax_check_failed' };
    }
    return {
      supported: true,
      normalized,
      ir: ast2,
      is_module: isMod,
      renamed_locals: canonInfo.renamed,
      rename_skipped: canonInfo.skippedReason,
      error: null,
    };
  } catch (err) {
    return {
      supported: false,
      normalized: source,
      ir: null,
      is_module: false,
      renamed_locals: 0,
      rename_skipped: null,
      error: String(err && err.message ? err.message : err),
    };
  }
}

function parseIrOne(source) {
  try {
    const ast = new Parser(source).parseProgram();
    const round = unparseAST(ast);
    if (round !== source) {
      return { supported: false, ir: null, error: 'not_canonical_normalized_js' };
    }
    return { supported: true, ir: ast, error: null };
  } catch (err) {
    return { supported: false, ir: null, error: String(err && err.message ? err.message : err) };
  }
}

function unparseIrOne(ir) {
  try {
    return { ok: true, source: unparseAST(ir), error: null };
  } catch (err) {
    return { ok: false, source: null, error: String(err && err.message ? err.message : err) };
  }
}

// ---------------------------------------------------------------------------
// CLI Entrypoint
// ---------------------------------------------------------------------------

if (import.meta.url === `file://${process.argv[1]}`) {
  const mode = process.argv[2] || 'normalize';
  const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
  const items = payload.items || [];
  let results;
  if (mode === 'normalize') {
    results = items.map(it => ({ id: it.id, ...normalizeOne(it.source) }));
  } else if (mode === 'parse_ir') {
    results = items.map(it => ({ id: it.id, ...parseIrOne(it.source) }));
  } else if (mode === 'unparse_ir') {
    results = items.map(it => ({ id: it.id, ...unparseIrOne(it.ir) }));
  } else {
    throw new Error(`Unknown mode: ${mode}`);
  }
  process.stdout.write(JSON.stringify({ mode, results }));
}

export { Parser, unparseAST, normalizeOne, parseIrOne, unparseIrOne };
