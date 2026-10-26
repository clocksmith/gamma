'use strict';

// 1707. Maximum XOR With an Element From Array: offline limit sweep and binary trie; O(n log n+q log q+31*(n+q)) time and O(31*n+q) space.

function solve(nums, queries) {
  const ordered = nums.slice().sort((a, b) => a - b);
  const pending = queries.map(([value, limit], index) => [limit, value, index]);
  pending.sort((a, b) => a[0] - b[0]);
  const zero = [-1];
  const one = [-1];
  function insert(value) {
    let node = 0;
    for (let bit = 30; bit >= 0; bit -= 1) {
      const children = ((value >>> bit) & 1) !== 0 ? one : zero;
      if (children[node] === -1) {
        children[node] = zero.length;
        zero.push(-1);
        one.push(-1);
      }
      node = children[node];
    }
  }
  const answers = Array(queries.length).fill(-1);
  let count = 0;
  for (const [limit, value, index] of pending) {
    while (count < ordered.length && ordered[count] <= limit) {
      insert(ordered[count]);
      count += 1;
    }
    if (count === 0) continue;
    let node = 0;
    let answer = 0;
    for (let bit = 30; bit >= 0; bit -= 1) {
      const set = ((value >>> bit) & 1) !== 0;
      const preferred = set ? zero : one;
      const fallback = set ? one : zero;
      if (preferred[node] !== -1) {
        answer += 2 ** bit;
        node = preferred[node];
      } else node = fallback[node];
    }
    answers[index] = answer;
  }
  return answers;
}

const maximizeXor = solve;
class Solution {
  maximizeXor(nums, queries) { return solve(nums, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximizeXor };
