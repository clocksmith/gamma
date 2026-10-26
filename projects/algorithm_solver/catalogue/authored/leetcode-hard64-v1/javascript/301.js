'use strict';

// 301. Remove Invalid Parentheses: two directional passes removing only surplus parentheses.
// O(n * 2^n) time; O(n^2) stack strings plus output. Inputs are preserved.
function solve(s) {
  const answers = [];
  function visit(text, scanStart, removalStart, opening, closing) {
    let balance = 0;
    for (let index = scanStart; index < text.length; index += 1) {
      if (text[index] === opening) balance += 1;
      else if (text[index] === closing) balance -= 1;
      if (balance >= 0) continue;
      for (let remove = removalStart; remove <= index; remove += 1) {
        if (text[remove] === closing && (remove === removalStart || text[remove - 1] !== closing)) {
          visit(text.slice(0, remove) + text.slice(remove + 1), index, remove, opening, closing);
        }
      }
      return;
    }
    const reversed = text.split('').reverse().join('');
    if (opening === '(') visit(reversed, 0, 0, ')', '(');
    else answers.push(reversed);
  }
  visit(s, 0, 0, '(', ')');
  return answers;
}

const removeInvalidParentheses = solve;
class Solution {
  removeInvalidParentheses(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeInvalidParentheses };
