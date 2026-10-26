'use strict';

// 2612. Minimum Reverse Operations: breadth-first search with parity-preserving successor deletion.
// O(n * alpha(n) + len(banned)) amortized time and O(n) space. Inputs are preserved.
function solve(n, p, banned, k) {
  const successor = Int32Array.from({ length: n + 2 }, (_, index) => index);
  function find(index) {
    let root = index;
    while (successor[root] !== root) root = successor[root];
    while (successor[index] !== index) {
      const following = successor[index];
      successor[index] = root;
      index = following;
    }
    return root;
  }
  for (const index of banned) successor[index] = find(index + 2);
  successor[p] = find(p + 2);
  const answer = Array(n).fill(-1);
  answer[p] = 0;
  const queue = [p];
  for (let head = 0; head < queue.length; head += 1) {
    const current = queue[head];
    const minimum = 2 * Math.max(0, current - k + 1) + k - 1 - current;
    const maximum = 2 * Math.min(current, n - k) + k - 1 - current;
    let following = find(minimum);
    while (following <= maximum) {
      answer[following] = answer[current] + 1;
      queue.push(following);
      successor[following] = find(following + 2);
      following = find(following);
    }
  }
  return answer;
}

const minReverseOperations = solve;
class Solution {
  minReverseOperations(n, p, banned, k) { return solve(n, p, banned, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minReverseOperations };
