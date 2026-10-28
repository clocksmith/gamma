'use strict';

// 394. Decode String (Medium).
// Specification: https://leetcode.com/problems/decode-string/description/
function solve(s) {
  const countStack = [];
  const stringStack = [];
  let current = '';
  let number = 0;
  for (const ch of s) {
    if (ch >= '0' && ch <= '9') number = number * 10 + Number(ch);
    else if (ch === '[') { countStack.push(number); stringStack.push(current); current = ''; number = 0; }
    else if (ch === ']') { const repeat = countStack.pop(); const previous = stringStack.pop(); current = previous + current.repeat(repeat); }
    else current += ch;
  }
  return current;
}
const decodeString = solve;
class Solution { decodeString(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, decodeString };
