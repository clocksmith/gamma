'use strict';
// 281. Zigzag Iterator.
class ZigzagIterator {
  constructor(v1, v2) {
    this.queue = [];
    if (v1.length) this.queue.push([v1, 0]);
    if (v2.length) this.queue.push([v2, 0]);
  }
  next() {
    const [values, index] = this.queue.shift();
    if (index + 1 < values.length) this.queue.push([values, index + 1]);
    return values[index];
  }
  hasNext() { return this.queue.length > 0; }
}
function solve(v1, v2) {
  const iterator = new ZigzagIterator(v1, v2); const result = [];
  while (iterator.hasNext()) result.push(iterator.next());
  return result;
}
if (typeof module !== 'undefined') module.exports = { solve, ZigzagIterator };
