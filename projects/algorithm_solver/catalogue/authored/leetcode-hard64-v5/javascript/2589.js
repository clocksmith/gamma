'use strict';

// 2589. Minimum Time to Complete All Tasks. Schedule latest unused instants using a Fenwick tree and predecessor links; O(n log n+(n+T) log(T+1)) time and O(n+T) space, T=max(end). Inputs are preserved.

function solve(tasks) {
  let limit = 0;
  for (const task of tasks) limit = Math.max(limit, task[1] + 2);
  const tree = Array(limit).fill(0);
  const parent = Array.from({ length: limit }, (_, index) => index);
  function prefix(index) {
    let result = 0;
    while (index > 0) { result += tree[index]; index -= index & -index; }
    return result;
  }
  function activate(index) {
    while (index < limit) { tree[index] += 1; index += index & -index; }
  }
  function available(index) {
    while (parent[index] !== index) {
      parent[index] = parent[parent[index]];
      index = parent[index];
    }
    return index;
  }
  let answer = 0;
  for (const [start, end, duration] of tasks.slice().sort((a, b) => a[1] - b[1])) {
    let missing = duration - (prefix(end + 1) - prefix(start));
    while (missing > 0) {
      const index = available(end + 1);
      activate(index);
      parent[index] = available(index - 1);
      missing -= 1;
      answer += 1;
    }
  }
  return answer;
}

const findMinimumTime = solve;
class Solution {
  findMinimumTime(tasks) { return solve(tasks); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMinimumTime };
