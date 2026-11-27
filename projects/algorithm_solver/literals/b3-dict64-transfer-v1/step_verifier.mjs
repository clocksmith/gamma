"use strict";
// Deterministic Node execution, hidden-helper auditor, and runtime-step verifier.
//
// Deterministic runtime-step counter rules (zero wall-clock nondeterminism):
//   +1 per function / arrow / method invocation entry
//   +1 per loop iteration (for, for..of, for..in, while, do..while)
//   +1 per executed statement
//   +1 per call / new expression
//
// Enforces hard step ceiling, VM timeout, clean isolated context (zero hidden
// helpers), and static free-identifier audit against strict ES built-ins.

import fs from "node:fs";
import vm from "node:vm";
import { parse, generate, cloneAst, analyzeScopes } from "./js_ast.mjs";

const ALLOWED_ES_GLOBALS = new Set([
  "Math", "Array", "Number", "String", "BigInt", "Map", "Set", "Object",
  "JSON", "RegExp", "Error", "RangeError", "TypeError", "SyntaxError",
  "Infinity", "NaN", "undefined", "parseInt", "parseFloat", "isNaN", "isFinite",
  "Int8Array", "Uint8Array", "Int16Array", "Uint16Array", "Int32Array", "Uint32Array",
  "Float32Array", "Float64Array", "BigInt64Array", "BigUint64Array",
  "Symbol", "Boolean", "globalThis", "arguments",
]);

const FORBIDDEN_GLOBALS = new Set(["eval", "Function", "require", "process", "global"]);

function tickStmt() {
  return {
    type: "ExpressionStatement",
    expression: {
      type: "CallExpression",
      callee: { type: "Identifier", name: "__b3t" },
      arguments: [{ type: "Literal", value: 1, raw: "1" }],
      optional: false,
    },
  };
}

function tickWrapExpr(expr) {
  return {
    type: "SequenceExpression",
    expressions: [
      {
        type: "CallExpression",
        callee: { type: "Identifier", name: "__b3t" },
        arguments: [{ type: "Literal", value: 1, raw: "1" }],
        optional: false,
      },
      expr,
    ],
  };
}

function instrumentAst(ast) {
  const copy = cloneAst(ast);

  function instExpr(node) {
    if (!node) return node;
    switch (node.type) {
      case "CallExpression":
        node.callee = instExpr(node.callee);
        node.arguments = node.arguments.map(a =>
          a.type === "SpreadElement" ? { ...a, argument: instExpr(a.argument) } : instExpr(a)
        );
        return tickWrapExpr(node);
      case "NewExpression":
        node.callee = instExpr(node.callee);
        node.arguments = node.arguments.map(a =>
          a.type === "SpreadElement" ? { ...a, argument: instExpr(a.argument) } : instExpr(a)
        );
        return tickWrapExpr(node);
      case "MemberExpression":
        node.object = instExpr(node.object);
        if (node.computed) node.property = instExpr(node.property);
        return node;
      case "BinaryExpression":
      case "LogicalExpression":
        node.left = instExpr(node.left);
        node.right = instExpr(node.right);
        return node;
      case "ConditionalExpression":
        node.test = instExpr(node.test);
        node.consequent = instExpr(node.consequent);
        node.alternate = instExpr(node.alternate);
        return node;
      case "AssignmentExpression":
        if (node.left.type === "MemberExpression") node.left = instExpr(node.left);
        node.right = instExpr(node.right);
        return node;
      case "UnaryExpression":
      case "UpdateExpression":
        node.argument = instExpr(node.argument);
        return node;
      case "SequenceExpression":
        node.expressions = node.expressions.map(instExpr);
        return node;
      case "ArrayExpression":
        node.elements = node.elements.map(e => {
          if (!e) return null;
          if (e.type === "SpreadElement") return { ...e, argument: instExpr(e.argument) };
          return instExpr(e);
        });
        return node;
      case "ObjectExpression":
        node.properties = node.properties.map(p => {
          if (p.type === "SpreadElement") return { ...p, argument: instExpr(p.argument) };
          if (p.computed) p.key = instExpr(p.key);
          p.value = instExpr(p.value);
          return p;
        });
        return node;
      case "TemplateLiteral":
        node.expressions = node.expressions.map(instExpr);
        return node;
      case "FunctionExpression":
        node.body = instBlockBody(node.body, true);
        return node;
      case "ArrowFunctionExpression":
        if (node.body.type === "BlockStatement") {
          node.body = instBlockBody(node.body, true);
        } else {
          node.body = tickWrapExpr(instExpr(node.body));
        }
        return node;
      case "ClassExpression":
        for (const m of node.body.body) {
          if (m.computed) m.key = instExpr(m.key);
          m.value = instExpr(m.value);
        }
        return node;
      default:
        return node;
    }
  }

  function instLoopBody(body) {
    if (body.type === "BlockStatement") {
      return instBlockBody(body, true);
    }
    const inner = instStmt(body);
    return { type: "BlockStatement", body: [tickStmt(), ...inner] };
  }

  function instBlockBody(block, addEntryTick) {
    const out = [];
    if (addEntryTick) out.push(tickStmt());
    for (const s of block.body) {
      out.push(...instStmt(s));
    }
    return { type: "BlockStatement", body: out };
  }

  function instStmt(node) {
    if (!node) return [];
    switch (node.type) {
      case "EmptyStatement":
        return [node];
      case "BlockStatement":
        return [instBlockBody(node, false)];
      case "FunctionDeclaration":
        node.body = instBlockBody(node.body, true);
        return [node];
      case "ClassDeclaration":
        if (node.superClass) node.superClass = instExpr(node.superClass);
        for (const m of node.body.body) {
          if (m.computed) m.key = instExpr(m.key);
          m.value = instExpr(m.value);
        }
        return [node];
      case "VariableDeclaration":
        for (const d of node.declarations) {
          if (d.init) d.init = instExpr(d.init);
        }
        return [tickStmt(), node];
      case "ExpressionStatement":
        node.expression = instExpr(node.expression);
        return [tickStmt(), node];
      case "ReturnStatement":
        if (node.argument) node.argument = instExpr(node.argument);
        return [tickStmt(), node];
      case "ThrowStatement":
        node.argument = instExpr(node.argument);
        return [tickStmt(), node];
      case "BreakStatement":
      case "ContinueStatement":
        return [tickStmt(), node];
      case "IfStatement":
        node.test = instExpr(node.test);
        node.consequent = node.consequent.type === "BlockStatement"
          ? instBlockBody(node.consequent, false)
          : { type: "BlockStatement", body: instStmt(node.consequent) };
        if (node.alternate) {
          node.alternate = node.alternate.type === "BlockStatement"
            ? instBlockBody(node.alternate, false)
            : (node.alternate.type === "IfStatement"
              ? { type: "BlockStatement", body: instStmt(node.alternate) }
              : { type: "BlockStatement", body: instStmt(node.alternate) });
        }
        return [tickStmt(), node];
      case "ForStatement":
        if (node.init) {
          if (node.init.type === "VariableDeclaration") {
            for (const d of node.init.declarations) if (d.init) d.init = instExpr(d.init);
          } else {
            node.init = instExpr(node.init);
          }
        }
        if (node.test) node.test = instExpr(node.test);
        if (node.update) node.update = instExpr(node.update);
        node.body = instLoopBody(node.body);
        return [tickStmt(), node];
      case "ForOfStatement":
      case "ForInStatement":
        node.right = instExpr(node.right);
        node.body = instLoopBody(node.body);
        return [tickStmt(), node];
      case "WhileStatement":
      case "DoWhileStatement":
        node.test = instExpr(node.test);
        node.body = instLoopBody(node.body);
        return [tickStmt(), node];
      case "SwitchStatement":
        node.discriminant = instExpr(node.discriminant);
        for (const c of node.cases) {
          if (c.test) c.test = instExpr(c.test);
          const nextCons = [];
          for (const s of c.consequent) nextCons.push(...instStmt(s));
          c.consequent = nextCons;
        }
        return [tickStmt(), node];
      case "TryStatement":
        node.block = instBlockBody(node.block, false);
        if (node.handler) node.handler.body = instBlockBody(node.handler.body, false);
        if (node.finalizer) node.finalizer = instBlockBody(node.finalizer, false);
        return [tickStmt(), node];
      case "LabeledStatement": {
        const inner = instStmt(node.body);
        node.body = inner.length === 1 ? inner[0] : { type: "BlockStatement", body: inner };
        return [node];
      }
      default:
        return [tickStmt(), node];
    }
  }

  const outBody = [];
  for (const s of copy.body) {
    outBody.push(...instStmt(s));
  }
  return { type: "Program", body: outBody };
}

function auditSource(code, ast, allowCjsExport = false, injectedHelper = null) {
  if (injectedHelper !== null && injectedHelper !== undefined && injectedHelper !== "") {
    return { ok: false, reason: "injected_hidden_helper_forbidden", details: ["external helper code supplied"] };
  }
  const scopeInfo = analyzeScopes(ast);
  const badIdents = [];
  const allowed = new Set(ALLOWED_ES_GLOBALS);
  if (allowCjsExport) {
    allowed.add("module");
    allowed.add("exports");
  }
  for (const b of scopeInfo.bindings) {
    if (b.name.startsWith("__b3")) badIdents.push(`reserved_binding:${b.name}`);
  }
  for (const ref of scopeInfo.freeRefs) {
    if (ref.name.startsWith("__b3")) {
      badIdents.push(`reserved_ref:${ref.name}`);
    } else if (FORBIDDEN_GLOBALS.has(ref.name)) {
      badIdents.push(`forbidden_global:${ref.name}`);
    } else if (!allowed.has(ref.name)) {
      badIdents.push(`undeclared_free_identifier:${ref.name}`);
    }
  }
  if (badIdents.length > 0) {
    return { ok: false, reason: "undeclared_or_hidden_helper", details: [...new Set(badIdents)].sort() };
  }
  return { ok: true, reason: "ok", details: [] };
}

