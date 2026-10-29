"use strict";
// Hack2Hire 678d3e738c349080cddc5f5e (Evaluate String Expression II) over an INFERRED spec; qualification unknown.

function solve(expression) {
  const stack = []; // frames [operation, accumulator]
  let result = null;
  let i = 0;
  const n = expression.length;
  while (i < n) {
    const c = expression[i];
    if (c === " ") { i++; continue; }
    if (c === "(") {
      i++;
      while (expression[i] === " ") i++;
      const operation = expression.slice(i, i + 3);
      i += 3;
      stack.push([operation, operation === "add" ? 0 : 1]);
      continue;
    }
    let value;
    if (c === ")") {
      value = stack.pop()[1];
      i++;
    } else {
      let j = i + 1;
      while (j < n && expression[j] !== " " && expression[j] !== "(" && expression[j] !== ")") j++;
      value = Number(expression.slice(i, j));
      i = j;
    }
    if (stack.length) {
      const frame = stack[stack.length - 1];
      frame[1] = frame[0] === "add" ? frame[1] + value : frame[1] * value;
    } else {
      result = value;
    }
  }
  return result === 0 ? 0 : result; // never -0
}

function evaluate(expression) { return solve(expression); }

module.exports = solve;
module.exports.evaluate = evaluate;
