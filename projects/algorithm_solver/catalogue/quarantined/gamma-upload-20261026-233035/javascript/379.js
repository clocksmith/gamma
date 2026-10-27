'use strict';
// 379. Design Phone Directory.
class PhoneDirectory {
  constructor(maxNumbers) {
    this.available = Array.from({ length: maxNumbers }, (_, index) => maxNumbers - 1 - index);
    this.used = new Set();
  }
  get() { if (!this.available.length) return -1; const number = this.available.pop(); this.used.add(number); return number; }
  check(number) { return !this.used.has(number); }
  release(number) { if (this.used.delete(number)) this.available.push(number); }
}
function solve(maxNumbers, operations, args) {
  const directory = new PhoneDirectory(maxNumbers);
  return operations.map((operation, index) => directory[operation](...args[index]));
}
if (typeof module !== 'undefined') module.exports = { solve, PhoneDirectory };
