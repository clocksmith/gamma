'use strict';

// 2182. Construct String With Repeat Limit: emit the largest available letter and use one smaller separator when needed.
// O(n) time and O(n) output-construction space for a fixed 26-letter alphabet; inputs are read-only.
function solve(s, repeatLimit) {
  const counts = new Array(26).fill(0);
  for (let index = 0; index < s.length; index += 1) counts[s.charCodeAt(index) - 97] += 1;
  const pieces = [];
  let current = 25;
  while (current >= 0) {
    if (counts[current] === 0) { current -= 1; continue; }
    const take = Math.min(repeatLimit, counts[current]);
    pieces.push(String.fromCharCode(97 + current).repeat(take));
    counts[current] -= take;
    if (counts[current] === 0) { current -= 1; continue; }
    let separator = current - 1;
    while (separator >= 0 && counts[separator] === 0) separator -= 1;
    if (separator < 0) break;
    pieces.push(String.fromCharCode(97 + separator));
    counts[separator] -= 1;
  }
  return pieces.join('');
}

const repeatLimitedString = solve;
class Solution {
  repeatLimitedString(s, repeatLimit) { return solve(s, repeatLimit); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, repeatLimitedString };
