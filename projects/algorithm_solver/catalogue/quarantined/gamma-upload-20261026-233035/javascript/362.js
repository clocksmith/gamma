'use strict';
// 362. Design Hit Counter.
class HitCounter {
  constructor() { this.hits = []; this.head = 0; }
  expire(timestamp) { while (this.head < this.hits.length && this.hits[this.head] <= timestamp - 300) this.head += 1; }
  hit(timestamp) { this.hits.push(timestamp); }
  getHits(timestamp) { this.expire(timestamp); return this.hits.length - this.head; }
}
function solve(operations, args) {
  const counter = new HitCounter();
  return operations.map((operation, index) => operation === 'HitCounter' ? null : counter[operation](...args[index]));
}
if (typeof module !== 'undefined') module.exports = { solve, HitCounter };
