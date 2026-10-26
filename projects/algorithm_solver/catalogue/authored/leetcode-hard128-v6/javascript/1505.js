'use strict';

// 1505. Minimum Possible Integer After at Most K Adjacent Swaps On Digits.
// Greedily extract the smallest reachable digit using a Fenwick tree of removals; O(10*n*log n) time, O(n) space.

function solve(num, k) {
  const n = num.length;
  const positions = Array.from({ length: 10 }, () => []);
  for (let i = 0; i < n; i += 1) positions[Number(num[i])].push(i);
  const heads = Array(10).fill(0), removed = Array(n + 1).fill(0), answer = [];
  for (let output = 0; output < n; output += 1) {
    for (let digit = 0; digit < 10; digit += 1) {
      if (heads[digit] === positions[digit].length) continue;
      const position = positions[digit][heads[digit]];
      let before = 0;
      for (let i = position + 1; i > 0; i -= i & -i) before += removed[i];
      const cost = position - before;
      if (cost > k) continue;
      k -= cost;
      answer.push(String(digit));
      heads[digit] += 1;
      for (let i = position + 1; i <= n; i += i & -i) removed[i] += 1;
      break;
    }
  }
  return answer.join('');
}

const minInteger = solve;
class Solution {
  minInteger(num, k) { return solve(num, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minInteger };
