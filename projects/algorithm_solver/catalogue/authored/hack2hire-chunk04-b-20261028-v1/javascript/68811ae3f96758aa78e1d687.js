"use strict";
// Hack2Hire 68811ae3f96758aa78e1d687 (Calculate Equation Expression, level 1) over an INFERRED spec; qualification unknown.

function parse(arr) {
  const defs = new Map();
  for (let i = 1; i < arr.length; i++) {
    const tokens = arr[i].split(" ");
    const terms = [["+", tokens[2]]];
    for (let j = 3; j < tokens.length; j += 2) terms.push([tokens[j], tokens[j + 1]]);
    defs.set(tokens[0], terms.map(([sign, tok]) => [sign, tok[0] >= "0" && tok[0] <= "9" ? Number(tok) : tok]));
  }
  return defs;
}

// Iterative three-colour post-order DFS: 1 = on the current path, 2 = evaluated, 3 = failed.
function evaluate(target, defs) {
  const state = new Map(), value = new Map();
  const stack = [target];
  while (stack.length) {
    const name = stack[stack.length - 1];
    const st = state.get(name) || 0;
    if (st === 0) {
      if (!defs.has(name)) { state.set(name, 3); stack.pop(); continue; }
      state.set(name, 1);
      for (const [, op] of defs.get(name)) if (typeof op === "string" && !state.has(op)) stack.push(op);
    } else if (st === 1) {
      stack.pop();
      let total = 0, ok = true;
      for (const [sign, op] of defs.get(name)) {
        let v;
        if (typeof op === "number") v = op;
        else if (state.get(op) === 2) v = value.get(op);
        else { ok = false; break; }
        total = sign === "+" ? total + v : total - v;
      }
      if (ok) { state.set(name, 2); value.set(name, total); } else state.set(name, 3);
    } else stack.pop();
  }
  return value.has(target) ? value.get(target) : null;
}

function solve(arr) { return evaluate(arr[0], parse(arr)); }

function calculate(arr) { return solve(arr); }

module.exports = solve;
module.exports.calculate = calculate;
