"use strict";
// Self-contained zero-dependency ES2022 JS Lexer, Recursive-Descent AST Parser,
// Scope Analyzer, and Precedence-Safe Compact Printer for B3.

const KEYWORDS = new Set([
  "break", "case", "catch", "class", "const", "continue", "debugger", "default",
  "delete", "do", "else", "export", "extends", "false", "finally", "for",
  "function", "if", "import", "in", "instanceof", "let", "new", "null", "of",
  "return", "static", "super", "switch", "this", "throw", "true", "try",
  "typeof", "var", "void", "while", "with", "yield",
]);

const REGEX_BEFORE_KEYWORDS = new Set([
  "return", "throw", "case", "delete", "void", "typeof", "in", "of",
  "instanceof", "new", "else", "do", "yield",
]);

const MULTI_OPS = [
  ">>>=", "...", "===", "!==", ">>>", "<<=", ">>=", "**=", "&&=", "||=", "??=",
  "<=", ">=", "==", "!=", "++", "--", "<<", ">>", "&&", "||", "??", "**", "=>",
  "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "?.",
];

const SINGLE_PUNCT = new Set("(){}[];,.:?+-*/%<>!&|^~=".split(""));

function isIdentStart(ch) {
  if (!ch) return false;
  const c = ch.charCodeAt(0);
  return (c >= 65 && c <= 90) || (c >= 97 && c <= 122) || c === 95 || c === 36;
}

function isIdentPart(ch) {
  if (!ch) return false;
  const c = ch.charCodeAt(0);
  return isIdentStart(ch) || (c >= 48 && c <= 57);
}

function isDigit(ch) {
  if (!ch) return false;
  const c = ch.charCodeAt(0);
  return c >= 48 && c <= 57;
}

function isHexDigit(ch) {
  if (!ch) return false;
  const c = ch.charCodeAt(0);
  return (c >= 48 && c <= 57) || (c >= 65 && c <= 70) || (c >= 97 && c <= 102);
}

function unescapeString(raw) {
  let out = "";
  for (let i = 0; i < raw.length; i++) {
    if (raw[i] !== "\\") {
      out += raw[i];
      continue;
    }
    i++;
    const ch = raw[i];
    if (ch === "n") out += "\n";
    else if (ch === "r") out += "\r";
    else if (ch === "t") out += "\t";
    else if (ch === "b") out += "\b";
    else if (ch === "f") out += "\f";
    else if (ch === "v") out += "\v";
    else if (ch === "0") out += "\0";
    else if (ch === "x") {
      out += String.fromCharCode(parseInt(raw.slice(i + 1, i + 3), 16));
      i += 2;
    } else if (ch === "u") {
      if (raw[i + 1] === "{") {
        const end = raw.indexOf("}", i + 2);
        out += String.fromCodePoint(parseInt(raw.slice(i + 2, end), 16));
        i = end;
      } else {
        out += String.fromCharCode(parseInt(raw.slice(i + 1, i + 5), 16));
        i += 4;
      }
    } else if (ch === "\n") {
      // line continuation
    } else {
      out += ch;
    }
  }
  return out;
}

function tokenize(code) {
  const tokens = [];
  let i = 0;
  const n = code.length;
  let newlineBefore = false;
  // Track parens that belong to if/while/for/with so ')' allows regex after them
  const parenKinds = [];
  const braceStack = []; // 'tpl' for template expr braces, 'blk' otherwise

  function regexAllowed() {
    if (tokens.length === 0) return true;
    const prev = tokens[tokens.length - 1];
    if (prev.type === "punct") {
      if (prev.value === ")") return prev._condClose === true;
      if (prev.value === "]" || prev.value === "++" || prev.value === "--") return false;
      return true;
    }
    if (prev.type === "keyword") {
      return REGEX_BEFORE_KEYWORDS.has(prev.value);
    }
    if (prev.type === "tpl_head" || prev.type === "tpl_mid") return true;
    return false;
  }

  function scanTemplateChunk(isHead) {
    let raw = "";
    const start = i;
    while (i < n) {
      const ch = code[i];
      if (ch === "\\") {
        raw += code[i] + (code[i + 1] || "");
        i += 2;
      } else if (ch === "`") {
        i++;
        tokens.push({
          type: isHead ? "tpl_no_sub" : "tpl_tail",
          value: unescapeString(raw),
          raw,
          newlineBefore,
          pos: start,
        });
        newlineBefore = false;
        return;
      } else if (ch === "$" && code[i + 1] === "{") {
        i += 2;
        braceStack.push("tpl");
        tokens.push({
          type: isHead ? "tpl_head" : "tpl_mid",
          value: unescapeString(raw),
          raw,
          newlineBefore,
          pos: start,
        });
        newlineBefore = false;
        return;
      } else {
        raw += ch;
        i++;
      }
    }
    throw new SyntaxError("Unterminated template literal");
  }

  while (i < n) {
    const ch = code[i];
    if (ch === " " || ch === "\t" || ch === "\r" || ch === "\f" || ch === "\v") {
      i++;
      continue;
    }
    if (ch === "\n") {
      newlineBefore = true;
      i++;
      continue;
    }
    // Line comment
    if (ch === "/" && code[i + 1] === "/") {
      i += 2;
      while (i < n && code[i] !== "\n") i++;
      continue;
    }
    // Block comment
    if (ch === "/" && code[i + 1] === "*") {
      i += 2;
      while (i < n && !(code[i] === "*" && code[i + 1] === "/")) {
        if (code[i] === "\n") newlineBefore = true;
        i++;
      }
      i += 2;
      continue;
    }
    // String literal
    if (ch === "'" || ch === '"') {
      const quote = ch;
      const start = i;
      i++;
      let raw = "";
      while (i < n && code[i] !== quote) {
        if (code[i] === "\\") {
          raw += code[i] + (code[i + 1] || "");
          i += 2;
        } else {
          raw += code[i++];
        }
      }
      if (i >= n) throw new SyntaxError("Unterminated string literal");
      i++;
      tokens.push({ type: "string", value: unescapeString(raw), raw, quote, newlineBefore, pos: start });
      newlineBefore = false;
      continue;
    }
    // Template literal
    if (ch === "`") {
      i++;
      scanTemplateChunk(true);
      continue;
    }
    // Template closing brace continuation
    if (ch === "}" && braceStack.length > 0 && braceStack[braceStack.length - 1] === "tpl") {
      braceStack.pop();
      i++;
      scanTemplateChunk(false);
      continue;
    }
    // Regex literal
    if (ch === "/" && regexAllowed()) {
      const start = i;
      i++;
      let pattern = "";
      let inClass = false;
      while (i < n) {
        const c = code[i];
        if (c === "\\") {
          pattern += c + (code[i + 1] || "");
          i += 2;
        } else if (c === "[") {
          inClass = true;
          pattern += c;
          i++;
        } else if (c === "]") {
          inClass = false;
          pattern += c;
          i++;
        } else if (c === "/" && !inClass) {
          i++;
          break;
        } else {
          pattern += c;
          i++;
        }
      }
      let flags = "";
      while (i < n && isIdentStart(code[i])) {
        flags += code[i++];
      }
      tokens.push({ type: "regex", pattern, flags, newlineBefore, pos: start });
      newlineBefore = false;
      continue;
    }
    // Number / BigInt
    if (isDigit(ch) || (ch === "." && isDigit(code[i + 1]))) {
      const start = i;
      let raw = "";
      if (ch === "0" && (code[i + 1] === "x" || code[i + 1] === "X")) {
        raw += code.slice(i, i + 2);
        i += 2;
        while (i < n && (isHexDigit(code[i]) || code[i] === "_")) raw += code[i++];
      } else if (ch === "0" && (code[i + 1] === "b" || code[i + 1] === "B")) {
        raw += code.slice(i, i + 2);
        i += 2;
        while (i < n && (code[i] === "0" || code[i] === "1" || code[i] === "_")) raw += code[i++];
      } else if (ch === "0" && (code[i + 1] === "o" || code[i + 1] === "O")) {
        raw += code.slice(i, i + 2);
        i += 2;
        while (i < n && ((code[i] >= "0" && code[i] <= "7") || code[i] === "_")) raw += code[i++];
      } else {
        while (i < n && (isDigit(code[i]) || code[i] === "_")) raw += code[i++];
        if (code[i] === "." && code[i + 1] !== ".") {
          raw += code[i++];
          while (i < n && (isDigit(code[i]) || code[i] === "_")) raw += code[i++];
        }
        if (code[i] === "e" || code[i] === "E") {
          raw += code[i++];
          if (code[i] === "+" || code[i] === "-") raw += code[i++];
          while (i < n && (isDigit(code[i]) || code[i] === "_")) raw += code[i++];
        }
      }
      if (code[i] === "n") {
        i++;
        const clean = raw.replace(/_/g, "");
        tokens.push({ type: "bigint", value: clean, raw: clean + "n", newlineBefore, pos: start });
      } else {
        const clean = raw.replace(/_/g, "");
        tokens.push({ type: "number", value: Number(clean), raw: clean, newlineBefore, pos: start });
      }
      newlineBefore = false;
      continue;
    }
    // Identifier / Keyword
    if (isIdentStart(ch)) {
      const start = i;
      let val = "";
      while (i < n && isIdentPart(code[i])) val += code[i++];
      const type = KEYWORDS.has(val) ? "keyword" : "ident";
      tokens.push({ type, value: val, newlineBefore, pos: start });
      newlineBefore = false;
      continue;
    }
    // Punctuators / Operators
    let matched = null;
    for (const op of MULTI_OPS) {
      if (code.startsWith(op, i)) {
        matched = op;
        break;
      }
    }
    if (matched) {
      tokens.push({ type: "punct", value: matched, newlineBefore, pos: i });
      i += matched.length;
      newlineBefore = false;
      continue;
    }
    if (SINGLE_PUNCT.has(ch)) {
      const tok = { type: "punct", value: ch, newlineBefore, pos: i };
      if (ch === "(") {
        const prev = tokens[tokens.length - 1];
        const isCond = prev && prev.type === "keyword" && ["if", "while", "for", "with"].includes(prev.value);
        parenKinds.push(isCond);
      } else if (ch === ")") {
        const isCond = parenKinds.pop();
        if (isCond) tok._condClose = true;
      } else if (ch === "{") {
        braceStack.push("blk");
      } else if (ch === "}") {
        braceStack.pop();
      }
      tokens.push(tok);
      i++;
      newlineBefore = false;
      continue;
    }
    throw new SyntaxError(`Unexpected character ${JSON.stringify(ch)} at pos ${i}`);
  }
  tokens.push({ type: "eof", value: "", newlineBefore, pos: n });
  return tokens;
}

const ASSIGN_OPS = new Set([
  "=", "+=", "-=", "*=", "/=", "%=", "**=", "<<=", ">>=", ">>>=", "&=", "|=", "^=", "&&=", "||=", "??=",
]);

const BIN_PRECEDENCE = {
  "??": 1,
  "||": 2,
  "&&": 3,
  "|": 4,
  "^": 5,
  "&": 6,
  "==": 7, "!=": 7, "===": 7, "!==": 7,
  "<": 8, "<=": 8, ">": 8, ">=": 8, "in": 8, "instanceof": 8,
  "<<": 9, ">>": 9, ">>>": 9,
  "+": 10, "-": 10,
  "*": 11, "/": 11, "%": 11,
  "**": 12,
};

function parse(code) {
  const tokens = tokenize(code);
  let pos = 0;

  function peek(offset = 0) {
    return tokens[Math.min(pos + offset, tokens.length - 1)];
  }
  function next() {
    return tokens[pos++];
  }
  function matchPunct(v) {
    const t = peek();
    if (t.type === "punct" && t.value === v) { pos++; return true; }
    return false;
  }
  function matchKw(v) {
    const t = peek();
    if (t.type === "keyword" && t.value === v) { pos++; return true; }
    return false;
  }
  function expectPunct(v) {
    const t = next();
    if (t.type !== "punct" || t.value !== v) {
      throw new SyntaxError(`Expected '${v}', got ${t.type}:${t.value} at ${t.pos}`);
    }
    return t;
  }
  function expectKw(v) {
    const t = next();
    if (t.type !== "keyword" || t.value !== v) {
      throw new SyntaxError(`Expected keyword '${v}', got ${t.type}:${t.value} at ${t.pos}`);
    }
    return t;
  }
  function eatSemi() {
    if (matchPunct(";")) return;
    const t = peek();
    if (t.type === "eof" || (t.type === "punct" && t.value === "}") || t.newlineBefore) return;
    throw new SyntaxError(`Expected ';' at ${t.pos}, got ${t.type}:${t.value}`);
  }
  function isIdentOrKwName(t) {
    return t.type === "ident" || t.type === "keyword";
  }

  function parseProgram() {
    const body = [];
    while (peek().type !== "eof") {
      body.push(parseStatement());
    }
    return { type: "Program", body };
  }

  function parseStatement() {
    const t = peek();
    if (t.type === "punct" && t.value === "{") return parseBlock();
    if (t.type === "punct" && t.value === ";") { next(); return { type: "EmptyStatement" }; }
    if (t.type === "keyword") {
      if (t.value === "function") return parseFunctionDecl();
      if (t.value === "class") return parseClassDecl();
      if (t.value === "let" || t.value === "const" || t.value === "var") return parseVarDecl(true);
      if (t.value === "if") return parseIf();
      if (t.value === "for") return parseFor();
      if (t.value === "while") return parseWhile();
      if (t.value === "do") return parseDoWhile();
      if (t.value === "switch") return parseSwitch();
      if (t.value === "return") return parseReturn();
      if (t.value === "throw") return parseThrow();
      if (t.value === "break") return parseBreak();
      if (t.value === "continue") return parseContinue();
      if (t.value === "try") return parseTry();
    }
    // Labeled statement: ident ':' stmt
    if (t.type === "ident" && peek(1).type === "punct" && peek(1).value === ":") {
      const label = { type: "Identifier", name: next().value };
      expectPunct(":");
      const body = parseStatement();
      return { type: "LabeledStatement", label, body };
    }
    const expr = parseExpression(true);
    eatSemi();
    return { type: "ExpressionStatement", expression: expr };
  }

  function parseBlock() {
    expectPunct("{");
    const body = [];
    while (!(peek().type === "punct" && peek().value === "}")) {
      if (peek().type === "eof") throw new SyntaxError("Unterminated block");
      body.push(parseStatement());
    }
    expectPunct("}");
    return { type: "BlockStatement", body };
  }

  function parseBindingPattern() {
    const t = peek();
    if (t.type === "punct" && t.value === "[") {
      next();
      const elements = [];
      while (!(peek().type === "punct" && peek().value === "]")) {
        if (matchPunct(",")) {
          elements.push(null);
          continue;
        }
        if (matchPunct("...")) {
          elements.push({ type: "RestElement", argument: parseBindingPattern() });
          matchPunct(",");
          break;
        }
        let elem = parseBindingPattern();
        if (matchPunct("=")) {
          elem = { type: "AssignmentPattern", left: elem, right: parseAssignment(true) };
        }
        elements.push(elem);
        if (!matchPunct(",")) break;
      }
      expectPunct("]");
      return { type: "ArrayPattern", elements };
    }
    if (t.type === "punct" && t.value === "{") {
      next();
      const properties = [];
      while (!(peek().type === "punct" && peek().value === "}")) {
        if (matchPunct("...")) {
          properties.push({ type: "RestElement", argument: parseBindingPattern() });
          matchPunct(",");
          break;
        }
        let key, computed = false, shorthand = false, value;
        if (matchPunct("[")) {
          computed = true;
          key = parseAssignment(true);
          expectPunct("]");
          expectPunct(":");
          value = parseBindingPattern();
        } else {
          const kt = next();
          if (kt.type === "ident" || kt.type === "keyword") key = { type: "Identifier", name: kt.value };
          else if (kt.type === "string" || kt.type === "number") key = { type: "Literal", value: kt.value, raw: kt.raw };
          else throw new SyntaxError(`Invalid object pattern key ${kt.value}`);
          if (matchPunct(":")) {
            value = parseBindingPattern();
          } else {
            shorthand = true;
            value = { type: "Identifier", name: kt.value };
          }
        }
        if (matchPunct("=")) {
          value = { type: "AssignmentPattern", left: value, right: parseAssignment(true) };
        }
        properties.push({ type: "Property", key, value, computed, shorthand, kind: "init" });
        if (!matchPunct(",")) break;
      }
      expectPunct("}");
      return { type: "ObjectPattern", properties };
    }
    if (t.type === "ident" || (t.type === "keyword" && t.value === "of")) {
      next();
      return { type: "Identifier", name: t.value };
    }
    throw new SyntaxError(`Expected binding pattern, got ${t.type}:${t.value} at ${t.pos}`);
  }

  function parseParams() {
    expectPunct("(");
    const params = [];
    while (!(peek().type === "punct" && peek().value === ")")) {
      if (matchPunct("...")) {
        params.push({ type: "RestElement", argument: parseBindingPattern() });
        matchPunct(",");
        break;
      }
      let param = parseBindingPattern();
      if (matchPunct("=")) {
        param = { type: "AssignmentPattern", left: param, right: parseAssignment(true) };
      }
      params.push(param);
      if (!matchPunct(",")) break;
    }
    expectPunct(")");
    return params;
  }

  function parseFunctionDecl() {
    expectKw("function");
    const generator = matchPunct("*");
    const idTok = next();
    const id = { type: "Identifier", name: idTok.value };
    const params = parseParams();
    const body = parseBlock();
    return { type: "FunctionDeclaration", id, params, body, generator };
  }

  function parseClassBody() {
    expectPunct("{");
    const body = [];
    while (!(peek().type === "punct" && peek().value === "}")) {
      if (matchPunct(";")) continue;
      const isStatic = peek().type === "keyword" && peek().value === "static" && peek(1).value !== "(";
      if (isStatic) next();
      let kind = "method";
      if (peek().type === "ident" && (peek().value === "get" || peek().value === "set") && peek(1).value !== "(") {
        kind = next().value;
      }
      let key, computed = false;
      if (matchPunct("[")) {
        computed = true;
        key = parseAssignment(true);
        expectPunct("]");
      } else {
        const kt = next();
        key = isIdentOrKwName(kt)
          ? { type: "Identifier", name: kt.value }
          : { type: "Literal", value: kt.value, raw: kt.raw };
      }
      if (!computed && key.type === "Identifier" && key.name === "constructor" && !isStatic && kind === "method") {
        kind = "constructor";
      }
      const params = parseParams();
      const fnBody = parseBlock();
      body.push({
        type: "MethodDefinition",
        key,
        computed,
        static: isStatic,
        kind,
        value: { type: "FunctionExpression", id: null, params, body: fnBody, generator: false },
      });
    }
    expectPunct("}");
    return { type: "ClassBody", body };
  }

  function parseClassDecl() {
    expectKw("class");
    const id = { type: "Identifier", name: next().value };
    let superClass = null;
    if (matchKw("extends")) superClass = parseLeftHandSide();
    const body = parseClassBody();
    return { type: "ClassDeclaration", id, superClass, body };
  }

  function parseVarDecl(withSemi, allowIn = true) {
    const kind = next().value;
    const declarations = [];
    do {
      const id = parseBindingPattern();
      let init = null;
      if (matchPunct("=")) init = parseAssignment(allowIn);
      declarations.push({ type: "VariableDeclarator", id, init });
    } while (matchPunct(","));
    if (withSemi) eatSemi();
    return { type: "VariableDeclaration", kind, declarations };
  }

  function parseIf() {
    expectKw("if");
    expectPunct("(");
    const test = parseExpression(true);
    expectPunct(")");
    const consequent = parseStatement();
    let alternate = null;
    if (matchKw("else")) alternate = parseStatement();
    return { type: "IfStatement", test, consequent, alternate };
  }

  function parseFor() {
    expectKw("for");
    expectPunct("(");
    let init = null;
    if (!(peek().type === "punct" && peek().value === ";")) {
      const t = peek();
      if (t.type === "keyword" && (t.value === "let" || t.value === "const" || t.value === "var")) {
        init = parseVarDecl(false, false);
        if (matchKw("of")) {
          const right = parseExpression(true);
          expectPunct(")");
          return { type: "ForOfStatement", left: init, right, body: parseStatement() };
        }
        if (matchKw("in")) {
          const right = parseExpression(true);
          expectPunct(")");
          return { type: "ForInStatement", left: init, right, body: parseStatement() };
        }
      } else {
        const expr = parseExpression(false);
        if (matchKw("of")) {
          const right = parseExpression(true);
          expectPunct(")");
          return { type: "ForOfStatement", left: expr, right, body: parseStatement() };
        }
        if (matchKw("in")) {
          const right = parseExpression(true);
          expectPunct(")");
          return { type: "ForInStatement", left: expr, right, body: parseStatement() };
        }
        init = expr;
      }
    }
    expectPunct(";");
    let test = null;
    if (!(peek().type === "punct" && peek().value === ";")) test = parseExpression(true);
    expectPunct(";");
    let update = null;
    if (!(peek().type === "punct" && peek().value === ")")) update = parseExpression(true);
    expectPunct(")");
    return { type: "ForStatement", init, test, update, body: parseStatement() };
  }

  function parseWhile() {
    expectKw("while");
    expectPunct("(");
    const test = parseExpression(true);
    expectPunct(")");
    return { type: "WhileStatement", test, body: parseStatement() };
  }

  function parseDoWhile() {
    expectKw("do");
    const body = parseStatement();
    expectKw("while");
    expectPunct("(");
    const test = parseExpression(true);
    expectPunct(")");
    matchPunct(";");
    return { type: "DoWhileStatement", body, test };
  }

  function parseSwitch() {
    expectKw("switch");
    expectPunct("(");
    const discriminant = parseExpression(true);
    expectPunct(")");
    expectPunct("{");
    const cases = [];
    while (!(peek().type === "punct" && peek().value === "}")) {
      let test = null;
      if (matchKw("case")) {
        test = parseExpression(true);
        expectPunct(":");
      } else if (matchKw("default")) {
        expectPunct(":");
      } else {
        throw new SyntaxError("Expected case/default in switch");
      }
      const consequent = [];
      while (
        !(peek().type === "punct" && peek().value === "}") &&
        !(peek().type === "keyword" && (peek().value === "case" || peek().value === "default"))
      ) {
        consequent.push(parseStatement());
      }
      cases.push({ type: "SwitchCase", test, consequent });
    }
    expectPunct("}");
    return { type: "SwitchStatement", discriminant, cases };
  }

  function parseReturn() {
    expectKw("return");
    const t = peek();
    if (t.type === "eof" || (t.type === "punct" && (t.value === ";" || t.value === "}")) || t.newlineBefore) {
      matchPunct(";");
      return { type: "ReturnStatement", argument: null };
    }
    const argument = parseExpression(true);
    eatSemi();
    return { type: "ReturnStatement", argument };
  }

  function parseThrow() {
    expectKw("throw");
    const argument = parseExpression(true);
    eatSemi();
    return { type: "ThrowStatement", argument };
  }

  function parseBreak() {
    expectKw("break");
    let label = null;
    const t = peek();
    if (t.type === "ident" && !t.newlineBefore) label = { type: "Identifier", name: next().value };
    eatSemi();
    return { type: "BreakStatement", label };
  }

  function parseContinue() {
    expectKw("continue");
    let label = null;
    const t = peek();
    if (t.type === "ident" && !t.newlineBefore) label = { type: "Identifier", name: next().value };
    eatSemi();
    return { type: "ContinueStatement", label };
  }

  function parseTry() {
    expectKw("try");
    const block = parseBlock();
    let handler = null;
    if (matchKw("catch")) {
      let param = null;
      if (matchPunct("(")) {
        param = parseBindingPattern();
        expectPunct(")");
      }
      handler = { type: "CatchClause", param, body: parseBlock() };
    }
    let finalizer = null;
    if (matchKw("finally")) finalizer = parseBlock();
    return { type: "TryStatement", block, handler, finalizer };
  }

  function parseExpression(allowIn) {
    const first = parseAssignment(allowIn);
    if (!(peek().type === "punct" && peek().value === ",")) return first;
    const expressions = [first];
    while (matchPunct(",")) expressions.push(parseAssignment(allowIn));
    return { type: "SequenceExpression", expressions };
  }

  function tryParseArrow(allowIn) {
    const saved = pos;
    try {
      let params;
      if (peek().type === "ident" && peek(1).type === "punct" && peek(1).value === "=>" && !peek(1).newlineBefore) {
        params = [{ type: "Identifier", name: next().value }];
      } else if (peek().type === "punct" && peek().value === "(") {
        params = parseParams();
        if (!(peek().type === "punct" && peek().value === "=>" && !peek().newlineBefore)) {
          pos = saved;
          return null;
        }
      } else {
        return null;
      }
      expectPunct("=>");
      let body, expression;
      if (peek().type === "punct" && peek().value === "{") {
        body = parseBlock();
        expression = false;
      } else {
        body = parseAssignment(allowIn);
        expression = true;
      }
      return { type: "ArrowFunctionExpression", params, body, expression };
    } catch {
      pos = saved;
      return null;
    }
  }

  function exprToPattern(node) {
    if (!node) return node;
    if (node.type === "ArrayExpression") {
      return {
        type: "ArrayPattern",
        elements: node.elements.map(e => {
          if (!e) return null;
          if (e.type === "SpreadElement") return { type: "RestElement", argument: exprToPattern(e.argument) };
          if (e.type === "AssignmentExpression" && e.operator === "=") {
            return { type: "AssignmentPattern", left: exprToPattern(e.left), right: e.right };
          }
          return exprToPattern(e);
        }),
      };
    }
    if (node.type === "ObjectExpression") {
      return {
        type: "ObjectPattern",
        properties: node.properties.map(p => {
          if (p.type === "SpreadElement") return { type: "RestElement", argument: exprToPattern(p.argument) };
          return { ...p, value: exprToPattern(p.value) };
        }),
      };
    }
    return node;
  }

  function parseAssignment(allowIn) {
    const arrow = tryParseArrow(allowIn);
    if (arrow) return arrow;
    const left = parseConditional(allowIn);
    const t = peek();
    if (t.type === "punct" && ASSIGN_OPS.has(t.value)) {
      const operator = next().value;
      const right = parseAssignment(allowIn);
      return { type: "AssignmentExpression", operator, left: operator === "=" ? exprToPattern(left) : left, right };
    }
    return left;
  }

  function parseConditional(allowIn) {
    const test = parseBinary(allowIn, 1);
    if (!matchPunct("?")) return test;
    const consequent = parseAssignment(true);
    expectPunct(":");
    const alternate = parseAssignment(allowIn);
    return { type: "ConditionalExpression", test, consequent, alternate };
  }

  function parseBinary(allowIn, minPrec) {
    let left = parseUnary();
    while (true) {
      const t = peek();
      let op = null;
      if (t.type === "punct" && t.value in BIN_PRECEDENCE) op = t.value;
      else if (t.type === "keyword" && (t.value === "instanceof" || (allowIn && t.value === "in"))) op = t.value;
      if (op === null) break;
      const prec = BIN_PRECEDENCE[op];
      if (prec < minPrec) break;
      next();
      const nextMin = op === "**" ? prec : prec + 1;
      const right = parseBinary(allowIn, nextMin);
      const nodeType = (op === "&&" || op === "||" || op === "??") ? "LogicalExpression" : "BinaryExpression";
      left = { type: nodeType, operator: op, left, right };
    }
    return left;
  }

  function parseUnary() {
    const t = peek();
    if (
      (t.type === "punct" && ["+", "-", "!", "~"].includes(t.value)) ||
      (t.type === "keyword" && ["typeof", "void", "delete"].includes(t.value))
    ) {
      const operator = next().value;
      return { type: "UnaryExpression", operator, prefix: true, argument: parseUnary() };
    }
    if (t.type === "punct" && (t.value === "++" || t.value === "--")) {
      const operator = next().value;
      return { type: "UpdateExpression", operator, prefix: true, argument: parseUnary() };
    }
    let expr = parseLeftHandSide();
    const nxt = peek();
    if (nxt.type === "punct" && (nxt.value === "++" || nxt.value === "--") && !nxt.newlineBefore) {
      const operator = next().value;
      expr = { type: "UpdateExpression", operator, prefix: false, argument: expr };
    }
    return expr;
  }

  function parseArguments() {
    expectPunct("(");
    const args = [];
    while (!(peek().type === "punct" && peek().value === ")")) {
      if (matchPunct("...")) {
        args.push({ type: "SpreadElement", argument: parseAssignment(true) });
      } else {
        args.push(parseAssignment(true));
      }
      if (!matchPunct(",")) break;
    }
    expectPunct(")");
    return args;
  }

  function parseMemberAndNew(allowCall) {
    let expr;
    if (matchKw("new")) {
      const callee = parseMemberAndNew(false);
      const args = (peek().type === "punct" && peek().value === "(") ? parseArguments() : [];
      expr = { type: "NewExpression", callee, arguments: args };
    } else {
      expr = parsePrimary();
    }
    while (true) {
      if (matchPunct(".")) {
        const prop = next();
        if (!isIdentOrKwName(prop)) throw new SyntaxError(`Expected property name at ${prop.pos}`);
        expr = { type: "MemberExpression", object: expr, property: { type: "Identifier", name: prop.value }, computed: false, optional: false };
      } else if (matchPunct("?.")) {
        if (peek().type === "punct" && peek().value === "[") {
          next();
          const property = parseExpression(true);
          expectPunct("]");
          expr = { type: "MemberExpression", object: expr, property, computed: true, optional: true };
        } else if (allowCall && peek().type === "punct" && peek().value === "(") {
          expr = { type: "CallExpression", callee: expr, arguments: parseArguments(), optional: true };
        } else {
          const prop = next();
          expr = { type: "MemberExpression", object: expr, property: { type: "Identifier", name: prop.value }, computed: false, optional: true };
        }
      } else if (matchPunct("[")) {
        const property = parseExpression(true);
        expectPunct("]");
        expr = { type: "MemberExpression", object: expr, property, computed: true, optional: false };
      } else if (allowCall && peek().type === "punct" && peek().value === "(") {
        expr = { type: "CallExpression", callee: expr, arguments: parseArguments(), optional: false };
      } else {
        break;
      }
    }
    return expr;
  }

  function parseLeftHandSide() {
    return parseMemberAndNew(true);
  }

  function parsePrimary() {
    const t = peek();
    if (t.type === "ident" || (t.type === "keyword" && t.value === "of")) {
      next();
      return { type: "Identifier", name: t.value };
    }
    if (t.type === "keyword") {
      if (t.value === "this") { next(); return { type: "ThisExpression" }; }
      if (t.value === "super") { next(); return { type: "Super" }; }
      if (t.value === "true") { next(); return { type: "Literal", value: true, raw: "true" }; }
      if (t.value === "false") { next(); return { type: "Literal", value: false, raw: "false" }; }
      if (t.value === "null") { next(); return { type: "Literal", value: null, raw: "null" }; }
      if (t.value === "function") {
        next();
        const generator = matchPunct("*");
        let id = null;
        if (peek().type === "ident") id = { type: "Identifier", name: next().value };
        const params = parseParams();
        const body = parseBlock();
        return { type: "FunctionExpression", id, params, body, generator };
      }
      if (t.value === "class") {
        next();
        let id = null;
        if (peek().type === "ident") id = { type: "Identifier", name: next().value };
        let superClass = null;
        if (matchKw("extends")) superClass = parseLeftHandSide();
        return { type: "ClassExpression", id, superClass, body: parseClassBody() };
      }
    }
    if (t.type === "number") {
      next();
      return { type: "Literal", value: t.value, raw: t.raw };
    }
    if (t.type === "bigint") {
      next();
      return { type: "Literal", value: null, bigint: t.value, raw: t.raw };
    }
    if (t.type === "string") {
      next();
      return { type: "Literal", value: t.value, raw: t.raw, isString: true };
    }
    if (t.type === "regex") {
      next();
      return { type: "Literal", value: null, regex: { pattern: t.pattern, flags: t.flags }, raw: `/${t.pattern}/${t.flags}` };
    }
    if (t.type === "tpl_no_sub") {
      next();
      return { type: "TemplateLiteral", quasis: [{ value: t.value, raw: t.raw }], expressions: [] };
    }
    if (t.type === "tpl_head") {
      next();
      const quasis = [{ value: t.value, raw: t.raw }];
      const expressions = [];
      while (true) {
        expressions.push(parseExpression(true));
        const nxt = next();
        if (nxt.type === "tpl_mid") {
          quasis.push({ value: nxt.value, raw: nxt.raw });
        } else if (nxt.type === "tpl_tail") {
          quasis.push({ value: nxt.value, raw: nxt.raw });
          break;
        } else {
          throw new SyntaxError(`Expected template continuation, got ${nxt.type}`);
        }
      }
      return { type: "TemplateLiteral", quasis, expressions };
    }
    if (matchPunct("(")) {
      const expr = parseExpression(true);
      expectPunct(")");
      return expr;
    }
    if (matchPunct("[")) {
      const elements = [];
      while (!(peek().type === "punct" && peek().value === "]")) {
        if (matchPunct(",")) {
          elements.push(null);
          continue;
        }
        if (matchPunct("...")) elements.push({ type: "SpreadElement", argument: parseAssignment(true) });
        else elements.push(parseAssignment(true));
        if (!matchPunct(",")) break;
      }
      expectPunct("]");
      return { type: "ArrayExpression", elements };
    }
    if (matchPunct("{")) {
      const properties = [];
      while (!(peek().type === "punct" && peek().value === "}")) {
        if (matchPunct("...")) {
          properties.push({ type: "SpreadElement", argument: parseAssignment(true) });
          if (!matchPunct(",")) break;
          continue;
        }
        let key, computed = false, shorthand = false, method = false, value;
        if (matchPunct("[")) {
          computed = true;
          key = parseAssignment(true);
          expectPunct("]");
        } else {
          const kt = next();
          if (isIdentOrKwName(kt)) key = { type: "Identifier", name: kt.value };
          else if (kt.type === "string") key = { type: "Literal", value: kt.value, raw: kt.raw, isString: true };
          else if (kt.type === "number") key = { type: "Literal", value: kt.value, raw: kt.raw };
          else throw new SyntaxError(`Invalid object key ${kt.value}`);
        }
        if (matchPunct(":")) {
          value = parseAssignment(true);
        } else if (peek().type === "punct" && peek().value === "(") {
          method = true;
          const params = parseParams();
          const body = parseBlock();
          value = { type: "FunctionExpression", id: null, params, body, generator: false };
        } else {
          shorthand = true;
          value = { type: "Identifier", name: key.name };
        }
        properties.push({ type: "Property", key, value, computed, shorthand, method, kind: "init" });
        if (!matchPunct(",")) break;
      }
      expectPunct("}");
      return { type: "ObjectExpression", properties };
    }
    throw new SyntaxError(`Unexpected token ${t.type}:${t.value} at ${t.pos}`);
  }

  return parseProgram();
}

