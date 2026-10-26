'use strict';

// 3709. Design Exam Scores Tracker.
// O(1) amortized record, O(log n) query, O(n) space. Prefix sums remain exact below 1e14.
class ExamTracker {
  constructor() {
    this.times = [];
    this.prefix = [0];
  }
  record(time, score) {
    this.times.push(time);
    this.prefix.push(this.prefix[this.prefix.length - 1] + score);
  }
  bound(value, inclusive) {
    let left = 0;
    let right = this.times.length;
    while (left < right) {
      const middle = left + Math.floor((right - left) / 2);
      if (this.times[middle] < value || (inclusive && this.times[middle] === value)) left = middle + 1;
      else right = middle;
    }
    return left;
  }
  totalScore(startTime, endTime) {
    return this.prefix[this.bound(endTime, true)] - this.prefix[this.bound(startTime, false)];
  }
}

function solve(operations, argumentsList) {
  // Replay the native interface with one request-local instance.
  if (operations.length === 0) return [];
  const instance = new ExamTracker(...argumentsList[0]);
  const result = [null];
  for (let index = 1; index < operations.length; index += 1) {
    const value = instance[operations[index]](...argumentsList[index]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = ExamTracker;
if (typeof module !== 'undefined') module.exports = { solve, Solution, ExamTracker };
