'use strict';
// 352. Data Stream as Disjoint Intervals.
class SummaryRanges {
  constructor() { this.intervals = []; }
  addNum(value) {
    let index = 0;
    while (index < this.intervals.length && this.intervals[index][1] < value - 1) index += 1;
    if (index === this.intervals.length || this.intervals[index][0] > value + 1) {
      this.intervals.splice(index, 0, [value, value]);
      return;
    }
    this.intervals[index][0] = Math.min(this.intervals[index][0], value);
    this.intervals[index][1] = Math.max(this.intervals[index][1], value);
    while (index + 1 < this.intervals.length && this.intervals[index + 1][0] <= this.intervals[index][1] + 1) {
      this.intervals[index][1] = Math.max(this.intervals[index][1], this.intervals[index + 1][1]);
      this.intervals.splice(index + 1, 1);
    }
  }
  getIntervals() { return this.intervals.map(interval => interval.slice()); }
}
function solve(values) {
  const ranges = new SummaryRanges(); const result = [];
  for (const value of values) { ranges.addNum(value); result.push(ranges.getIntervals()); }
  return result;
}
if (typeof module !== 'undefined') module.exports = { solve, SummaryRanges };