function escapeSingleQuoted(s) {
  let out = "";
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (ch === "\\") out += "\\\\";
    else if (ch === "'") out += "\\'";
    else if (ch === "\n") out += "\\n";
    else if (ch === "\r") out += "\\r";
    else if (ch === "\t") out += "\\t";
    else out += ch;
  }
  return "'" + out + "'";
}

function exprPrec(node) {
  switch (node.type) {
    case "SequenceExpression": return 0;
    case "AssignmentExpression":
    case "ArrowFunctionExpression": return 1;
    case "ConditionalExpression": return 2;
    case "LogicalExpression":
    case "BinaryExpression": return 2 + BIN_PRECEDENCE[node.operator];
    case "UnaryExpression": return 15;
    case "UpdateExpression": return node.prefix ? 15 : 16;
    case "NewExpression": return node.arguments.length ? 18 : 17;
    case "CallExpression":
    case "MemberExpression": return 18;
    default: return 20;
  }
}

function generate(node, opts = {}) {
  const minimalBraces = opts.minimalBraces === true;
  const canonicalKeywords = opts.canonicalKeywords === true;

  function needSpace(a, b) {
    if (!a || !b) return false;
    const lc = a[a.length - 1];
    const fc = b[0];
    if (isIdentPart(lc) && isIdentPart(fc)) return true;
    if (lc === "+" && fc === "+") return true;
    if (lc === "-" && fc === "-") return true;
    return false;
  }

  function joinSafe(a, b) {
    return needSpace(a, b) ? a + " " + b : a + b;
  }

  function genStmt(s, omitTrailingSemi = false) {
    if (!s) return "";
    switch (s.type) {
      case "Program":
        return s.body.map(st => genStmt(st)).join("");
      case "EmptyStatement":
        return ";";
      case "BlockStatement":
        return "{" + s.body.map(st => genStmt(st)).join("") + "}";
      case "ExpressionStatement": {
        let e = genExpr(s.expression);
        if (e.startsWith("{") || e.startsWith("function") || e.startsWith("class")) e = "(" + e + ")";
        return e + (omitTrailingSemi ? "" : ";");
      }
      case "VariableDeclaration": {
        const decls = s.declarations.map(d => {
          const lhs = genPattern(d.id);
          return d.init ? lhs + "=" + genExpr(d.init, 1) : lhs;
        }).join(",");
        return s.kind + " " + decls + (omitTrailingSemi ? "" : ";");
      }
      case "FunctionDeclaration":
        return "function" + (s.generator ? "*" : " ") + s.id.name + "(" + s.params.map(genPattern).join(",") + ")" + genStmt(s.body);
      case "ClassDeclaration":
        return "class " + s.id.name + (s.superClass ? " extends " + genExpr(s.superClass, 17) : "") + genClassBody(s.body);
      case "IfStatement": {
        let cons = genBranchStmt(s.consequent, Boolean(s.alternate));
        let out = "if(" + genExpr(s.test) + ")" + cons;
        if (s.alternate) {
          if (canonicalKeywords) {
            const alt = s.alternate.type === "BlockStatement" ? genStmt(s.alternate) : "{" + genStmt(s.alternate) + "}";
            out += "else" + alt;
          } else {
            const alt = s.alternate.type === "IfStatement" ? genStmt(s.alternate) : genBranchStmt(s.alternate, false);
            out += joinSafe("else", alt);
          }
        }
        return out;
      }
      case "ForStatement": {
        const init = s.init
          ? (s.init.type === "VariableDeclaration" ? genStmt(s.init, true) : genExpr(s.init))
          : "";
        const test = s.test ? genExpr(s.test) : "";
        const upd = s.update ? genExpr(s.update) : "";
        return "for(" + init + ";" + test + ";" + upd + ")" + genBranchStmt(s.body, false);
      }
      case "ForOfStatement": {
        const left = s.left.type === "VariableDeclaration" ? genStmt(s.left, true) : genExpr(s.left);
        return "for(" + left + " of " + genExpr(s.right, 1) + ")" + genBranchStmt(s.body, false);
      }
      case "ForInStatement": {
        const left = s.left.type === "VariableDeclaration" ? genStmt(s.left, true) : genExpr(s.left);
        return "for(" + left + " in " + genExpr(s.right, 1) + ")" + genBranchStmt(s.body, false);
      }
      case "WhileStatement":
        return "while(" + genExpr(s.test) + ")" + genBranchStmt(s.body, false);
      case "DoWhileStatement":
        return joinSafe("do", genStmt(s.body)) + "while(" + genExpr(s.test) + ");";
      case "SwitchStatement":
        return "switch(" + genExpr(s.discriminant) + "){" + s.cases.map(c =>
          (c.test ? "case " + genExpr(c.test) + ":" : "default:") + c.consequent.map(st => genStmt(st)).join("")
        ).join("") + "}";
      case "ReturnStatement":
        if (!s.argument) return "return;";
        if (canonicalKeywords) {
          const arg = genExpr(s.argument);
          return (arg[0] === "(" || arg[0] === "[" || arg[0] === "{" || arg[0] === "!" || arg[0] === "-" || arg[0] === "'")
            ? "return" + arg + ";"
            : "return(" + arg + ");";
        }
        return joinSafe("return", genExpr(s.argument)) + ";";
      case "ThrowStatement":
        if (canonicalKeywords) return "throw(" + genExpr(s.argument) + ");";
        return joinSafe("throw", genExpr(s.argument)) + ";";
      case "BreakStatement":
        return (s.label ? "break " + s.label.name : "break") + ";";
      case "ContinueStatement":
        return (s.label ? "continue " + s.label.name : "continue") + ";";
      case "TryStatement":
        return "try" + genStmt(s.block)
          + (s.handler ? "catch" + (s.handler.param ? "(" + genPattern(s.handler.param) + ")" : "") + genStmt(s.handler.body) : "")
          + (s.finalizer ? "finally" + genStmt(s.finalizer) : "");
      case "LabeledStatement":
        return s.label.name + ":" + genStmt(s.body);
      default:
        throw new Error(`Unsupported statement type: ${s.type}`);
    }
  }

  function endsWithDanglingIf(s) {
    if (!s) return false;
    if (s.type === "IfStatement") return !s.alternate || endsWithDanglingIf(s.alternate);
    if (s.type === "ForStatement" || s.type === "ForOfStatement" || s.type === "ForInStatement" || s.type === "WhileStatement") {
      return endsWithDanglingIf(s.body);
    }
    return false;
  }

  function genBranchStmt(s, hasElseFollowing) {
    if (minimalBraces && s.type === "BlockStatement" && s.body.length === 1) {
      const inner = s.body[0];
      const safeInner = inner.type !== "VariableDeclaration" && inner.type !== "FunctionDeclaration" && inner.type !== "ClassDeclaration";
      if (safeInner && !(hasElseFollowing && endsWithDanglingIf(inner))) {
        return genStmt(inner);
      }
    }
    if (hasElseFollowing && endsWithDanglingIf(s)) {
      return "{" + genStmt(s) + "}";
    }
    return genStmt(s);
  }

  function genClassBody(cb) {
    return "{" + cb.body.map(m => {
      const prefix = (m.static ? "static " : "") + (m.kind === "get" || m.kind === "set" ? m.kind + " " : "");
      const key = m.computed ? "[" + genExpr(m.key, 1) + "]" : (m.key.type === "Identifier" ? m.key.name : genExpr(m.key));
      return prefix + key + "(" + m.value.params.map(genPattern).join(",") + ")" + genStmt(m.value.body);
    }).join("") + "}";
  }

  function genPattern(p) {
    if (!p) return "";
    switch (p.type) {
      case "Identifier": return p.name;
      case "RestElement": return "..." + genPattern(p.argument);
      case "AssignmentPattern": return genPattern(p.left) + "=" + genExpr(p.right, 1);
      case "ArrayPattern": return "[" + p.elements.map(e => e ? genPattern(e) : "").join(",") + "]";
      case "ObjectPattern":
        return "{" + p.properties.map(pr => {
          if (pr.type === "RestElement") return "..." + genPattern(pr.argument);
          if (pr.shorthand && pr.value.type === "Identifier" && pr.key.name === pr.value.name) return pr.key.name;
          if (pr.shorthand && pr.value.type === "AssignmentPattern" && pr.value.left.type === "Identifier" && pr.key.name === pr.value.left.name) {
            return genPattern(pr.value);
          }
          const k = pr.computed ? "[" + genExpr(pr.key, 1) + "]" : (pr.key.type === "Identifier" ? pr.key.name : genExpr(pr.key));
          return k + ":" + genPattern(pr.value);
        }).join(",") + "}";
      default:
        return genExpr(p);
    }
  }

  function genExpr(e, minPrec = 0) {
    const p = exprPrec(e);
    let out;
    switch (e.type) {
      case "Identifier": out = e.name; break;
      case "ThisExpression": out = "this"; break;
      case "Super": out = "super"; break;
      case "Literal":
        if (e.regex) out = `/${e.regex.pattern}/${e.regex.flags}`;
        else if (e.bigint !== undefined) out = e.bigint + "n";
        else if (e.isString || typeof e.value === "string") out = escapeSingleQuoted(e.value);
        else if (e.value === null) out = "null";
        else if (typeof e.value === "boolean") out = e.value ? "true" : "false";
        else out = e.raw !== undefined ? String(e.raw) : String(e.value);
        break;
      case "TemplateLiteral": {
        out = "`";
        for (let i = 0; i < e.quasis.length; i++) {
          out += e.quasis[i].raw;
          if (i < e.expressions.length) out += "${" + genExpr(e.expressions[i]) + "}";
        }
        out += "`";
        break;
      }
      case "ArrayExpression":
        out = "[" + e.elements.map(el => {
          if (!el) return "";
          if (el.type === "SpreadElement") return "..." + genExpr(el.argument, 1);
          return genExpr(el, 1);
        }).join(",") + "]";
        break;
      case "ObjectExpression":
        out = "{" + e.properties.map(pr => {
          if (pr.type === "SpreadElement") return "..." + genExpr(pr.argument, 1);
          const k = pr.computed ? "[" + genExpr(pr.key, 1) + "]" : (pr.key.type === "Identifier" ? pr.key.name : genExpr(pr.key));
          if (pr.method) {
            return k + "(" + pr.value.params.map(genPattern).join(",") + ")" + genStmt(pr.value.body);
          }
          if (pr.shorthand && pr.key.type === "Identifier" && pr.value.type === "Identifier" && pr.key.name === pr.value.name) {
            return k;
          }
          return k + ":" + genExpr(pr.value, 1);
        }).join(",") + "}";
        break;
      case "FunctionExpression":
        if (canonicalKeywords) {
          out = "function " + (e.id ? e.id.name : "") + "(" + e.params.map(genPattern).join(",") + ")" + genStmt(e.body);
        } else {
          out = "function" + (e.generator ? "*" : "") + (e.id ? " " + e.id.name : "") + "(" + e.params.map(genPattern).join(",") + ")" + genStmt(e.body);
        }
        break;
      case "ClassExpression":
        out = "class" + (e.id ? " " + e.id.name : "") + (e.superClass ? " extends " + genExpr(e.superClass, 17) : "") + genClassBody(e.body);
        break;
      case "ArrowFunctionExpression": {
        const ps = (e.params.length === 1 && e.params[0].type === "Identifier")
          ? e.params[0].name
          : "(" + e.params.map(genPattern).join(",") + ")";
        let body = e.expression ? genExpr(e.body, 1) : genStmt(e.body);
        if (e.expression && body.startsWith("{")) body = "(" + body + ")";
        out = ps + "=>" + body;
        break;
      }
      case "MemberExpression": {
        let obj = genExpr(e.object, 18);
        // Numeric literal followed by dot needs parens: (1).toString()
        if (!e.computed && e.object.type === "Literal" && typeof e.object.value === "number") obj = "(" + obj + ")";
        if (e.computed) out = obj + (e.optional ? "?." : "") + "[" + genExpr(e.property) + "]";
        else out = obj + (e.optional ? "?." : ".") + e.property.name;
        break;
      }
      case "CallExpression": {
        const callee = genExpr(e.callee, 18);
        const args = e.arguments.map(a => a.type === "SpreadElement" ? "..." + genExpr(a.argument, 1) : genExpr(a, 1)).join(",");
        out = callee + (e.optional ? "?.(" : "(") + args + ")";
        break;
      }
      case "NewExpression": {
        const callee = genExpr(e.callee, 18);
        const args = e.arguments.map(a => a.type === "SpreadElement" ? "..." + genExpr(a.argument, 1) : genExpr(a, 1)).join(",");
        out = (canonicalKeywords ? "new " + callee : joinSafe("new", callee)) + "(" + args + ")";
        break;
      }
      case "UnaryExpression": {
        const arg = genExpr(e.argument, 15);
        out = joinSafe(e.operator, arg);
        break;
      }
      case "UpdateExpression": {
        const arg = genExpr(e.argument, 17);
        out = e.prefix ? e.operator + arg : arg + e.operator;
        break;
      }
      case "BinaryExpression":
      case "LogicalExpression": {
        const isRightAssoc = e.operator === "**";
        let lp = isRightAssoc ? p + 1 : p;
        let rp = isRightAssoc ? p : p + 1;
        // JS requires parens when mixing ?? with && or ||
        if (e.operator === "??" && (e.left.type === "LogicalExpression" && e.left.operator !== "??")) lp = p + 1;
        if ((e.operator === "&&" || e.operator === "||") && e.left.type === "LogicalExpression" && e.left.operator === "??") lp = p + 1;
        // Unary on LHS of ** requires parens in ES2016+
        if (e.operator === "**" && e.left.type === "UnaryExpression") lp = 20;
        const left = genExpr(e.left, lp);
        const right = genExpr(e.right, rp);
        out = joinSafe(joinSafe(left, e.operator), right);
        break;
      }
      case "ConditionalExpression": {
        const test = genExpr(e.test, 3);
        const cons = genExpr(e.consequent, 1);
        const alt = genExpr(e.alternate, 1);
        out = test + "?" + cons + ":" + alt;
        break;
      }
      case "AssignmentExpression":
        out = genPattern(e.left) + e.operator + genExpr(e.right, 1);
        break;
      case "SequenceExpression":
        out = e.expressions.map(x => genExpr(x, 1)).join(",");
        break;
      default:
        throw new Error(`Unsupported expression type: ${e.type}`);
    }
    return p < minPrec ? "(" + out + ")" : out;
  }

  return node.type === "Program" || node.type.endsWith("Statement") || node.type.endsWith("Declaration")
    ? genStmt(node)
    : genExpr(node);
}

