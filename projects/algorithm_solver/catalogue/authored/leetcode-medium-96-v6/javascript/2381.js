'use strict';

// 2381. Shifting Letters II: accumulate signed interval shifts in a difference array.
// O(n + q) time and O(n) auxiliary and result space; inputs are read-only.
function solve(s, shifts) {
  const difference = new Int32Array(s.length + 1);
  for (const [start, end, direction] of shifts) {
    const amount = direction === 1 ? 1 : -1;
    difference[start] += amount;
    difference[end + 1] -= amount;
  }
  let current = 0;
  const result = [];
  for (let index = 0; index < s.length; index += 1) {
    current += difference[index];
    const letter = ((s.charCodeAt(index) - 97 + current) % 26 + 26) % 26;
    result.push(String.fromCharCode(97 + letter));
  }
  return result.join('');
}

const shiftingLetters = solve;
class Solution {
  shiftingLetters(s, shifts) { return solve(s, shifts); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, shiftingLetters };
