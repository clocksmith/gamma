"use strict";
// Hack2Hire 692d0f861abcca80b112238f (Basic Calculator) over an INFERRED spec; qualification unknown.

function divide(a, b) {
  return (a - (a % b)) / b + 0;  // exact truncation toward zero for |a|, |b| < 2**53; + 0 clears -0
}

function combine(term, mulop, value) {
  if (mulop === "*") return term * value;
  if (mulop === "/") return divide(term, value);
  return value;
}

function solve(s) {
  const stack = [];
  let total = 0, term = 0, sign = 1, mulop = "", negate = false, expectOperand = true;
  let i = 0;
  const n = s.length;
  while (i < n) {
    const ch = s[i];
    if (ch >= "0" && ch <= "9") {
      let j = i;
      while (j < n && s[j] >= "0" && s[j] <= "9") j++;
      let value = Number(s.slice(i, j));
      if (negate) value = -value;
      term = combine(term, mulop, value);
      mulop = ""; negate = false; expectOperand = false;
      i = j;
      continue;
    }
    if (expectOperand) {
      if (ch === "-") negate = !negate;
      else { stack.push([total, term, sign, mulop, negate]); total = 0; term = 0; sign = 1; mulop = ""; negate = false; }
    } else if (ch === ")") {
      let value = total + sign * term;
      [total, term, sign, mulop, negate] = stack.pop();
      if (negate) value = -value;
      term = combine(term, mulop, value);
      mulop = ""; negate = false;
    } else if (ch === "+" || ch === "-") {
      total += sign * term;
      term = 0; sign = ch === "+" ? 1 : -1; expectOperand = true;
    } else {
      mulop = ch; expectOperand = true;
    }
    i++;
  }
  return total + sign * term + 0;
}

function calculate(s) { return solve(s); }

module.exports = solve;
module.exports.calculate = calculate;
