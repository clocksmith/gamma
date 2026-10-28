'use strict';

// 752. Open the Lock (Medium).
// Specification: https://leetcode.com/problems/open-the-lock/description/
function solve(deadends, target) {
  const dead = new Set(deadends);
  if (dead.has('0000')) return -1;
  if (target === '0000') return 0;
  let queue = ['0000'];
  const visited = new Set(['0000']);
  let steps = 0;
  while (queue.length > 0) {
    steps++;
    const nextQueue = [];
    for (const current of queue) {
      for (let i = 0; i < 4; i++) {
        for (const delta of [-1, 1]) {
          const digit = (Number(current[i]) + delta + 10) % 10;
          const candidate = current.slice(0, i) + String(digit) + current.slice(i + 1);
          if (candidate === target) return steps;
          if (!dead.has(candidate) && !visited.has(candidate)) { visited.add(candidate); nextQueue.push(candidate); }
        }
      }
    }
    queue = nextQueue;
  }
  return -1;
}
const openLock = solve;
class Solution { openLock(deadends, target) { return solve(deadends, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, openLock };
