'use strict';

// 1807. Evaluate the Bracket Pairs of a String: substitute bracketed keys while leaving ordinary text untouched.
// O(n + K + R) expected time and space, with K knowledge size and R output length; inputs are read-only.
function solve(s, knowledge) {
  const values = new Map(knowledge);
  const result = [];
  let index = 0;
  while (index < s.length) {
    if (s[index] !== '(') {
      result.push(s[index]);
      index += 1;
      continue;
    }
    const end = s.indexOf(')', index + 1);
    const key = s.slice(index + 1, end);
    result.push(values.has(key) ? values.get(key) : '?');
    index = end + 1;
  }
  return result.join('');
}

const evaluate = solve;
class Solution {
  evaluate(s, knowledge) { return solve(s, knowledge); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, evaluate };
