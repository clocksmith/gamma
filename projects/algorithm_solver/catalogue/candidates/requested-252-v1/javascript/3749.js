/**
 * 3749. Evaluate Valid Expressions
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(expression).
 * Algorithm: Iterative operator/value stacks; no recursive descent and no eval.
 * Complexity: O(expression length) arithmetic operations and space; integer operands bounded by the stated long range.
 * Numeric semantics: JavaScript solve and evaluateExpression return BigInt; Python returns int. Both solveJson functions return an exact decimal string. Never coerce a signed 64-bit result to an unsafe Number.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: solve(expression) and evaluateExpression; explicit solveJson adapter for JSON transport. Gamma exact-integer adapter remains pending.
 * Specification: https://leetcode.com/problems/evaluate-valid-expressions/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3749.Evaluate%20Valid%20Expressions/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 */

function solve(expression) {
  const operators = [];
  const values = [];
  let index = 0;
  while (index < expression.length) {
    const character = expression[index];
    if (character === "-" || (character >= "0" && character <= "9")) {
      let end = index + (character === "-" ? 1 : 0);
      while (end < expression.length && expression[end] >= "0" && expression[end] <= "9") end += 1;
      values.push(BigInt(expression.slice(index, end)));
      index = end;
    } else if (character >= "a" && character <= "z") {
      const operator = expression.slice(index, index + 3);
      if (!["add", "sub", "mul", "div"].includes(operator)) throw new TypeError("Unknown operator.");
      operators.push(operator);
      index += 3;
    } else if (character === ")") {
      const right = values.pop();
      const left = values.pop();
      const operator = operators.pop();
      let value;
      if (operator === "add") value = left + right;
      else if (operator === "sub") value = left - right;
      else if (operator === "mul") value = left * right;
      else if (operator === "div") {
        if (right === 0n || left % right !== 0n) throw new RangeError("Division must have a nonzero divisor and exact integer result.");
        value = left / right;
      } else throw new TypeError("Missing operator.");
      values.push(value);
      index += 1;
    } else if (character === "(" || character === ",") {
      index += 1;
    } else throw new TypeError("Unexpected expression character.");
  }
  if (operators.length !== 0 || values.length !== 1) throw new TypeError("Incomplete expression.");
  return values[0];
}

function solveJson(expression) {
  return solve(expression).toString();
}

function evaluateExpression(expression) {
  return solve(expression);
}

class Solution {
  evaluateExpression(expression) {
    return solve(expression);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, solveJson, evaluateExpression, Solution };
}
