'use strict';

// 1366. Rank Teams by Votes: compare complete position-count vectors before alphabetical order.
// O(v * t + t^2 log t) time and O(t^2) auxiliary space for v votes and t teams; inputs are read-only.
function solve(votes) {
  const teams = [...votes[0]];
  const counts = new Map(teams.map(team => [team, new Array(teams.length).fill(0)]));
  for (const vote of votes) {
    for (let position = 0; position < vote.length; position += 1) counts.get(vote[position])[position] += 1;
  }
  teams.sort((left, right) => {
    for (let position = 0; position < teams.length; position += 1) {
      const difference = counts.get(right)[position] - counts.get(left)[position];
      if (difference !== 0) return difference;
    }
    return left < right ? -1 : left > right ? 1 : 0;
  });
  return teams.join('');
}

const rankTeams = solve;
class Solution {
  rankTeams(votes) { return solve(votes); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, rankTeams };
