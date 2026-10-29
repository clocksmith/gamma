"use strict";
// Hack2Hire 677b092f78175fce2ecdfc0e (Simplify Expression) over an INFERRED spec; qualification unknown.

function solve(expression) {
  const terms = [];
  const groups = [1];
  let pending = 1;
  let i = 0;
  const n = expression.length;
  while (i < n) {
    const c = expression[i];
    if (c === "+") { pending = 1; i++; }
    else if (c === "-") { pending = -1; i++; }
    else if (c === "(") { groups.push(groups[groups.length - 1] * pending); pending = 1; i++; }
    else if (c === ")") { groups.pop(); i++; }
    else {
      let j = i;
      while (j < n && expression[j] >= "a" && expression[j] <= "z") j++;
      terms.push((groups[groups.length - 1] * pending < 0 ? "-" : "+") + expression.slice(i, j));
      pending = 1;
      i = j;
    }
  }
  const text = terms.join("");
  return text[0] === "+" ? text.slice(1) : text;
}

function simplifyExpression(expression) { return solve(expression); }

module.exports = solve;
module.exports.simplifyExpression = simplifyExpression;
