'use strict';

// 3801. Minimum Cost to Merge Sorted Lists.
// O(N log N + 2^m * N + 3^m) time and O(N + 2^m) space, m <= 12 and total elements N <= 2000.
function solve(lists) {
  const count = lists.length;
  const size = 2 ** count;
  const ordered = [];
  for (let owner = 0; owner < count; owner += 1) for (const value of lists[owner]) ordered.push([value, owner]);
  ordered.sort((left, right) => left[0] - right[0] || left[1] - right[1]);
  const lengths = new Int32Array(size);
  const medians = new Float64Array(size);
  const cost = Array(size).fill(Infinity);
  cost[0] = 0;
  for (let mask = 1; mask < size; mask += 1) {
    const bit = mask & -mask;
    const index = Math.log2(bit);
    lengths[mask] = lengths[mask ^ bit] + lists[index].length;
    let position = Math.floor((lengths[mask] - 1) / 2);
    for (const [value, owner] of ordered) {
      if ((mask & (1 << owner)) === 0) continue;
      if (position === 0) {
        medians[mask] = value;
        break;
      }
      position -= 1;
    }
    if (mask === bit) {
      cost[mask] = 0;
      continue;
    }
    for (let subset = (mask - 1) & mask; subset > 0; subset = (subset - 1) & mask) {
      if ((subset & bit) === 0) continue;
      const other = mask ^ subset;
      const candidate = cost[subset] + cost[other] + lengths[mask] + Math.abs(medians[subset] - medians[other]);
      cost[mask] = Math.min(cost[mask], candidate);
    }
  }
  return cost[size - 1];
}

const minMergeCost = solve;
class Solution {
  minMergeCost(lists) { return solve(lists); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMergeCost };
