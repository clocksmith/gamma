'use strict';

// 3624. Number of Integers With Popcount-Depth Equal to K II.
// Maintain one Fenwick count tree per reduction depth, updating only a changed value classification; O((n+q) log n+(n+q) log V) time and O(n+q) space. Inputs are preserved.

function solve(nums, queries) {
  const n = nums.length, trees = Array.from({ length: 7 }, () => new Int32Array(n + 1));
  function classify(value) {
    let remaining = BigInt(value), depth = 0;
    while (remaining !== 1n) {
      let amount = 0;
      for (const bit of remaining.toString(2)) if (bit === '1') amount += 1;
      remaining = BigInt(amount); depth += 1;
    }
    return depth;
  }
  function update(depth, index, difference) {
    for (index += 1; index <= n; index += index & -index) trees[depth][index] += difference;
  }
  function prefix(depth, end) {
    let answer = 0;
    for (; end > 0; end -= end & -end) answer += trees[depth][end];
    return answer;
  }
  const depths = nums.map(classify), answers = [];
  depths.forEach((depth, index) => update(depth, index, 1));
  for (const query of queries) {
    if (query[0] === 1) {
      const [, left, right, depth] = query;
      answers.push(prefix(depth, right + 1) - prefix(depth, left));
    } else {
      const [, index, value] = query, following = classify(value);
      update(depths[index], index, -1); update(following, index, 1); depths[index] = following;
    }
  }
  return answers;
}

const popcountDepth = solve;
class Solution {
  popcountDepth(nums, queries) { return solve(nums, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, popcountDepth };
