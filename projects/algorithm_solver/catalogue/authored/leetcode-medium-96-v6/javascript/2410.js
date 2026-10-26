'use strict';

// 2410. Maximum Matching of Players With Trainers: give each sorted player the first remaining trainer with sufficient capacity.
// O(p log p + t log t) time and O(p + t) auxiliary space; inputs are read-only.
function solve(players, trainers) {
  const abilities = players.slice().sort((left, right) => left - right);
  const capacities = trainers.slice().sort((left, right) => left - right);
  let player = 0;
  for (const capacity of capacities) {
    if (player < abilities.length && abilities[player] <= capacity) player += 1;
  }
  return player;
}

const matchPlayersAndTrainers = solve;
class Solution {
  matchPlayersAndTrainers(players, trainers) { return solve(players, trainers); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, matchPlayersAndTrainers };
