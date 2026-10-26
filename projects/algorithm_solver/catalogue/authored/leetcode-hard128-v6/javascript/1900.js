'use strict';

// 1900. The Earliest and Latest Rounds Where Players Compete.
// Memoize protected-player positions; enumerate reachable winner counts without enumerating complete tournaments.

function solve(n, firstPlayer, secondPlayer) {
  const memo = new Map();
  function rounds(size, first, second) {
    if (first + second === size + 1) return [1, 1];
    const key = `${size},${first},${second}`;
    if (memo.has(key)) return memo.get(key);
    let reachable = new Set([0]);
    const base = size + 1;
    for (let left = 1; left <= Math.ceil(size / 2); left += 1) {
      const right = size + 1 - left;
      let winners;
      if (left === first || left === second) winners = [left];
      else if (right === first || right === second) winners = [right];
      else winners = left === right ? [left] : [left, right];
      const following = new Set();
      for (const state of reachable) {
        const a = Math.floor(state / base), b = state % base;
        for (const winner of winners) following.add((a + Number(winner < first)) * base + b + Number(winner < second));
      }
      reachable = following;
    }
    let earliest = size, latest = 0;
    for (const state of reachable) {
      const [low, high] = rounds(Math.ceil(size / 2), Math.floor(state / base) + 1, state % base + 1);
      earliest = Math.min(earliest, low + 1); latest = Math.max(latest, high + 1);
    }
    const answer = [earliest, latest];
    memo.set(key, answer);
    return answer;
  }
  return rounds(n, Math.min(firstPlayer, secondPlayer), Math.max(firstPlayer, secondPlayer)).slice();
}

const earliestAndLatest = solve;
class Solution {
  earliestAndLatest(n, firstPlayer, secondPlayer) { return solve(n, firstPlayer, secondPlayer); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, earliestAndLatest };
