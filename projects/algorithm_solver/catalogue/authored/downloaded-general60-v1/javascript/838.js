'use strict';

// 838. Push Dominoes (Medium).
// Specification: https://leetcode.com/problems/push-dominoes/description/
function solve(dominoes) {
  const n = dominoes.length;
  const forces = new Array(n).fill(0);
  let force = 0;
  for (let i = 0; i < n; i++) {
    if (dominoes[i] === 'R') force = n;
    else if (dominoes[i] === 'L') force = 0;
    else force = Math.max(force - 1, 0);
    forces[i] += force;
  }
  force = 0;
  for (let i = n - 1; i >= 0; i--) {
    if (dominoes[i] === 'L') force = n;
    else if (dominoes[i] === 'R') force = 0;
    else force = Math.max(force - 1, 0);
    forces[i] -= force;
  }
  let result = '';
  for (let i = 0; i < n; i++) result += forces[i] > 0 ? 'R' : forces[i] < 0 ? 'L' : '.';
  return result;
}
const pushDominoes = solve;
class Solution { pushDominoes(dominoes) { return solve(dominoes); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, pushDominoes };