function cloneAst(node) {
  return JSON.parse(JSON.stringify(node));
}

function collectPatternIdents(pat, out) {
  if (!pat) return;
  if (pat.type === "Identifier") out.push(pat);
  else if (pat.type === "RestElement") collectPatternIdents(pat.argument, out);
  else if (pat.type === "AssignmentPattern") collectPatternIdents(pat.left, out);
  else if (pat.type === "ArrayPattern") pat.elements.forEach(e => collectPatternIdents(e, out));
  else if (pat.type === "ObjectPattern") pat.properties.forEach(p => {
    if (p.type === "RestElement") collectPatternIdents(p.argument, out);
    else collectPatternIdents(p.value, out);
  });
}

function analyzeScopes(ast) {
  let nextScopeId = 0;
  let nextBindingId = 0;
  const scopes = [];
  const bindings = [];
  const nodeToBinding = new Map(); // Identifier node -> binding
  const freeRefs = [];

  function makeScope(kind, parent, node) {
    const sc = { id: nextScopeId++, kind, parent, node, vars: new Map(), children: [] };
    scopes.push(sc);
    if (parent) parent.children.push(sc);
    return sc;
  }

  function declare(sc, identNode, kind) {
    // Hoist var to nearest function/program scope
    let target = sc;
    if (kind === "var") {
      while (target.parent && target.kind !== "function" && target.kind !== "program") {
        target = target.parent;
      }
    }
    let b = target.vars.get(identNode.name);
    if (!b) {
      b = { id: nextBindingId++, name: identNode.name, kind, scope: target, defs: [], refs: [] };
      target.vars.set(identNode.name, b);
      bindings.push(b);
    }
    b.defs.push(identNode);
    nodeToBinding.set(identNode, b);
    return b;
  }

  function resolve(sc, identNode) {
    let cur = sc;
    while (cur) {
      if (cur.vars.has(identNode.name)) {
        const b = cur.vars.get(identNode.name);
        b.refs.push(identNode);
        nodeToBinding.set(identNode, b);
        return b;
      }
      cur = cur.parent;
    }
    freeRefs.push(identNode);
    return null;
  }

  function hoistStatements(stmts, sc) {
    for (const s of stmts) {
      if (!s) continue;
      if (s.type === "FunctionDeclaration" && s.id) {
        declare(sc, s.id, "func");
      } else if (s.type === "ClassDeclaration" && s.id) {
        declare(sc, s.id, "class");
      } else if (s.type === "VariableDeclaration") {
        for (const d of s.declarations) {
          const ids = [];
          collectPatternIdents(d.id, ids);
          for (const id of ids) declare(sc, id, s.kind);
        }
      } else if (s.type === "ForStatement" && s.init && s.init.type === "VariableDeclaration" && s.init.kind === "var") {
        for (const d of s.init.declarations) {
          const ids = [];
          collectPatternIdents(d.id, ids);
          for (const id of ids) declare(sc, id, "var");
        }
      }
    }
  }

  function visitPatternRefs(pat, sc, isDecl) {
    if (!pat) return;
    if (pat.type === "Identifier") {
      if (!isDecl) resolve(sc, pat);
    } else if (pat.type === "RestElement") {
      visitPatternRefs(pat.argument, sc, isDecl);
    } else if (pat.type === "AssignmentPattern") {
      visitPatternRefs(pat.left, sc, isDecl);
      visit(pat.right, sc);
    } else if (pat.type === "ArrayPattern") {
      pat.elements.forEach(e => visitPatternRefs(e, sc, isDecl));
    } else if (pat.type === "ObjectPattern") {
      for (const p of pat.properties) {
        if (p.type === "RestElement") visitPatternRefs(p.argument, sc, isDecl);
        else {
          if (p.computed) visit(p.key, sc);
          visitPatternRefs(p.value, sc, isDecl);
        }
      }
    } else {
      visit(pat, sc);
    }
  }

  function visit(node, sc) {
    if (!node) return;
    switch (node.type) {
      case "Program":
        hoistStatements(node.body, sc);
        node.body.forEach(s => visit(s, sc));
        return;
      case "BlockStatement": {
        const bsc = makeScope("block", sc, node);
        hoistStatements(node.body, bsc);
        node.body.forEach(s => visit(s, bsc));
        return;
      }
      case "FunctionDeclaration":
      case "FunctionExpression": {
        const fsc = makeScope("function", sc, node);
        if (node.type === "FunctionExpression" && node.id) declare(fsc, node.id, "func");
        for (const p of node.params) {
          const ids = [];
          collectPatternIdents(p, ids);
          ids.forEach(id => declare(fsc, id, "param"));
          visitPatternRefs(p, fsc, true);
        }
        hoistStatements(node.body.body, fsc);
        node.body.body.forEach(s => visit(s, fsc));
        return;
      }
      case "ArrowFunctionExpression": {
        const fsc = makeScope("function", sc, node);
        for (const p of node.params) {
          const ids = [];
          collectPatternIdents(p, ids);
          ids.forEach(id => declare(fsc, id, "param"));
          visitPatternRefs(p, fsc, true);
        }
        if (node.body.type === "BlockStatement") {
          hoistStatements(node.body.body, fsc);
          node.body.body.forEach(s => visit(s, fsc));
        } else {
          visit(node.body, fsc);
        }
        return;
      }
      case "ClassDeclaration":
      case "ClassExpression": {
        if (node.superClass) visit(node.superClass, sc);
        const csc = makeScope("block", sc, node);
        if (node.type === "ClassExpression" && node.id) declare(csc, node.id, "class");
        for (const m of node.body.body) {
          if (m.computed) visit(m.key, csc);
          visit(m.value, csc);
        }
        return;
      }
      case "VariableDeclaration":
        for (const d of node.declarations) {
          visitPatternRefs(d.id, sc, true);
          if (d.init) visit(d.init, sc);
        }
        return;
      case "ForStatement": {
        const fsc = makeScope("block", sc, node);
        if (node.init) {
          if (node.init.type === "VariableDeclaration") {
            if (node.init.kind !== "var") {
              for (const d of node.init.declarations) {
                const ids = [];
                collectPatternIdents(d.id, ids);
                ids.forEach(id => declare(fsc, id, node.init.kind));
              }
            }
          }
          visit(node.init, fsc);
        }
        if (node.test) visit(node.test, fsc);
        if (node.update) visit(node.update, fsc);
        visit(node.body, fsc);
        return;
      }
      case "ForOfStatement":
      case "ForInStatement": {
        const fsc = makeScope("block", sc, node);
        if (node.left.type === "VariableDeclaration") {
          for (const d of node.left.declarations) {
            const ids = [];
            collectPatternIdents(d.id, ids);
            ids.forEach(id => declare(fsc, id, node.left.kind));
          }
          visit(node.left, fsc);
        } else {
          visitPatternRefs(node.left, fsc, false);
        }
        visit(node.right, fsc);
        visit(node.body, fsc);
        return;
      }
      case "IfStatement":
        visit(node.test, sc);
        visit(node.consequent, sc);
        if (node.alternate) visit(node.alternate, sc);
        return;
      case "WhileStatement":
      case "DoWhileStatement":
        visit(node.test, sc);
        visit(node.body, sc);
        return;
      case "SwitchStatement": {
        visit(node.discriminant, sc);
        const ssc = makeScope("block", sc, node);
        for (const c of node.cases) {
          if (c.test) visit(c.test, ssc);
          hoistStatements(c.consequent, ssc);
          c.consequent.forEach(s => visit(s, ssc));
        }
        return;
      }
      case "TryStatement":
        visit(node.block, sc);
        if (node.handler) {
          const csc = makeScope("block", sc, node.handler);
          if (node.handler.param) {
            const ids = [];
            collectPatternIdents(node.handler.param, ids);
            ids.forEach(id => declare(csc, id, "catch"));
            visitPatternRefs(node.handler.param, csc, true);
          }
          hoistStatements(node.handler.body.body, csc);
          node.handler.body.body.forEach(s => visit(s, csc));
        }
        if (node.finalizer) visit(node.finalizer, sc);
        return;
      case "LabeledStatement":
        visit(node.body, sc);
        return;
      case "ReturnStatement":
      case "ThrowStatement":
        if (node.argument) visit(node.argument, sc);
        return;
      case "ExpressionStatement":
        visit(node.expression, sc);
        return;
      case "Identifier":
        resolve(sc, node);
        return;
      case "MemberExpression":
        visit(node.object, sc);
        if (node.computed) visit(node.property, sc);
        return;
      case "CallExpression":
      case "NewExpression":
        visit(node.callee, sc);
        node.arguments.forEach(a => visit(a, sc));
        return;
      case "AssignmentExpression":
        visitPatternRefs(node.left, sc, false);
        visit(node.right, sc);
        return;
      case "BinaryExpression":
      case "LogicalExpression":
        visit(node.left, sc);
        visit(node.right, sc);
        return;
      case "ConditionalExpression":
        visit(node.test, sc);
        visit(node.consequent, sc);
        visit(node.alternate, sc);
        return;
      case "UnaryExpression":
      case "UpdateExpression":
      case "SpreadElement":
        visit(node.argument, sc);
        return;
      case "SequenceExpression":
        node.expressions.forEach(x => visit(x, sc));
        return;
      case "ArrayExpression":
        node.elements.forEach(x => x && visit(x, sc));
        return;
      case "ObjectExpression":
        for (const p of node.properties) {
          if (p.type === "SpreadElement") visit(p.argument, sc);
          else {
            if (p.computed) visit(p.key, sc);
            visit(p.value, sc);
          }
        }
        return;
      case "TemplateLiteral":
        node.expressions.forEach(x => visit(x, sc));
        return;
      default:
        return;
    }
  }

  const root = makeScope("program", null, ast);
  visit(ast, root);
  return { root, scopes, bindings, nodeToBinding, freeRefs };
}

export { tokenize, parse, generate, cloneAst, analyzeScopes, KEYWORDS };
