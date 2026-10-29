"use strict";
// Hack2Hire 67872240e20f8f324213c297 (Evaluate String Expression) over an INFERRED spec; qualification unknown.

function solve(expression) {
  const s = expression, n = s.length, stack = [];  // frames {add, acc, count}
  let result = null, i = 0;
  const give = (value) => {
    if (!stack.length) { result = value; return; }
    const f = stack[stack.length - 1];
    f.acc = f.add || f.count === 0 ? f.acc + value : f.acc - value;
    f.count++;
  };
  while (i < n) {
    const ch = s.charCodeAt(i);
    if (ch === 32 || ch === 40 || ch === 44) i++;  // space ( ,
    else if (ch === 97 || ch === 115) { stack.push({add: ch === 97, acc: 0, count: 0}); i += 3; }  // a s
    else if (ch === 41) { give(stack.pop().acc); i++; }  // )
    else {
      let neg = false, value = 0;
      if (ch === 45) { neg = true; i++; }
      while (i < n) { const d = s.charCodeAt(i) - 48; if (d < 0 || d > 9) break; value = value * 10 + d; i++; }
      give(neg ? -value : value);
    }
  }
  return result;
}

function evaluate(expression) { return solve(expression); }

module.exports = solve;
module.exports.evaluate = evaluate;
