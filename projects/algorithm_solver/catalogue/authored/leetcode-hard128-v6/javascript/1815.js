'use strict';

// 1815. Maximum Number of Groups Getting Fresh Donuts.
// Remove zero/complement remainders, then memoize remaining remainder counts. O(b^2*S+n) time, O(b*S+n) space; S is the count-state space. Inputs are preserved.

function solve(batchSize, groups) {
  const counts = Array(batchSize).fill(0);
  for (const value of groups) counts[value % batchSize] += 1;
  let answer = counts[0];
  counts[0] = 0;
  for (let value = 1; 2 * value < batchSize; value += 1) {
    const pairs = Math.min(counts[value], counts[batchSize - value]);
    counts[value] -= pairs; counts[batchSize - value] -= pairs; answer += pairs;
  }
  if (batchSize % 2 === 0) {
    answer += Math.floor(counts[batchSize / 2] / 2);
    counts[batchSize / 2] %= 2;
  }
  const memo = new Map();
  function best(remainder) {
    const key = `${remainder}:${counts.join(',')}`;
    if (memo.has(key)) return memo.get(key);
    let result = 0;
    for (let value = 1; value < batchSize; value += 1) {
      if (counts[value] === 0) continue;
      counts[value] -= 1;
      result = Math.max(result, Number(remainder === 0) + best((remainder + value) % batchSize));
      counts[value] += 1;
    }
    memo.set(key, result);
    return result;
  }
  return answer + best(0);
}

const maxHappyGroups = solve;
class Solution {
  maxHappyGroups(batchSize, groups) { return solve(batchSize, groups); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxHappyGroups };
