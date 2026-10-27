'use strict';
// 294. Flip Game II.
function solve(currentState) {
  const memo = new Map();
  function win(state) {
    if (memo.has(state)) return memo.get(state);
    for (let index = 0; index + 1 < state.length; index += 1) {
      if (state.slice(index, index + 2) === '++') {
        const following = state.slice(0, index) + '--' + state.slice(index + 2);
        if (!win(following)) { memo.set(state, true); return true; }
      }
    }
    memo.set(state, false); return false;
  }
  return win(currentState);
}
const canWin = solve;
class Solution { canWin(currentState) { return solve(currentState); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, canWin };
