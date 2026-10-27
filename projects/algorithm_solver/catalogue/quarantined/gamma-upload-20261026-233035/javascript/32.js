'use strict';
// 32. Longest Valid Parentheses.
function solve(s) {
  const stack = [-1];
  let best = 0;
  for (let index = 0; index < s.length; index += 1) {
    if (s[index] === '(') stack.push(index);
    else {
      stack.pop();
      if (stack.length) best = Math.max(best, index - stack[stack.length - 1]);
      else stack.push(index);
    }
  }
  return best;
}
const longestValidParentheses = solve;
class Solution { longestValidParentheses(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestValidParentheses };
