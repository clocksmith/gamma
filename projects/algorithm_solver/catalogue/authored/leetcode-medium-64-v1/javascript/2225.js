'use strict';

// 2225. Find Players With Zero or One Losses: record every participating player and sort the zero-loss and one-loss groups.
// O(m + p log p) expected time and O(p) auxiliary space for m matches and p players; inputs are read-only.
function solve(matches) {
  const losses = new Map();
  for (const [winner, loser] of matches) {
    if (!losses.has(winner)) losses.set(winner, 0);
    losses.set(loser, (losses.get(loser) || 0) + 1);
  }
  const undefeated = [];
  const oneLoss = [];
  for (const [player, count] of losses) {
    if (count === 0) undefeated.push(player);
    if (count === 1) oneLoss.push(player);
  }
  undefeated.sort((left, right) => left - right);
  oneLoss.sort((left, right) => left - right);
  return [undefeated, oneLoss];
}

const findWinners = solve;
class Solution {
  findWinners(matches) { return solve(matches); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findWinners };
