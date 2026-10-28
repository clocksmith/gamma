'use strict';

// 3324. Find the Sequence of Strings Appeared on the Screen (Medium).
// Specification: https://leetcode.com/problems/find-the-sequence-of-strings-appeared-on-the-screen/description/
function solve(target) {
  const out = [];
  let s = '';
  for (const c of target) {
    for (let code = 97; code <= c.charCodeAt(0); code++) {
      s = s + String.fromCharCode(code);
      out.push(s);
      s = s.slice(0, -1);
    }
    s = s + c;
  }
  return out;
}
const stringSequence = solve;
class Solution { stringSequence(target) { return solve(target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, stringSequence };
