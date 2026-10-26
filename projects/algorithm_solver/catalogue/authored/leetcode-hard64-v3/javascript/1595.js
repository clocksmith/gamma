'use strict';

// 1595. Minimum Cost to Connect Two Groups of Points: one edge per first-group point, then cheapest uncovered columns; O(rows*columns*2^columns) time.

function solve(cost) {
  const columns = cost[0].length;
  const full = 1 << columns;
  const cheapest = Array(columns).fill(Infinity);
  for (const row of cost) {
    for (let column = 0; column < columns; column += 1) cheapest[column] = Math.min(cheapest[column], row[column]);
  }
  let previous = Array(full).fill(Infinity);
  previous[0] = 0;
  for (const row of cost) {
    const current = Array(full).fill(Infinity);
    for (let mask = 0; mask < full; mask += 1) {
      if (previous[mask] === Infinity) continue;
      for (let column = 0; column < columns; column += 1) {
        const following = mask | (1 << column);
        current[following] = Math.min(current[following], previous[mask] + row[column]);
      }
    }
    previous = current;
  }
  let answer = Infinity;
  for (let mask = 0; mask < full; mask += 1) {
    let total = previous[mask];
    for (let column = 0; column < columns; column += 1) {
      if ((mask & (1 << column)) === 0) total += cheapest[column];
    }
    answer = Math.min(answer, total);
  }
  return answer;
}

const connectTwoGroups = solve;
class Solution {
  connectTwoGroups(cost) { return solve(cost); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, connectTwoGroups };
