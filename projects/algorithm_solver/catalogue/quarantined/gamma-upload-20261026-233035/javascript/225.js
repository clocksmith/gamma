'use strict';
// 225. Implement Stack using Queues.
class MyStack {
  constructor() { this.queue = []; }
  push(x) { this.queue.push(x); for (let index = 1; index < this.queue.length; index += 1) this.queue.push(this.queue.shift()); }
  pop() { return this.queue.shift(); }
  top() { return this.queue[0]; }
  empty() { return this.queue.length === 0; }
}
function solve(operations, args) {
  const stack = new MyStack();
  return operations.map((operation, index) => operation === 'MyStack' ? null : stack[operation](...args[index]));
}
if (typeof module !== 'undefined') module.exports = { solve, MyStack };
