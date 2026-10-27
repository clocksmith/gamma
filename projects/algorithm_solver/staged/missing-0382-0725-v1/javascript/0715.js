'use strict';

// 715. Range Module.

class RangeNode {
  constructor(covered = false) { this.covered = covered; this.left = null; this.right = null; }
}

class RangeModule {
  constructor() { this.root = new RangeNode(); }
  _assign(node, low, high, left, right, covered) {
    if (left <= low && high <= right) {
      node.covered = covered; node.left = null; node.right = null; return;
    }
    if (node.covered !== null) {
      node.left = new RangeNode(node.covered); node.right = new RangeNode(node.covered);
      node.covered = null;
    }
    const middle = Math.floor((low + high) / 2);
    if (left < middle) this._assign(node.left, low, middle, left, right, covered);
    if (right > middle) this._assign(node.right, middle, high, left, right, covered);
    if (node.left.covered !== null && node.left.covered === node.right.covered) {
      node.covered = node.left.covered; node.left = null; node.right = null;
    }
  }
  _query(node, low, high, left, right) {
    if (node.covered !== null) return node.covered;
    if (left <= low && high <= right) return false;
    const middle = Math.floor((low + high) / 2);
    if (right <= middle) return this._query(node.left, low, middle, left, right);
    if (left >= middle) return this._query(node.right, middle, high, left, right);
    return this._query(node.left, low, middle, left, right)
      && this._query(node.right, middle, high, left, right);
  }
  addRange(left, right) { this._assign(this.root, 0, 1000000000, left, right, true); }
  removeRange(left, right) { this._assign(this.root, 0, 1000000000, left, right, false); }
  queryRange(left, right) { return this._query(this.root, 0, 1000000000, left, right); }
}


function solve(operations, args) {
  // Replay the native LeetCode interface with one request-local instance.
  if (operations.length === 0) return [];
  const instance = new RangeModule(...args[0]);
  const result = [null];
  for (let index = 1; index < operations.length; index += 1) {
    const value = instance[operations[index]](...args[index]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = RangeModule;
if (typeof module !== 'undefined') module.exports = { solve, Solution, RangeModule };
