'use strict';

// 2660. Determine the Winner of a Bowling Game (Easy).
// Specification: https://leetcode.com/problems/determine-the-winner-of-a-bowling-game/description/
// O(n) time, O(1) space; either of the previous two strikes doubles a turn once.
function solve(player1, player2) {
  function score(player) {
    let total = 0;
    for (let index = 0; index < player.length; index++) {
      const doubled = (index >= 1 && player[index - 1] === 10) ||
        (index >= 2 && player[index - 2] === 10);
      total += player[index] * (doubled ? 2 : 1);
    }
    return total;
  }
  const first = score(player1);
  const second = score(player2);
  if (first === second) return 0;
  return first > second ? 1 : 2;
}

const isWinner = solve;
class Solution {
  isWinner(player1, player2) { return solve(player1, player2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isWinner };
