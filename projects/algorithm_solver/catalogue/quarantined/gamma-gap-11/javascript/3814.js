'use strict';

// 3814. Maximum Capacity Within Budget.
// O(n log n) time and O(n) space; strictly enforces budget and distinct machine indices.
function solve(costs, capacity, budget) {
  const machines = costs.map((cost, index) => [cost, capacity[index]]);
  machines.sort((left, right) => left[0] - right[0]);
  const prefixBest = [];
  let answer = 0;
  for (let index = 0; index < machines.length; index += 1) {
    const [cost, value] = machines[index];
    if (cost < budget) answer = Math.max(answer, value);
    let low = 0;
    let high = index;
    while (low < high) {
      const middle = Math.floor((low + high) / 2);
      if (machines[middle][0] < budget - cost) low = middle + 1;
      else high = middle;
    }
    if (low > 0) answer = Math.max(answer, value + prefixBest[low - 1]);
    prefixBest.push(Math.max(value, index > 0 ? prefixBest[index - 1] : 0));
  }
  return answer;
}

const maxCapacity = solve;
class Solution {
  maxCapacity(costs, capacity, budget) { return solve(costs, capacity, budget); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxCapacity };
