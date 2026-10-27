'use strict';
// 346. Moving Average from Data Stream.
class MovingAverage {
  constructor(size) { this.size = size; this.values = []; this.head = 0; this.total = 0; }
  next(val) {
    this.values.push(val); this.total += val;
    if (this.values.length - this.head > this.size) this.total -= this.values[this.head++];
    return this.total / (this.values.length - this.head);
  }
}
function solve(size, values) {
  const average = new MovingAverage(size);
  return values.map(value => average.next(value));
}
if (typeof module !== 'undefined') module.exports = { solve, MovingAverage };
