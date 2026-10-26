'use strict';

// 3664. Two-Letter Card Game.
// O(n) time and O(1) auxiliary space for the fixed alphabet; inputs are preserved.
function solve(cards, x) {
  const left = Array(26).fill(0);
  const right = Array(26).fill(0);
  let double = 0;
  for (const card of cards) {
    if (card[0] === x && card[1] === x) double += 1;
    else if (card[0] === x) left[card.charCodeAt(1) - 97] += 1;
    else if (card[1] === x) right[card.charCodeAt(0) - 97] += 1;
  }
  const leftTotal = left.reduce((sum, count) => sum + count, 0);
  const rightTotal = right.reduce((sum, count) => sum + count, 0);
  const leftMax = Math.max(...left);
  const rightMax = Math.max(...right);
  let answer = 0;
  for (let assigned = 0; assigned <= double; assigned += 1) {
    const a = leftTotal + assigned;
    const b = rightTotal + double - assigned;
    const first = Math.min(Math.floor(a / 2), a - Math.max(leftMax, assigned));
    const second = Math.min(Math.floor(b / 2), b - Math.max(rightMax, double - assigned));
    answer = Math.max(answer, first + second);
  }
  return answer;
}

const score = solve;
class Solution {
  score(cards, x) { return solve(cards, x); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, score };
