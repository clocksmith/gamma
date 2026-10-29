"use strict";

function ListNode(val, next) {
  this.val = val === undefined ? 0 : val;
  this.next = next === undefined ? null : next;
}

class Solution {
  constructor(head) {
    if (Array.isArray(head)) {
      this.vals = head.slice();
    } else {
      const vals = [];
      let cur = head;
      while (cur !== null && cur !== undefined) {
        vals.push(cur.val);
        cur = cur.next;
      }
      this.vals = vals;
    }
    this._state = 0x9e3779b9 >>> 0;
  }
  _randrange(n) {
    this._state = (Math.imul(this._state, 1664525) + 1013904223) >>> 0;
    return this._state % n;
  }
  getRandom() {
    return this.vals[this._randrange(this.vals.length)];
  }
}

function solve(operation_names, argument_lists) {
  const instance = new Solution(argument_lists[0][0]);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i];
    if (op === "getRandom") out.push(instance.getRandom());
    else throw new Error("unknown operation");
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.Solution = Solution;
module.exports.ListNode = ListNode;
