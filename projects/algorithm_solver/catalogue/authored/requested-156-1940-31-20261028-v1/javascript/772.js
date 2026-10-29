"use strict";

function solve(s) {
  let idx = 0;
  const n = s.length;
  function parseExpr() {
    const stack = [];
    let num = 0;
    let op = "+";
    while (idx < n) {
      const ch = s[idx];
      const code = s.charCodeAt(idx);
      const isDigit = code >= 48 && code <= 57;
      if (isDigit) {
        num = num * 10 + (code - 48);
      } else if (ch === "(") {
        idx++;
        num = parseExpr();
      }
      if ((!isDigit && ch !== " ") || idx === n - 1) {
        if (op === "+") stack.push(num);
        else if (op === "-") stack.push(-num);
        else if (op === "*") stack.push(stack.pop() * num);
        else if (op === "/") stack.push(Math.trunc(stack.pop() / num));
        op = ch;
        num = 0;
        if (ch === ")") break;
      }
      idx++;
    }
    let total = 0;
    for (let i = 0; i < stack.length; i++) total += stack[i];
    return total;
  }
  return parseExpr();
}

function calculate(s) {
  return solve(s);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.calculate = calculate;
