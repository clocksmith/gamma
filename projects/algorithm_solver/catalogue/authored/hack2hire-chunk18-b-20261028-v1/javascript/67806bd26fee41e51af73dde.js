"use strict";
// Hack2Hire 67806bd26fee41e51af73dde (Prefix to Postfix) over an INFERRED spec; qualification unknown.

function solve(expression) {
  const out = [];
  const ops = [], done = [];  // open operators and their finished operand counts
  for (const ch of expression) {
    if ("+-*/^".includes(ch)) { ops.push(ch); done.push(0); continue; }
    out.push(ch);
    // a finished operand may complete a chain of open operators
    while (ops.length) {
      done[done.length - 1] += 1;
      if (done[done.length - 1] < 2) break;
      done.pop();
      out.push(ops.pop());
    }
  }
  return out.join("");
}

function prefixToPostfix(expression) { return solve(expression); }

module.exports = solve;
module.exports.prefixToPostfix = prefixToPostfix;