function runProgramJob(job) {
  const code = job.code;
  const entry = job.entry || "solve";
  const iface = job.interface || "function";
  const method = job.method || entry;
  const cases = job.cases || [];
  const stepLimit = job.step_limit || 20_000_000;
  const timeoutMs = job.timeout_ms || 3000;
  const allowCjsExport = Boolean(job.allow_cjs_export);
  const injectedHelper = job.injected_helper || null;

  let ast;
  try {
    ast = parse(code);
  } catch (err) {
    return { id: job.id, ok: false, reason: "parse_error", error: String(err), total_steps: 0, records: [] };
  }

  const audit = auditSource(code, ast, allowCjsExport, injectedHelper);
  if (!audit.ok) {
    return {
      id: job.id,
      ok: false,
      reason: audit.reason,
      error: audit.details.join(", "),
      audit,
      total_steps: 0,
      records: [],
    };
  }

  let instrumentedCode;
  try {
    const instAst = instrumentAst(ast);
    instrumentedCode = generate(instAst);
  } catch (err) {
    return { id: job.id, ok: false, reason: "instrument_error", error: String(err), total_steps: 0, records: [] };
  }

  let steps = 0;
  const sandbox = {};
  if (allowCjsExport) {
    sandbox.module = { exports: {} };
    sandbox.exports = sandbox.module.exports;
  }
  Object.defineProperty(sandbox, "__b3t", {
    value: function (k) {
      steps += k;
      if (steps > stepLimit) {
        throw new Error("__B3_STEP_LIMIT__");
      }
    },
    writable: false,
    configurable: false,
    enumerable: false,
  });

  const ctx = vm.createContext(sandbox);
  try {
    vm.runInContext(instrumentedCode, ctx, { filename: `${job.id || "program"}.js`, timeout: timeoutMs });
  } catch (err) {
    return {
      id: job.id,
      ok: false,
      reason: String(err).includes("__B3_STEP_LIMIT__") ? "step_limit_exceeded" : "load_error",
      error: String(err),
      total_steps: steps,
      records: [],
    };
  }
  const initSteps = steps;

  let target;
  try {
    target = vm.runInContext(entry, ctx, { timeout: timeoutMs });
  } catch (err) {
    return {
      id: job.id,
      ok: false,
      reason: "missing_entrypoint",
      error: String(err),
      total_steps: steps,
      records: [],
    };
  }

  const records = [];
  for (let i = 0; i < cases.length; i++) {
    const rawArgs = cases[i].args;
    const argsBefore = JSON.parse(JSON.stringify(rawArgs));
    // Materialize args inside the VM realm so Array.isArray / instanceof work cleanly
    const vmArgs = vm.runInContext("JSON.parse(" + JSON.stringify(JSON.stringify(rawArgs)) + ")", ctx);
    const beforeSteps = steps;
    let rec;
    try {
      let result;
      if (iface === "class") {
        const inst = new target();
        result = inst[method](...vmArgs);
      } else {
        result = target(...vmArgs);
      }
      const caseSteps = steps - beforeSteps;
      // Normalize via JSON roundtrip inside host to verify plain JSON values
      const normResult = result === undefined ? null : JSON.parse(JSON.stringify(result));
      const normArgsAfter = JSON.parse(JSON.stringify(vmArgs));
      rec = { i, result: normResult, args_before: argsBefore, args_after: normArgsAfter, steps: caseSteps };
    } catch (err) {
      const caseSteps = steps - beforeSteps;
      rec = { i, error: String(err), args_before: argsBefore, args_after: argsBefore, steps: caseSteps };
    }
    records.push(rec);
  }

  return {
    id: job.id,
    ok: true,
    reason: "ok",
    init_steps: initSteps,
    total_steps: steps,
    records,
  };
}

function main() {
  const inputRaw = fs.readFileSync(0, "utf8");
  const req = JSON.parse(inputRaw);
  if (req.mode === "batch") {
    const results = req.jobs.map(runProgramJob);
    process.stdout.write(JSON.stringify({ schema: "b3.step_verifier.v1", results }) + "\n");
  } else {
    const result = runProgramJob(req);
    process.stdout.write(JSON.stringify(result) + "\n");
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { runProgramJob, instrumentAst, auditSource, ALLOWED_ES_GLOBALS };
