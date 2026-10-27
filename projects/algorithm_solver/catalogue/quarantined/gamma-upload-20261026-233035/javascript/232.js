'use strict';
// 232. Implement Queue using Stacks.
class MyQueue {
  constructor() { this.input = []; this.output = []; }
  push(x) { this.input.push(x); }
  move() { if (!this.output.length) while (this.input.length) this.output.push(this.input.pop()); }
  pop() { this.move(); return this.output.pop(); }
  peek() { this.move(); return this.output[this.output.length - 1]; }
  empty() { return this.input.length === 0 && this.output.length === 0; }
}
function solve(operations, args) {
  const queue = new MyQueue();
  return operations.map((operation, index) => operation === 'MyQueue' ? null : queue[operation](...args[index]));
}
if (typeof module !== 'undefined') module.exports = { solve, MyQueue };
