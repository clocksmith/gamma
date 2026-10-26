'use strict';

// 2071. Maximum Number of Tasks You Can Assign. Binary search with a deque assignment check; O((n+m) log(n+m)) time and O(n+m) space. Inputs are preserved.

function solve(tasks, workers, pills, strength) {
  const jobs = tasks.slice().sort((a, b) => a - b);
  const people = workers.slice().sort((a, b) => a - b);
  function feasible(count) {
    const available = [];
    let head = 0;
    let cursor = 0;
    let remaining = pills;
    for (let index = people.length - count; index < people.length; index += 1) {
      const worker = people[index];
      while (cursor < count && jobs[cursor] <= worker + strength) {
        available.push(jobs[cursor]);
        cursor += 1;
      }
      if (head === available.length) return false;
      if (available[head] <= worker) head += 1;
      else {
        if (remaining === 0) return false;
        remaining -= 1;
        available.pop();
      }
    }
    return true;
  }
  let left = 0;
  let right = Math.min(tasks.length, workers.length);
  while (left < right) {
    const middle = Math.floor((left + right + 1) / 2);
    if (feasible(middle)) left = middle;
    else right = middle - 1;
  }
  return left;
}

const maxTaskAssign = solve;
class Solution {
  maxTaskAssign(tasks, workers, pills, strength) { return solve(tasks, workers, pills, strength); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxTaskAssign };
