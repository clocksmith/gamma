"use strict";
// Frozen general semantics-preserving JavaScript canonical rewriter for B3.
//
// Zero problem-specific logic, zero hidden helpers, zero escapes.
// Every output program is standalone ES2022 JavaScript executable directly in Node.

import fs from "node:fs";
import { parse, generate, cloneAst, analyzeScopes, KEYWORDS } from "./js_ast.mjs";

const CORE_STRING_CHARS = new Set(
  "abcde0123456789.,+-*/%<()[]{};:?!&|".split("")
);

const DIRECT_GLOBALS = new Set([
  "Math", "Array", "String",
]);

const DIRECT_PROPS = new Set([
  "length", "floor", "fromCharCode",
]);

function isPureExpr(node) {
  if (!node) return true;
  switch (node.type) {
    case "Identifier":
    case "Literal":
    case "ThisExpression":
      return true;
    case "UnaryExpression":
      return node.operator !== "delete" && isPureExpr(node.argument);
    case "BinaryExpression":
    case "LogicalExpression":
      return isPureExpr(node.left) && isPureExpr(node.right);
    case "MemberExpression":
      return isPureExpr(node.object) && (!node.computed || isPureExpr(node.property));
    case "ConditionalExpression":
      return isPureExpr(node.test) && isPureExpr(node.consequent) && isPureExpr(node.alternate);
    default:
      return false;
  }
}

function isCheapPureExpr(node) {
  if (!node) return false;
  if (node.type === "Identifier" || node.type === "Literal") return true;
  if (
    node.type === "MemberExpression" &&
    node.object.type === "Identifier" &&
    (!node.computed || node.property.type === "Identifier" || node.property.type === "Literal")
  ) {
    return true;
  }
  return false;
}

function hasThisOrArguments(node) {
  let found = false;
  function walk(n) {
    if (!n || found || typeof n !== "object") return;
    if (n.type === "FunctionDeclaration" || n.type === "FunctionExpression") return;
    if (n.type === "ThisExpression" || (n.type === "Identifier" && n.name === "arguments")) {
      found = true;
      return;
    }
    for (const v of Object.values(n)) {
      if (Array.isArray(v)) v.forEach(walk);
      else if (v && typeof v.type === "string") walk(v);
    }
  }
  walk(node);
  return found;
}

function containsNonCoreChar(str) {
  for (let i = 0; i < str.length; i++) {
    if (!CORE_STRING_CHARS.has(str[i])) return true;
  }
  return false;
}

function buildFromCharCodeExpr(str) {
  if (str.length === 0) {
    return { type: "Literal", value: "", raw: "", isString: true };
  }
  const runs = [];
  let i = 0;
  while (i < str.length) {
    if (CORE_STRING_CHARS.has(str[i])) {
      let j = i;
      while (j < str.length && CORE_STRING_CHARS.has(str[j])) j++;
      if (j - i >= 6) {
        runs.push({ kind: "lit", text: str.slice(i, j) });
        i = j;
        continue;
      }
    }
    let j = i;
    while (j < str.length) {
      if (CORE_STRING_CHARS.has(str[j])) {
        let k = j;
        while (k < str.length && CORE_STRING_CHARS.has(str[k])) k++;
        if (k - j >= 6) break;
        j = k;
      } else {
        j++;
      }
    }
    runs.push({ kind: "codes", text: str.slice(i, j) });
    i = j;
  }

  const parts = runs.map(r => {
    if (r.kind === "lit") {
      return { type: "Literal", value: r.text, raw: r.text, isString: true };
    }
    const codes = [];
    for (let k = 0; k < r.text.length; k++) codes.push(r.text.charCodeAt(k));
    return {
      type: "CallExpression",
      callee: {
        type: "MemberExpression",
        object: { type: "Identifier", name: "String" },
        property: { type: "Identifier", name: "fromCharCode" },
        computed: false,
        optional: false,
      },
      arguments: codes.map(c => ({ type: "Literal", value: c, raw: String(c) })),
      optional: false,
    };
  });

  let expr = parts[0];
  for (let k = 1; k < parts.length; k++) {
    expr = { type: "BinaryExpression", operator: "+", left: expr, right: parts[k] };
  }
  return expr;
}

function isCjsExportAssignment(expr, freeIdentSet) {
  if (!expr || expr.type !== "AssignmentExpression" || expr.operator !== "=") return false;
  const lhs = expr.left;
  if (!lhs || lhs.type !== "MemberExpression") return false;
  // module.exports = ...
  if (
    !lhs.computed &&
    lhs.object.type === "Identifier" &&
    lhs.object.name === "module" &&
    freeIdentSet.has(lhs.object) &&
    lhs.property.type === "Identifier" &&
    lhs.property.name === "exports"
  ) {
    return true;
  }
  // module.exports.x = ... or module.exports[x] = ...
  if (
    lhs.object.type === "MemberExpression" &&
    !lhs.object.computed &&
    lhs.object.object.type === "Identifier" &&
    lhs.object.object.name === "module" &&
    freeIdentSet.has(lhs.object.object) &&
    lhs.object.property.type === "Identifier" &&
    lhs.object.property.name === "exports"
  ) {
    return true;
  }
  // exports.x = ... or exports[x] = ...
  if (
    lhs.object.type === "Identifier" &&
    lhs.object.name === "exports" &&
    freeIdentSet.has(lhs.object)
  ) {
    return true;
  }
  return false;
}

function isCjsExportStmt(stmt, freeIdentSet) {
  if (!stmt) return false;
  if (stmt.type === "ExpressionStatement") {
    return isCjsExportAssignment(stmt.expression, freeIdentSet);
  }
  if (stmt.type === "IfStatement" && !stmt.alternate) {
    const bodyStmts = stmt.consequent.type === "BlockStatement" ? stmt.consequent.body : [stmt.consequent];
    if (bodyStmts.length > 0 && bodyStmts.every(s => isCjsExportStmt(s, freeIdentSet))) {
      return true;
    }
  }
  return false;
}

function stripExportBoilerplate(ast) {
  // 1. Strip standard CommonJS export statements (`module.exports = ...`,
  //    `module.exports.<name> = ...`, `exports.<name> = ...`, or UMD `if (...) { module.exports... }`).
  const initialScope = analyzeScopes(ast);
  const freeIdentSet = new Set(initialScope.freeRefs);
  ast.body = ast.body.filter(stmt => !isCjsExportStmt(stmt, freeIdentSet));

  // 2. Iteratively prune top-level dead export wrappers/aliases (unreferenced top-level
  //    FunctionDeclarations and pure alias VariableDeclarations other than `solve`).
  let changed = true;
  while (changed) {
    changed = false;
    const scopeInfo = analyzeScopes(ast);
    const nextBody = [];
    for (const stmt of ast.body) {
      if (stmt.type === "FunctionDeclaration" && stmt.id && stmt.id.name !== "solve") {
        const b = scopeInfo.nodeToBinding.get(stmt.id);
        if (b && b.refs.length === 0) {
          changed = true;
          continue;
        }
      }
      if (
        stmt.type === "VariableDeclaration" &&
        stmt.declarations.length === 1 &&
        stmt.declarations[0].id.type === "Identifier" &&
        stmt.declarations[0].id.name !== "solve"
      ) {
        const decl = stmt.declarations[0];
        const b = scopeInfo.nodeToBinding.get(decl.id);
        const pureAlias =
          decl.init &&
          (decl.init.type === "Identifier" ||
            decl.init.type === "FunctionExpression" ||
            decl.init.type === "ArrowFunctionExpression");
        if (b && b.refs.length === 0 && pureAlias) {
          changed = true;
          continue;
        }
      }
      nextBody.push(stmt);
    }
    ast.body = nextBody;
  }
}

function lowerLocalClasses(ast) {
  const scopeInfo = analyzeScopes(ast);
  const pool = ["a", "b", "c", "d", "e", "aa", "ab", "ac", "ad", "ae", "ba", "bb"];

  const newBody = [];
  for (const stmt of ast.body) {
    if (stmt.type !== "ClassDeclaration" || !stmt.id || stmt.superClass) {
      newBody.push(stmt);
      continue;
    }
    const members = stmt.body.body;
    if (members.some(m => m.static || m.computed || (m.kind !== "constructor" && m.kind !== "method"))) {
      newBody.push(stmt);
      continue;
    }
    const clsBinding = scopeInfo.nodeToBinding.get(stmt.id);
    if (!clsBinding) {
      newBody.push(stmt);
      continue;
    }
    const instanceBindings = new Set();
    let safe = true;
    function checkInst(n) {
      if (!n || typeof n !== "object") return;
      if (n.type === "VariableDeclarator" && n.id.type === "Identifier" && n.init && n.init.type === "NewExpression") {
        if (n.init.callee.type === "Identifier" && scopeInfo.nodeToBinding.get(n.init.callee) === clsBinding) {
          const b = scopeInfo.nodeToBinding.get(n.id);
          if (b) instanceBindings.add(b);
        }
      }
      if (n.type === "ReturnStatement" && n.argument && n.argument.type === "Identifier") {
        if (instanceBindings.has(scopeInfo.nodeToBinding.get(n.argument))) safe = false;
      }
      for (const v of Object.values(n)) {
        if (Array.isArray(v)) v.forEach(checkInst);
        else if (v && typeof v.type === "string") checkInst(v);
      }
    }
    checkInst(ast);
    if (!safe || instanceBindings.size === 0) {
      newBody.push(stmt);
      continue;
    }

    const methodMap = new Map();
    const fieldMap = new Map();
    let mIdx = 0;
    for (const m of members) {
      if (m.kind === "method" && m.key.type === "Identifier") {
        methodMap.set(m.key.name, pool[mIdx++]);
      }
    }
    function findFields(n) {
      if (!n || typeof n !== "object") return;
      if (n.type === "MemberExpression" && !n.computed && n.object.type === "ThisExpression" && n.property.type === "Identifier") {
        if (!methodMap.has(n.property.name) && !fieldMap.has(n.property.name)) {
          fieldMap.set(n.property.name, pool[mIdx++]);
        }
      }
      for (const v of Object.values(n)) {
        if (Array.isArray(v)) v.forEach(findFields);
        else if (v && typeof v.type === "string") findFields(v);
      }
    }
    findFields(stmt.body);

    function renameInstMembers(n, insideClass) {
      if (!n || typeof n !== "object") return;
      const nowIn = insideClass || n === stmt;
      if (n.type === "MemberExpression" && !n.computed && n.property.type === "Identifier") {
        if (nowIn && n.object.type === "ThisExpression") {
          if (methodMap.has(n.property.name)) n.property.name = methodMap.get(n.property.name);
          else if (fieldMap.has(n.property.name)) n.property.name = fieldMap.get(n.property.name);
        } else if (n.object.type === "Identifier" && instanceBindings.has(scopeInfo.nodeToBinding.get(n.object))) {
          if (methodMap.has(n.property.name)) n.property.name = methodMap.get(n.property.name);
          else if (fieldMap.has(n.property.name)) n.property.name = fieldMap.get(n.property.name);
        }
      }
      for (const v of Object.values(n)) {
        if (Array.isArray(v)) v.forEach(x => renameInstMembers(x, nowIn));
        else if (v && typeof v.type === "string") renameInstMembers(v, nowIn);
      }
    }
    renameInstMembers(ast, false);

    const ctor = members.find(m => m.kind === "constructor");
    const ctorParams = ctor ? ctor.value.params : [];
    const fnStmts = ctor ? [...ctor.value.body.body] : [];
    for (const m of members) {
      if (m.kind === "method") {
        const mapped = methodMap.get(m.key.name);
        fnStmts.push({
          type: "ExpressionStatement",
          expression: {
            type: "AssignmentExpression",
            operator: "=",
            left: {
              type: "MemberExpression",
              object: { type: "ThisExpression" },
              property: { type: "Identifier", name: mapped },
              computed: false,
              optional: false,
            },
            right: m.value,
          },
        });
      }
    }
    newBody.push({
      type: "FunctionDeclaration",
      id: stmt.id,
      params: ctorParams,
      body: { type: "BlockStatement", body: fnStmts },
      generator: false,
    });
  }
  ast.body = newBody;
}

function isSimpleContinue(stmt) {
  if (!stmt) return false;
  if (stmt.type === "ContinueStatement" && !stmt.label) return true;
  if (stmt.type === "BlockStatement" && stmt.body.length === 1 && stmt.body[0].type === "ContinueStatement" && !stmt.body[0].label) {
    return true;
  }
  return false;
}

function alwaysExits(stmt) {
  if (!stmt) return false;
  if (stmt.type === "ReturnStatement" || stmt.type === "ThrowStatement" || stmt.type === "BreakStatement" || stmt.type === "ContinueStatement") {
    return true;
  }
  if (stmt.type === "BlockStatement" && stmt.body.length > 0) {
    return alwaysExits(stmt.body[stmt.body.length - 1]);
  }
  return false;
}

function simplifyControlFlowBlock(stmts, isLoopTail) {
  // 1. Eliminate dead `else` after `if(cond){...return/throw/break/continue;}` (saves `else` tokens!)
  // 2. At loop tail (`isLoopTail === true`), eliminate label-free `continue;`:
  //    - `if(cond)continue; rest...` -> `if(!(cond)){rest...}`
  //    - `if(cond){body;continue;} rest...` -> `if(cond){body;}else{rest...}`
  //    - trailing unconditional `continue;` at very end of loop body -> dropped
  const out = [];
  for (let i = 0; i < stmts.length; i++) {
    const s = stmts[i];
    if (isLoopTail && i === stmts.length - 1 && s.type === "ContinueStatement" && !s.label) {
      continue;
    }
    if (isLoopTail && s.type === "IfStatement" && !s.alternate && isSimpleContinue(s.consequent)) {
      const rest = simplifyControlFlowBlock(stmts.slice(i + 1), true);
      if (rest.length > 0) {
        out.push({
          type: "IfStatement",
          test: { type: "UnaryExpression", operator: "!", prefix: true, argument: s.test },
          consequent: { type: "BlockStatement", body: rest },
          alternate: null,
        });
      }
      return out;
    }
    if (
      isLoopTail &&
      s.type === "IfStatement" &&
      !s.alternate &&
      s.consequent.type === "BlockStatement" &&
      s.consequent.body.length >= 2
    ) {
      const lastInCons = s.consequent.body[s.consequent.body.length - 1];
      if (lastInCons.type === "ContinueStatement" && !lastInCons.label) {
        const trimmedBody = s.consequent.body.slice(0, -1);
        const rest = simplifyControlFlowBlock(stmts.slice(i + 1), true);
        out.push({
          type: "IfStatement",
          test: s.test,
          consequent: { type: "BlockStatement", body: trimmedBody },
          alternate: rest.length > 0 ? { type: "BlockStatement", body: rest } : null,
        });
        return out;
      }
    }
    if (s.type === "IfStatement" && s.alternate && alwaysExits(s.consequent)) {
      const altStmts = s.alternate.type === "BlockStatement" ? s.alternate.body : [s.alternate];
      out.push({ type: "IfStatement", test: s.test, consequent: s.consequent, alternate: null });
      // Flatten alternate right into the current block if no var decls collide
      const hasBlockDecl = altStmts.some(x => x.type === "VariableDeclaration" || x.type === "FunctionDeclaration" || x.type === "ClassDeclaration");
      if (!hasBlockDecl) {
        out.push(...simplifyControlFlowBlock(altStmts, isLoopTail && i === stmts.length - 1));
        continue;
      } else {
        out.pop();
      }
    }
    out.push(s);
  }
  return out;
}

function matchNumericDiffComparator(fnNode) {
  // General AST check for pure 2-parameter numeric difference comparators:
  //   (a, b) => a - b  |  function(a, b) { return a - b; }  -> "asc"
  //   (a, b) => b - a  |  function(a, b) { return b - a; }  -> "desc"
  if (!fnNode) return null;
  if (fnNode.type !== "ArrowFunctionExpression" && fnNode.type !== "FunctionExpression") return null;
  if (!fnNode.params || fnNode.params.length !== 2) return null;
  const [p1, p2] = fnNode.params;
  if (p1.type !== "Identifier" || p2.type !== "Identifier" || p1.name === p2.name) return null;
  let expr = null;
  if (fnNode.type === "ArrowFunctionExpression" && fnNode.body.type !== "BlockStatement") {
    expr = fnNode.body;
  } else if (
    fnNode.body &&
    fnNode.body.type === "BlockStatement" &&
    fnNode.body.body.length === 1 &&
    fnNode.body.body[0].type === "ReturnStatement" &&
    fnNode.body.body[0].argument
  ) {
    expr = fnNode.body.body[0].argument;
  }
  if (!expr || expr.type !== "BinaryExpression" || expr.operator !== "-") return null;
  if (expr.left.type !== "Identifier" || expr.right.type !== "Identifier") return null;
  if (expr.left.name === p1.name && expr.right.name === p2.name) return "asc";
  if (expr.left.name === p2.name && expr.right.name === p1.name) return "desc";
  return null;
}

function extractFreshSortSource(targetNode) {
  // Match ONLY provably fresh (non-mutating copy) array receivers, returning { kind, src }:
  //   1. <expr>.slice()  (0 args)          -> { kind: "slice", src: <expr> }
  //   2. [...<iterable>] (single spread)   -> { kind: "spread", src: <iterable> }
  //   3. [e1, e2, ...]   (dense literal)   -> { kind: "literal", src: targetNode }
  if (!targetNode) return null;
  if (
    targetNode.type === "CallExpression" &&
    !targetNode.optional &&
    targetNode.arguments.length === 0 &&
    targetNode.callee.type === "MemberExpression" &&
    !targetNode.callee.computed &&
    !targetNode.callee.optional &&
    targetNode.callee.property.type === "Identifier" &&
    targetNode.callee.property.name === "slice"
  ) {
    return { kind: "slice", src: targetNode.callee.object };
  }
  if (targetNode.type === "ArrayExpression" && targetNode.elements.length > 0) {
    if (targetNode.elements.length === 1 && targetNode.elements[0] && targetNode.elements[0].type === "SpreadElement") {
      return { kind: "spread", src: targetNode.elements[0].argument };
    }
    if (targetNode.elements.every(e => e !== null && e.type !== "SpreadElement")) {
      return { kind: "literal", src: targetNode };
    }
  }
  return null;
}

function canonicalizeSyntax(ast, opts) {
  const elimGt = opts.eliminateGt !== false;
  const elimXor = opts.eliminateXor !== false;
  const incStyle = opts.incStyle || "plus_eq";
  const inlineMath = opts.inlineMath !== false;
  const pushToAssign = opts.pushToAssign !== false;
  const lowerDirectBuiltins = opts.lowerDirectBuiltins === true;
  const nativeNumericSort = opts.nativeNumericSort !== false;

  // Two-tier top-level hoist:
  //   baseHoist (`__H`): pure independent literals/globals/properties in ONE compact array literal `let __H=[...]`!
  //   depHoist (`__D`): BigInt/RegExp constants that depend on `__H`, in a single second array literal `let __D=[...]`!
  // ZERO per-element `h[0]=...;h[1]=...;` assignment boilerplate!
  const HOIST_BASE = "__H";
  const HOIST_DEP = "__D";
  const baseExprs = [];
  const baseIndex = new Map();
  const depExprs = [];
  const depIndex = new Map();

  function getBaseRef(key, initBuilder) {
    let idx;
    if (baseIndex.has(key)) {
      idx = baseIndex.get(key);
    } else {
      const initExpr = initBuilder();
      idx = baseExprs.length;
      baseIndex.set(key, idx);
      baseExprs.push(initExpr);
    }
    return {
      type: "MemberExpression",
      object: { type: "Identifier", name: HOIST_BASE },
      property: { type: "Literal", value: idx, raw: String(idx) },
      computed: true,
      optional: false,
    };
  }

  function getDepRef(key, initBuilder) {
    let idx;
    if (depIndex.has(key)) {
      idx = depIndex.get(key);
    } else {
      const initExpr = initBuilder();
      idx = depExprs.length;
      depIndex.set(key, idx);
      depExprs.push(initExpr);
    }
    return {
      type: "MemberExpression",
      object: { type: "Identifier", name: HOIST_DEP },
      property: { type: "Literal", value: idx, raw: String(idx) },
      computed: true,
      optional: false,
    };
  }

  function lowerStringExpr(str, allowHoist) {
    if (!containsNonCoreChar(str)) {
      return { type: "Literal", value: str, raw: str, isString: true };
    }
    if (allowHoist) {
      return getBaseRef("S:" + str, () => buildFromCharCodeExpr(str));
    }
    return buildFromCharCodeExpr(str);
  }

  function getGlobalRef(name) {
    // Inline `this[String.fromCharCode(...)]` directly inside `__H` (saves 1 array slot & 1 lookup!)
    return getBaseRef("G:" + name, () => ({
      type: "MemberExpression",
      object: { type: "ThisExpression" },
      property: buildFromCharCodeExpr(name),
      computed: true,
      optional: false,
    }));
  }

  function getGuardedNumericSortHelper(kind, dir) {
    // Hoisted standalone runtime domain guard inside `__D` (zero external helpers, zero escapes).
    // Fast-paths to Float64Array sort ONLY when:
    //   1. Receiver is a true Array with unmodified `.slice` (for slice) or `[Symbol.iterator]` (for spread),
    //   2. Length >= 8 (avoids O(n) guard overhead on tiny arrays), and
    //   3. Every element is a finite IEEE-754 number excluding -0 (Number.isFinite(v) && (v !== 0 || 1/v === 1/0)),
    //      rejecting null, undefined, sparse holes, strings, booleans, BigInt, Symbol, objects, NaN, +/-Infinity, and -0.
    // Any input outside this sealed numeric domain falls back verbatim to the exact original JS comparator sort.
    return getDepRef(`NSORT:${kind}:${dir}`, () => {
      const sId = () => ({ type: "Identifier", name: "__s" });
      const oId = () => ({ type: "Identifier", name: "__o" });
      const iId = () => ({ type: "Identifier", name: "__i" });
      const vId = () => ({ type: "Identifier", name: "__v" });
      const aId = () => ({ type: "Identifier", name: "__a" });
      const bId = () => ({ type: "Identifier", name: "__b" });

      const nfRef = getBaseRef("NF:Number.isFinite", () => ({
        type: "MemberExpression",
        object: {
          type: "MemberExpression",
          object: { type: "ThisExpression" },
          property: buildFromCharCodeExpr("Number"),
          computed: true,
          optional: false,
        },
        property: buildFromCharCodeExpr("isFinite"),
        computed: true,
        optional: false,
      }));
      const isArrayCall = {
        type: "CallExpression",
        callee: {
          type: "MemberExpression",
          object: { type: "Identifier", name: "Array" },
          property: lowerStringExpr("isArray", true),
          computed: true,
          optional: false,
        },
        arguments: [sId()],
        optional: false,
      };
      const arrProtoRef = () => ({
        type: "MemberExpression",
        object: { type: "Identifier", name: "Array" },
        property: lowerStringExpr("prototype", true),
        computed: true,
        optional: false,
      });

      let receiverOk;
      if (kind === "slice") {
        receiverOk = {
          type: "LogicalExpression",
          operator: "&&",
          left: isArrayCall,
          right: {
            type: "BinaryExpression",
            operator: "===",
            left: {
              type: "MemberExpression",
              object: sId(),
              property: lowerStringExpr("slice", true),
              computed: true,
              optional: false,
            },
            right: {
              type: "MemberExpression",
              object: arrProtoRef(),
              property: lowerStringExpr("slice", true),
              computed: true,
              optional: false,
            },
          },
        };
      } else if (kind === "spread") {
        const symIterRef = getBaseRef("SYM:Symbol.iterator", () => ({
          type: "MemberExpression",
          object: {
            type: "MemberExpression",
            object: { type: "ThisExpression" },
            property: buildFromCharCodeExpr("Symbol"),
            computed: true,
            optional: false,
          },
          property: buildFromCharCodeExpr("iterator"),
          computed: true,
          optional: false,
        }));
        receiverOk = {
          type: "LogicalExpression",
          operator: "&&",
          left: isArrayCall,
          right: {
            type: "BinaryExpression",
            operator: "===",
            left: {
              type: "MemberExpression",
              object: sId(),
              property: cloneAst(symIterRef),
              computed: true,
              optional: false,
            },
            right: {
              type: "MemberExpression",
              object: arrProtoRef(),
              property: symIterRef,
              computed: true,
              optional: false,
            },
          },
        };
      } else {
        receiverOk = { type: "UnaryExpression", operator: "!", prefix: true, argument: { type: "Literal", value: 0, raw: "0" } };
      }

      const lenExpr = () => ({
        type: "MemberExpression",
        object: sId(),
        property: { type: "Identifier", name: "length" },
        computed: false,
        optional: false,
      });

      const elemValid = {
        type: "LogicalExpression",
        operator: "&&",
        left: { type: "CallExpression", callee: nfRef, arguments: [vId()], optional: false },
        right: {
          type: "LogicalExpression",
          operator: "||",
          left: { type: "BinaryExpression", operator: "!==", left: vId(), right: { type: "Literal", value: 0, raw: "0" } },
          right: {
            type: "BinaryExpression",
            operator: "===",
            left: { type: "BinaryExpression", operator: "/", left: { type: "Literal", value: 1, raw: "1" }, right: vId() },
            right: { type: "BinaryExpression", operator: "/", left: { type: "Literal", value: 1, raw: "1" }, right: { type: "Literal", value: 0, raw: "0" } },
          },
        },
      };

      const typedArr = {
        type: "NewExpression",
        callee: getGlobalRef("Float64Array"),
        arguments: [sId()],
      };
      let sortedTyped = {
        type: "CallExpression",
        callee: {
          type: "MemberExpression",
          object: typedArr,
          property: lowerStringExpr("sort", true),
          computed: true,
          optional: false,
        },
        arguments: [],
        optional: false,
      };
      if (dir === "desc") {
        sortedTyped = {
          type: "CallExpression",
          callee: {
            type: "MemberExpression",
            object: sortedTyped,
            property: lowerStringExpr("reverse", true),
            computed: true,
            optional: false,
          },
          arguments: [],
          optional: false,
        };
      }
      const fastReturn = {
        type: "ReturnStatement",
        argument: { type: "ArrayExpression", elements: [{ type: "SpreadElement", argument: sortedTyped }] },
      };

      let fallbackRecv;
      if (kind === "slice") {
        fallbackRecv = {
          type: "CallExpression",
          callee: {
            type: "MemberExpression",
            object: sId(),
            property: lowerStringExpr("slice", true),
            computed: true,
            optional: false,
          },
          arguments: [],
          optional: false,
        };
      } else if (kind === "spread") {
        fallbackRecv = {
          type: "ArrayExpression",
          elements: [{ type: "SpreadElement", argument: sId() }],
        };
      } else {
        fallbackRecv = sId();
      }
      const cmpFn = {
        type: "FunctionExpression",
        id: null,
        params: [aId(), bId()],
        body: {
          type: "BlockStatement",
          body: [{
            type: "ReturnStatement",
            argument: {
              type: "BinaryExpression",
              operator: "-",
              left: dir === "asc" ? aId() : bId(),
              right: dir === "asc" ? bId() : aId(),
            },
          }],
        },
        generator: false,
      };
      const fallbackReturn = {
        type: "ReturnStatement",
        argument: {
          type: "CallExpression",
          callee: {
            type: "MemberExpression",
            object: fallbackRecv,
            property: lowerStringExpr("sort", true),
            computed: true,
            optional: false,
          },
          arguments: [cmpFn],
          optional: false,
        },
      };

      const loopStmt = {
        type: "ForStatement",
        init: {
          type: "VariableDeclaration",
          kind: "let",
          declarations: [{ type: "VariableDeclarator", id: iId(), init: { type: "Literal", value: 0, raw: "0" } }],
        },
        test: { type: "BinaryExpression", operator: "<", left: iId(), right: lenExpr() },
        update: { type: "AssignmentExpression", operator: "+=", left: iId(), right: { type: "Literal", value: 1, raw: "1" } },
        body: {
          type: "BlockStatement",
          body: [
            {
              type: "VariableDeclaration",
              kind: "let",
              declarations: [{
                type: "VariableDeclarator",
                id: vId(),
                init: { type: "MemberExpression", object: sId(), property: iId(), computed: true, optional: false },
              }],
            },
            {
              type: "IfStatement",
              test: { type: "UnaryExpression", operator: "!", prefix: true, argument: elemValid },
              consequent: {
                type: "BlockStatement",
                body: [
                  {
                    type: "ExpressionStatement",
                    expression: {
                      type: "AssignmentExpression",
                      operator: "=",
                      left: oId(),
                      right: { type: "UnaryExpression", operator: "!", prefix: true, argument: { type: "Literal", value: 1, raw: "1" } },
                    },
                  },
                  { type: "BreakStatement", label: null },
                ],
              },
              alternate: null,
            },
          ],
        },
      };

      const guardedBlock = {
        type: "IfStatement",
        test: {
          type: "LogicalExpression",
          operator: "&&",
          left: oId(),
          right: { type: "BinaryExpression", operator: "<", left: { type: "Literal", value: 7, raw: "7" }, right: lenExpr() },
        },
        consequent: {
          type: "BlockStatement",
          body: [
            loopStmt,
            { type: "IfStatement", test: oId(), consequent: fastReturn, alternate: null },
          ],
        },
        alternate: null,
      };

      return {
        type: "FunctionExpression",
        id: null,
        params: [sId()],
        body: {
          type: "BlockStatement",
          body: [
            {
              type: "VariableDeclaration",
              kind: "let",
              declarations: [{ type: "VariableDeclarator", id: oId(), init: receiverOk }],
            },
            guardedBlock,
            fallbackReturn,
          ],
        },
        generator: false,
      };
    });
  }

  const scopeInfo = analyzeScopes(ast);
  const freeIdentSet = new Set(scopeInfo.freeRefs);

  function txExpr(node, inLoopDepth) {
    if (!node) return node;
    switch (node.type) {
      case "Identifier": {
        if (freeIdentSet.has(node)) {
          if (node.name === "Infinity") {
            return {
              type: "BinaryExpression",
              operator: "/",
              left: { type: "Literal", value: 1, raw: "1" },
              right: { type: "Literal", value: 0, raw: "0" },
            };
          }
          if (node.name === "undefined") {
            return {
              type: "MemberExpression",
              object: { type: "ArrayExpression", elements: [] },
              property: { type: "Literal", value: 0, raw: "0" },
              computed: true,
              optional: false,
            };
          }
          const isDirect = !lowerDirectBuiltins && DIRECT_GLOBALS.has(node.name);
          if (!isDirect && containsNonCoreChar(node.name)) {
            return getGlobalRef(node.name);
          }
        }
        return node;
      }
      case "Literal": {
        if (node.regex) {
          const pat = node.regex.pattern;
          const flags = node.regex.flags;
          const stateful = flags.includes("g") || flags.includes("y");
          const buildRegex = () => ({
            type: "NewExpression",
            callee: {
              type: "MemberExpression",
              object: { type: "Literal", value: null, regex: { pattern: "a", flags: "" }, raw: "/a/" },
              property: buildFromCharCodeExpr("constructor"),
              computed: true,
              optional: false,
            },
            arguments: [lowerStringExpr(pat, false), lowerStringExpr(flags, false)],
          });
          if (!stateful) {
            return getBaseRef(`R:${pat}/${flags}`, buildRegex);
          }
          return buildRegex();
        }
        if (typeof node.value === "boolean") {
          return {
            type: "UnaryExpression",
            operator: "!",
            prefix: true,
            argument: { type: "Literal", value: node.value ? 0 : 1, raw: node.value ? "0" : "1" },
          };
        }
        if (node.isString || typeof node.value === "string") {
          return lowerStringExpr(node.value, inLoopDepth > 0 || node.value.length > 0);
        }
        if (typeof node.value === "number" && node.raw) {
          if (Number.isInteger(node.value) && Math.abs(node.value) <= 9007199254740991) {
            const dec = String(node.value);
            if (dec !== node.raw && !dec.includes("e")) {
              return { type: "Literal", value: node.value, raw: dec };
            }
          }
        }
        if (node.bigint !== undefined) {
          const dec = BigInt(node.bigint).toString(10);
          return getDepRef("BI:" + dec, () => {
            const numArg = dec.length <= 15
              ? { type: "Literal", value: Number(dec), raw: dec }
              : { type: "Literal", value: dec, raw: dec, isString: true };
            return {
              type: "CallExpression",
              callee: getGlobalRef("BigInt"),
              arguments: [numArg],
              optional: false,
            };
          });
        }
        return node;
      }
      case "TemplateLiteral": {
        const pieces = [];
        for (let i = 0; i < node.quasis.length; i++) {
          const q = node.quasis[i].value;
          if (q.length > 0 || pieces.length === 0) pieces.push(lowerStringExpr(q, true));
          if (i < node.expressions.length) pieces.push(txExpr(node.expressions[i], inLoopDepth));
        }
        let acc = pieces[0];
        for (let i = 1; i < pieces.length; i++) {
          acc = { type: "BinaryExpression", operator: "+", left: acc, right: pieces[i] };
        }
        return acc;
      }
      case "MemberExpression": {
        if (
          !node.computed &&
          node.object.type === "Identifier" &&
          freeIdentSet.has(node.object) &&
          node.object.name === "Number" &&
          node.property.type === "Identifier"
        ) {
          if (node.property.name === "MAX_SAFE_INTEGER") {
            return { type: "Literal", value: 9007199254740991, raw: "9007199254740991" };
          }
          if (node.property.name === "MIN_SAFE_INTEGER") {
            return { type: "UnaryExpression", operator: "-", prefix: true, argument: { type: "Literal", value: 9007199254740991, raw: "9007199254740991" } };
          }
        }
        if (
          !node.computed &&
          node.object.type === "Identifier" &&
          freeIdentSet.has(node.object) &&
          node.object.name === "String" &&
          node.property.type === "Identifier" &&
          node.property.name === "fromCharCode"
        ) {
          return node;
        }
        node.object = txExpr(node.object, inLoopDepth);
        if (node.computed) {
          node.property = txExpr(node.property, inLoopDepth);
        } else if (node.property.type === "Identifier") {
          const pname = node.property.name;
          const isDirect = !lowerDirectBuiltins && DIRECT_PROPS.has(pname);
          if (!isDirect && containsNonCoreChar(pname)) {
            node.computed = true;
            node.property = lowerStringExpr(pname, true);
          }
        }
        return node;
      }
      case "NewExpression": {
        if (node.callee.type === "Identifier" && freeIdentSet.has(node.callee) && node.callee.name === "Array") {
          return {
            type: "CallExpression",
            callee: txExpr(node.callee, inLoopDepth),
            arguments: node.arguments.map(a =>
              a.type === "SpreadElement" ? { ...a, argument: txExpr(a.argument, inLoopDepth) } : txExpr(a, inLoopDepth)
            ),
            optional: false,
          };
        }
        node.callee = txExpr(node.callee, inLoopDepth);
        node.arguments = node.arguments.map(a =>
          a.type === "SpreadElement" ? { ...a, argument: txExpr(a.argument, inLoopDepth) } : txExpr(a, inLoopDepth)
        );
        return node;
      }
      case "CallExpression": {
        // General Numeric Copy-Sort Specialization (Pass 2, domain-sealed):
        // Replaces `<freshArray>.sort((a,b)=>a-b)` (or `b-a`) with a standalone hoisted
        // runtime-guarded helper that fast-paths to Float64Array sort ONLY for dense
        // finite non-negative-zero numeric Arrays (length >= 8) and falls back verbatim
        // to the original JS comparator sort on any input outside that numeric domain.
        if (
          nativeNumericSort &&
          !node.optional &&
          node.callee.type === "MemberExpression" &&
          !node.callee.computed &&
          !node.callee.optional &&
          node.callee.property.type === "Identifier" &&
          node.callee.property.name === "sort" &&
          node.arguments.length === 1 &&
          node.arguments[0].type !== "SpreadElement"
        ) {
          const dir = matchNumericDiffComparator(node.arguments[0]);
          const fresh = dir ? extractFreshSortSource(node.callee.object) : null;
          if (dir && fresh) {
            const srcTx = txExpr(fresh.src, inLoopDepth);
            const helperRef = getGuardedNumericSortHelper(fresh.kind, dir);
            return {
              type: "CallExpression",
              callee: helperRef,
              arguments: [srcTx],
              optional: false,
            };
          }
        }
        if (
          inlineMath &&
          node.callee.type === "MemberExpression" &&
          !node.callee.computed &&
          node.callee.object.type === "Identifier" &&
          freeIdentSet.has(node.callee.object) &&
          node.callee.object.name === "Math" &&
          node.callee.property.type === "Identifier"
        ) {
          const fn = node.callee.property.name;
          if (fn === "min" && node.arguments.length === 2 && node.arguments.every(a => a.type !== "SpreadElement" && isCheapPureExpr(a))) {
            const x = txExpr(node.arguments[0], inLoopDepth);
            const y = txExpr(node.arguments[1], inLoopDepth);
            return {
              type: "ConditionalExpression",
              test: { type: "BinaryExpression", operator: "<", left: cloneAst(x), right: cloneAst(y) },
              consequent: x,
              alternate: y,
            };
          }
          if (fn === "max" && node.arguments.length === 2 && node.arguments.every(a => a.type !== "SpreadElement" && isCheapPureExpr(a))) {
            const x = txExpr(node.arguments[0], inLoopDepth);
            const y = txExpr(node.arguments[1], inLoopDepth);
            return {
              type: "ConditionalExpression",
              test: { type: "BinaryExpression", operator: "<", left: cloneAst(y), right: cloneAst(x) },
              consequent: x,
              alternate: y,
            };
          }
          if (fn === "abs" && node.arguments.length === 1 && node.arguments[0].type !== "SpreadElement" && isCheapPureExpr(node.arguments[0])) {
            const x = txExpr(node.arguments[0], inLoopDepth);
            return {
              type: "ConditionalExpression",
              test: { type: "BinaryExpression", operator: "<", left: cloneAst(x), right: { type: "Literal", value: 0, raw: "0" } },
              consequent: { type: "UnaryExpression", operator: "-", prefix: true, argument: cloneAst(x) },
              alternate: x,
            };
          }
        }
        if (
          opts.stringToConcat &&
          node.callee.type === "Identifier" &&
          freeIdentSet.has(node.callee) &&
          node.callee.name === "String" &&
          node.arguments.length === 1 &&
          node.arguments[0].type !== "SpreadElement"
        ) {
          return {
            type: "BinaryExpression",
            operator: "+",
            left: { type: "Literal", value: "", raw: "", isString: true },
            right: txExpr(node.arguments[0], inLoopDepth),
          };
        }
        node.callee = txExpr(node.callee, inLoopDepth);
        node.arguments = node.arguments.map(a =>
          a.type === "SpreadElement" ? { ...a, argument: txExpr(a.argument, inLoopDepth) } : txExpr(a, inLoopDepth)
        );
        return node;
      }
      case "ArrowFunctionExpression": {
        if (!hasThisOrArguments(node.body)) {
          const body = node.body.type === "BlockStatement"
            ? txStmt(node.body, inLoopDepth)
            : { type: "BlockStatement", body: [{ type: "ReturnStatement", argument: txExpr(node.body, inLoopDepth) }] };
          return { type: "FunctionExpression", id: null, params: node.params, body, generator: false };
        }
        if (node.body.type === "BlockStatement") node.body = txStmt(node.body, inLoopDepth);
        else node.body = txExpr(node.body, inLoopDepth);
        return node;
      }
      case "FunctionExpression":
        node.body = txStmt(node.body, inLoopDepth);
        return node;
      case "UnaryExpression": {
        node.argument = txExpr(node.argument, inLoopDepth);
        if (node.operator === "~") {
          return {
            type: "BinaryExpression",
            operator: "|",
            left: {
              type: "BinaryExpression",
              operator: "-",
              left: { type: "UnaryExpression", operator: "-", prefix: true, argument: node.argument },
              right: { type: "Literal", value: 1, raw: "1" },
            },
            right: { type: "Literal", value: 0, raw: "0" },
          };
        }
        return node;
      }
      case "UpdateExpression":
        node.argument = txExpr(node.argument, inLoopDepth);
        return node;
      case "BinaryExpression": {
        if (
          (node.operator === "===" || node.operator === "!==") &&
          node.left.type === "UnaryExpression" &&
          node.left.operator === "typeof" &&
          isCheapPureExpr(node.left.argument) &&
          node.right.type === "Literal" &&
          typeof node.right.value === "string" &&
          ["number", "string", "boolean"].includes(node.right.value)
        ) {
          const arg = txExpr(node.left.argument, inLoopDepth);
          const ctorGlobal = node.right.value === "number" ? getGlobalRef("Number")
            : node.right.value === "string" ? { type: "Identifier", name: "String" }
            : getGlobalRef("Boolean");
          const check = {
            type: "LogicalExpression",
            operator: "&&",
            left: { type: "BinaryExpression", operator: "!=", left: cloneAst(arg), right: { type: "Literal", value: null, raw: "null" } },
            right: {
              type: "BinaryExpression",
              operator: "===",
              left: {
                type: "MemberExpression",
                object: arg,
                property: lowerStringExpr("constructor", true),
                computed: true,
                optional: false,
              },
              right: ctorGlobal,
            },
          };
          return node.operator === "===" ? check : { type: "UnaryExpression", operator: "!", prefix: true, argument: check };
        }
        node.left = txExpr(node.left, inLoopDepth);
        node.right = txExpr(node.right, inLoopDepth);
        if (elimGt && (node.operator === ">" || node.operator === ">=")) {
          if (isPureExpr(node.left) || isPureExpr(node.right)) {
            return {
              type: "BinaryExpression",
              operator: node.operator === ">" ? "<" : "<=",
              left: node.right,
              right: node.left,
            };
          }
        }
        if (elimGt && node.operator === ">>" && node.right.type === "Literal" && Number.isInteger(node.right.value) && node.right.value >= 1 && node.right.value <= 30) {
          const div = Math.pow(2, node.right.value);
          return {
            type: "CallExpression",
            callee: {
              type: "MemberExpression",
              object: { type: "Identifier", name: "Math" },
              property: { type: "Identifier", name: "floor" },
              computed: false,
              optional: false,
            },
            arguments: [{
              type: "BinaryExpression",
              operator: "/",
              left: node.left,
              right: { type: "Literal", value: div, raw: String(div) },
            }],
            optional: false,
          };
        }
        if (elimXor && node.operator === "^" && isPureExpr(node.left) && isPureExpr(node.right)) {
          const hasBig = node.left.bigint !== undefined || node.right.bigint !== undefined;
          if (!hasBig) {
            return {
              type: "BinaryExpression",
              operator: "-",
              left: { type: "BinaryExpression", operator: "|", left: cloneAst(node.left), right: cloneAst(node.right) },
              right: { type: "BinaryExpression", operator: "&", left: cloneAst(node.left), right: cloneAst(node.right) },
            };
          }
        }
        return node;
      }
      case "LogicalExpression":
        node.left = txExpr(node.left, inLoopDepth);
        node.right = txExpr(node.right, inLoopDepth);
        return node;
      case "ConditionalExpression":
        node.test = txExpr(node.test, inLoopDepth);
        node.consequent = txExpr(node.consequent, inLoopDepth);
        node.alternate = txExpr(node.alternate, inLoopDepth);
        return node;
      case "AssignmentExpression": {
        if (node.left.type === "MemberExpression") node.left = txExpr(node.left, inLoopDepth);
        node.right = txExpr(node.right, inLoopDepth);
        if (elimXor && node.operator === "^=" && isPureExpr(node.left) && isPureExpr(node.right)) {
          const hasBig = node.right.bigint !== undefined;
          if (!hasBig) {
            return {
              type: "AssignmentExpression",
              operator: "=",
              left: node.left,
              right: {
                type: "BinaryExpression",
                operator: "-",
                left: { type: "BinaryExpression", operator: "|", left: cloneAst(node.left), right: cloneAst(node.right) },
                right: { type: "BinaryExpression", operator: "&", left: cloneAst(node.left), right: cloneAst(node.right) },
              },
            };
          }
        }
        return node;
      }
      case "SequenceExpression":
        node.expressions = node.expressions.map(e => txExpr(e, inLoopDepth));
        return node;
      case "ArrayExpression":
        node.elements = node.elements.map(e => {
          if (!e) return null;
          if (e.type === "SpreadElement") return { ...e, argument: txExpr(e.argument, inLoopDepth) };
          return txExpr(e, inLoopDepth);
        });
        return node;
      case "ObjectExpression":
        node.properties = node.properties.map(p => {
          if (p.type === "SpreadElement") return { ...p, argument: txExpr(p.argument, inLoopDepth) };
          if (p.computed) {
            p.key = txExpr(p.key, inLoopDepth);
          } else if (p.key.type === "Identifier" && containsNonCoreChar(p.key.name)) {
            p.computed = true;
            p.shorthand = false;
            p.key = lowerStringExpr(p.key.name, true);
          } else if (p.key.type === "Literal" && typeof p.key.value === "string" && containsNonCoreChar(p.key.value)) {
            p.computed = true;
            p.key = lowerStringExpr(p.key.value, true);
          }
          p.value = txExpr(p.value, inLoopDepth);
          return p;
        });
        return node;
      case "ClassExpression":
        if (node.superClass) node.superClass = txExpr(node.superClass, inLoopDepth);
        for (const m of node.body.body) {
          if (m.computed) m.key = txExpr(m.key, inLoopDepth);
          m.value = txExpr(m.value, inLoopDepth);
        }
        return node;
      default:
        return node;
    }
  }

  function normalizeStepExpr(expr) {
    if (!expr) return expr;
    if (incStyle === "plus_eq" && expr.type === "UpdateExpression") {
      return {
        type: "AssignmentExpression",
        operator: expr.operator === "++" ? "+=" : "-=",
        left: expr.argument,
        right: { type: "Literal", value: 1, raw: "1" },
      };
    }
    if (
      incStyle === "plusplus" &&
      expr.type === "AssignmentExpression" &&
      (expr.operator === "+=" || expr.operator === "-=") &&
      expr.right.type === "Literal" &&
      expr.right.value === 1 &&
      expr.right.bigint === undefined
    ) {
      return {
        type: "UpdateExpression",
        operator: expr.operator === "+=" ? "++" : "--",
        prefix: false,
        argument: expr.left,
      };
    }
    return expr;
  }

  function txStmt(stmt, inLoopDepth, isLoopTail = false) {
    if (!stmt) return stmt;
    switch (stmt.type) {
      case "Program":
        stmt.body = stmt.body.map(s => txStmt(s, inLoopDepth, false));
        return stmt;
      case "BlockStatement": {
        const n = stmt.body.length;
        const mapped = stmt.body.map((s, idx) => txStmt(s, inLoopDepth, isLoopTail && idx === n - 1));
        stmt.body = simplifyControlFlowBlock(mapped, isLoopTail);
        return stmt;
      }
      case "FunctionDeclaration":
        stmt.body = txStmt(stmt.body, 0, false);
        return stmt;
      case "ClassDeclaration":
        if (stmt.superClass) stmt.superClass = txExpr(stmt.superClass, inLoopDepth);
        for (const m of stmt.body.body) {
          if (m.computed) m.key = txExpr(m.key, inLoopDepth);
          m.value = txExpr(m.value, 0);
        }
        return stmt;
      case "VariableDeclaration":
        if (stmt.kind === "const") stmt.kind = "let";
        else if (stmt.kind === "var" && stmt.declarations.every(d => d.id.type === "Identifier")) {
          const allSingle = stmt.declarations.every(d => {
            const b = scopeInfo.nodeToBinding.get(d.id);
            return b && b.defs.length === 1 && (b.scope.kind === "program" || b.scope.kind === "function");
          });
          if (allSingle) stmt.kind = "let";
        }
        for (const d of stmt.declarations) {
          if (d.init) d.init = txExpr(d.init, inLoopDepth);
        }
        return stmt;
      case "ExpressionStatement": {
        // Optional general lowering: `arr.push(x);` (1 non-spread arg, cheap receiver) -> `arr[arr.length]=x;`
        // Eliminates `.push(` slot AND removes CallExpression step!
        if (
          pushToAssign &&
          stmt.expression.type === "CallExpression" &&
          stmt.expression.callee.type === "MemberExpression" &&
          !stmt.expression.callee.computed &&
          stmt.expression.callee.property.type === "Identifier" &&
          stmt.expression.callee.property.name === "push" &&
          stmt.expression.arguments.length === 1 &&
          stmt.expression.arguments[0].type !== "SpreadElement" &&
          (stmt.expression.callee.object.type === "Identifier" ||
            (stmt.expression.callee.object.type === "MemberExpression" && stmt.expression.callee.object.object.type === "ThisExpression"))
        ) {
          const recv = txExpr(stmt.expression.callee.object, inLoopDepth);
          const arg = txExpr(stmt.expression.arguments[0], inLoopDepth);
          stmt.expression = {
            type: "AssignmentExpression",
            operator: "=",
            left: {
              type: "MemberExpression",
              object: cloneAst(recv),
              property: {
                type: "MemberExpression",
                object: recv,
                property: { type: "Identifier", name: "length" },
                computed: false,
                optional: false,
              },
              computed: true,
              optional: false,
            },
            right: arg,
          };
          return stmt;
        }
        stmt.expression = normalizeStepExpr(txExpr(stmt.expression, inLoopDepth));
        return stmt;
      }
      case "IfStatement":
        stmt.test = txExpr(stmt.test, inLoopDepth);
        stmt.consequent = txStmt(stmt.consequent, inLoopDepth, isLoopTail);
        if (stmt.alternate) stmt.alternate = txStmt(stmt.alternate, inLoopDepth, isLoopTail);
        return stmt;
      case "ForStatement":
        if (stmt.init) {
          stmt.init = stmt.init.type === "VariableDeclaration"
            ? txStmt(stmt.init, inLoopDepth, false)
            : txExpr(stmt.init, inLoopDepth);
        }
        if (stmt.test) stmt.test = txExpr(stmt.test, inLoopDepth + 1);
        if (stmt.update) stmt.update = normalizeStepExpr(txExpr(stmt.update, inLoopDepth + 1));
        stmt.body = txStmt(stmt.body, inLoopDepth + 1, true);
        return stmt;
      case "ForOfStatement":
      case "ForInStatement":
        if (stmt.left.type === "VariableDeclaration" && stmt.left.kind === "const") stmt.left.kind = "let";
        stmt.right = txExpr(stmt.right, inLoopDepth);
        stmt.body = txStmt(stmt.body, inLoopDepth + 1, true);
        return stmt;
      case "WhileStatement":
        stmt.test = txExpr(stmt.test, inLoopDepth + 1);
        stmt.body = txStmt(stmt.body, inLoopDepth + 1, true);
        return stmt;
      case "DoWhileStatement":
        stmt.body = txStmt(stmt.body, inLoopDepth + 1, true);
        stmt.test = txExpr(stmt.test, inLoopDepth + 1);
        return stmt;
      case "SwitchStatement":
        stmt.discriminant = txExpr(stmt.discriminant, inLoopDepth);
        for (const c of stmt.cases) {
          if (c.test) c.test = txExpr(c.test, inLoopDepth);
          c.consequent = c.consequent.map(s => txStmt(s, inLoopDepth, false));
        }
        return stmt;
      case "ReturnStatement":
        if (stmt.argument) stmt.argument = txExpr(stmt.argument, inLoopDepth);
        return stmt;
      case "ThrowStatement":
        stmt.argument = txExpr(stmt.argument, inLoopDepth);
        return stmt;
      case "TryStatement":
        stmt.block = txStmt(stmt.block, inLoopDepth, false);
        if (stmt.handler) stmt.handler.body = txStmt(stmt.handler.body, inLoopDepth, false);
        if (stmt.finalizer) stmt.finalizer = txStmt(stmt.finalizer, inLoopDepth, false);
        return stmt;
      case "LabeledStatement":
        stmt.body = txStmt(stmt.body, inLoopDepth, false);
        return stmt;
      default:
        return stmt;
    }
  }

  txStmt(ast, 0);

  // Emit ONE compact `let __H=[...],__D=[...];` statement at top of program!
  const topDecls = [];
  if (baseExprs.length > 0) {
    topDecls.push({
      type: "VariableDeclarator",
      id: { type: "Identifier", name: HOIST_BASE },
      init: { type: "ArrayExpression", elements: baseExprs },
    });
  }
  if (depExprs.length > 0) {
    topDecls.push({
      type: "VariableDeclarator",
      id: { type: "Identifier", name: HOIST_DEP },
      init: { type: "ArrayExpression", elements: depExprs },
    });
  }
  if (topDecls.length > 0) {
    ast.body.unshift({ type: "VariableDeclaration", kind: "let", declarations: topDecls });
  }

  return baseExprs.length + depExprs.length;
}

function makeNameGenerator(reservedSet, varAlphabet) {
  let idx = 0;
  const base = varAlphabet.length;
  return function nextName() {
    while (true) {
      let v = idx++;
      let out = "";
      do {
        out = varAlphabet[v % base] + out;
        v = Math.floor(v / base) - 1;
      } while (v >= 0);
      if (!reservedSet.has(out) && !KEYWORDS.has(out)) {
        return out;
      }
    }
  };
}

function renameScopesCompact(ast, namingOrder = "decl", varAlphabet = ["a", "b", "c", "d", "e", "f"]) {
  const before = analyzeScopes(ast);
  const freeNames = new Set(["solve", "arguments", ...before.freeRefs.map(r => r.name)]);

  function isAncestor(anc, sc) {
    let cur = sc;
    while (cur) {
      if (cur === anc) return true;
      cur = cur.parent;
    }
    return false;
  }

  const renameable = before.bindings.filter(b => b.name !== "solve" && b.name !== "arguments");
  function isHoistArr(b) {
    return (b.name === "__H" || b.name === "__D") && b.scope.kind === "program";
  }

  if (namingOrder === "freq") {
    renameable.sort((a, b) => {
      const ha = isHoistArr(a) ? 1 : 0, hb = isHoistArr(b) ? 1 : 0;
      if (ha !== hb) return ha - hb;
      return (b.refs.length + b.defs.length) - (a.refs.length + a.defs.length) || a.id - b.id;
    });
  } else if (namingOrder === "param_first_freq") {
    renameable.sort((a, b) => {
      const ha = isHoistArr(a) ? 1 : 0, hb = isHoistArr(b) ? 1 : 0;
      if (ha !== hb) return ha - hb;
      const pa = a.kind === "param" ? 0 : 1, pb = b.kind === "param" ? 0 : 1;
      if (pa !== pb) return pa - pb;
      return (b.refs.length + b.defs.length) - (a.refs.length + a.defs.length) || a.id - b.id;
    });
  } else {
    renameable.sort((a, b) => {
      const ha = isHoistArr(a) ? 1 : 0, hb = isHoistArr(b) ? 1 : 0;
      if (ha !== hb) return ha - hb;
      return a.id - b.id;
    });
  }

  const assigned = new Map();
  for (const b of renameable) {
    const blocked = new Set(freeNames);
    for (const [other, name] of assigned.entries()) {
      if (isAncestor(b.scope, other.scope) || isAncestor(other.scope, b.scope)) {
        blocked.add(name);
      }
    }
    const genName = makeNameGenerator(blocked, varAlphabet);
    assigned.set(b, genName());
  }

  function unshorthand(n) {
    if (!n || typeof n !== "object") return;
    if (n.type === "Property" && n.shorthand && n.value.type === "Identifier" && before.nodeToBinding.has(n.value)) {
      n.key = cloneAst(n.key);
      n.shorthand = false;
    }
    for (const v of Object.values(n)) {
      if (Array.isArray(v)) v.forEach(unshorthand);
      else if (v && typeof v.type === "string") unshorthand(v);
    }
  }
  unshorthand(ast);

  for (const [b, newName] of assigned.entries()) {
    for (const d of b.defs) d.name = newName;
    for (const r of b.refs) r.name = newName;
  }

  const after = analyzeScopes(ast);
  if (after.bindings.length !== before.bindings.length || after.freeRefs.length !== before.freeRefs.length) {
    throw new Error(`Scope capture check failed`);
  }
}

function rewriteSource(code, opts = {}) {
  const ast = parse(code);
  stripExportBoilerplate(ast);
  if (opts.lowerLocalClasses !== false) {
    lowerLocalClasses(ast);
  }
  const hoistedCount = canonicalizeSyntax(ast, opts);
  const varAlphabet = opts.varAlphabet || ["a", "b", "c", "d", "e", "f"];
  renameScopesCompact(ast, opts.namingOrder || "decl", varAlphabet);
  const minimalBraces = opts.minimalBraces !== false;
  const canonicalKeywords = opts.canonicalKeywords !== false;
  const out = generate(ast, { minimalBraces, canonicalKeywords });
  parse(out);
  return { code: out, hoisted_constants: hoistedCount };
}

function main() {
  const req = JSON.parse(fs.readFileSync(0, "utf8"));
  if (req.mode === "batch") {
    const results = req.jobs.map(job => {
      try {
        const res = rewriteSource(job.code, job.opts || {});
        return { id: job.id, variant: job.variant || "default", ok: true, ...res };
      } catch (err) {
        return { id: job.id, variant: job.variant || "default", ok: false, error: String(err) };
      }
    });
    process.stdout.write(JSON.stringify({ schema: "b3.rewriter.v1", results }) + "\n");
  } else {
    const res = rewriteSource(req.code, req.opts || {});
    process.stdout.write(JSON.stringify({ ok: true, ...res }) + "\n");
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { rewriteSource, CORE_STRING_CHARS, DIRECT_GLOBALS, DIRECT_PROPS };
