"use strict";
// Hack2Hire 67709b6d366afdc1233e4ffc (Largest Common BST Value) over an INFERRED spec; qualification unknown.

function decode(a) {
  const values = [a[0]], left = [-1], right = [-1], queue = [0];
  let head = 0, i = 1;
  while (i < a.length) {
    const parent = queue[head++];
    for (const side of [left, right]) {
      if (i < a.length) {
        if (a[i] !== null) {
          values.push(a[i]); left.push(-1); right.push(-1);
          side[parent] = values.length - 1;
          queue.push(values.length - 1);
        }
        i++;
      }
    }
  }
  return [values, left, right];
}

class Descending {
  // reverse in-order walk of a decoded tree with an explicit stack
  constructor([values, left, right]) {
    this.values = values; this.left = left; this.right = right; this.stack = [];
    this.push(0);
  }

  push(node) {
    while (node !== -1) { this.stack.push(node); node = this.right[node]; }
  }

  next() {
    if (this.stack.length === 0) return null;
    const node = this.stack.pop();
    this.push(this.left[node]);
    return this.values[node];
  }
}

function solve(root1, root2) {
  const a = new Descending(decode(root1)), b = new Descending(decode(root2));
  let x = a.next(), y = b.next();
  while (x !== null && y !== null) {
    if (x === y) return x;
    if (x > y) x = a.next();
    else y = b.next();
  }
  return -1;
}

function largestCommonValue(root1, root2) { return solve(root1, root2); }

module.exports = solve;
module.exports.largestCommonValue = largestCommonValue;
