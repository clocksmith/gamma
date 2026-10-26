'use strict';

// 1625. Lexicographically Smallest String After Applying Operations: search the finite set of strings reachable by addition and rotation.
// O(R * n) expected time and O(R * n) auxiliary space for R reachable strings; inputs are read-only.
function solve(s, a, b) {
  const seen = new Set([s]);
  const stack = [s];
  let best = s;
  while (stack.length) {
    const current = stack.pop();
    if (current < best) best = current;
    const digits = current.split('');
    for (let index = 1; index < digits.length; index += 2) {
      digits[index] = String((Number(digits[index]) + a) % 10);
    }
    const added = digits.join('');
    const rotated = current.slice(-b) + current.slice(0, -b);
    for (const following of [added, rotated]) {
      if (!seen.has(following)) {
        seen.add(following);
        stack.push(following);
      }
    }
  }
  return best;
}

const findLexSmallestString = solve;
class Solution {
  findLexSmallestString(s, a, b) { return solve(s, a, b); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLexSmallestString };
