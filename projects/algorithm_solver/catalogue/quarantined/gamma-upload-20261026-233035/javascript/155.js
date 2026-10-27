'use strict';
// 155. Min Stack.
class MinStack {
  constructor() { this.values = []; this.minimums = []; }
  push(val) {
    this.values.push(val);
    this.minimums.push(this.minimums.length ? Math.min(val, this.minimums[this.minimums.length - 1]) : val);
  }
  pop() { this.minimums.pop(); this.values.pop(); }
  top() { return this.values[this.values.length - 1]; }
  getMin() { return this.minimums[this.minimums.length - 1]; }
}
function solve(operations, args) {
  const stack = new MinStack();
  return operations.map((operation, index) => operation === 'MinStack' ? null : stack[operation](...args[index]));
}
if (typeof module !== 'undefined') module.exports = { solve, MinStack };
