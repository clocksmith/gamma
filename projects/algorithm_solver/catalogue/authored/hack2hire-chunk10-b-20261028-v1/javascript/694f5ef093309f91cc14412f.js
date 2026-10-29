"use strict";
// Hack2Hire 694f5ef093309f91cc14412f (Evaluate JSON Expression Tree) over an INFERRED spec; qualification unknown.

function value(node) {
  const op = node.operation;
  if (op === "CONSTANT_NUMBER") return node.value;
  const a = value(node.inputs[0]), b = value(node.inputs[1]);
  if (op === "ADD") return a + b;
  if (op === "SUBTRACT") return a - b;
  if (op === "MULTIPLY") return a * b;
  const x = Math.abs(a), y = Math.abs(b);
  const q = (x - (x % y)) / y; // exact truncation toward zero
  return (a < 0) === (b < 0) || q === 0 ? q : -q;
}

function solve(expression) {
  const v = value(expression);
  return v === 0 ? 0 : v; // never report negative zero
}

function evaluate(expression) { return solve(expression); }

module.exports = solve;
module.exports.evaluate = evaluate;
