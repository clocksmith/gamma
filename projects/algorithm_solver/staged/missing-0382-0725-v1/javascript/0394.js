'use strict';

// 394. Decode String. Decode nested groups with an explicit stack.

function solve(s) {
  const stack = [];
  let parts = [];
  let repeat = 0;
  for (const char of s) {
    if (char >= '0' && char <= '9') repeat = repeat * 10 + Number(char);
    else if (char === '[') { stack.push([parts, repeat]); parts = []; repeat = 0; }
    else if (char === ']') {
      const [previous, count] = stack.pop();
      previous.push(parts.join('').repeat(count));
      parts = previous;
    } else parts.push(char);
  }
  return parts.join('');
}

const decodeString = solve;
class Solution {
  decodeString(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, decodeString };
