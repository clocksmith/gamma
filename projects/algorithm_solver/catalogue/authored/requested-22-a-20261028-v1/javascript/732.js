"use strict";

const LIMIT = 1000000000;

class MyCalendarThree {
  constructor() {
    // Node 0 is the absent child (maximum 0); node 1 covers [0, LIMIT).
    this.left = [0, 0];
    this.right = [0, 0];
    this.added = [0, 0];
    this.best = [0, 0];
  }
  _child() {
    this.left.push(0);
    this.right.push(0);
    this.added.push(0);
    this.best.push(0);
    return this.best.length - 1;
  }
  _update(node, low, high, start, end) {
    if (start <= low && high <= end) {
      this.added[node]++;
      this.best[node]++;
      return;
    }
    const middle = Math.floor((low + high) / 2);
    if (start < middle) {
      if (!this.left[node]) this.left[node] = this._child();
      this._update(this.left[node], low, middle, start, end);
    }
    if (end > middle) {
      if (!this.right[node]) this.right[node] = this._child();
      this._update(this.right[node], middle, high, start, end);
    }
    this.best[node] = this.added[node] + Math.max(this.best[this.left[node]], this.best[this.right[node]]);
  }
  book(startTime, endTime) {
    this._update(1, 0, LIMIT, startTime, endTime);
    return this.best[1];
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "MyCalendarThree" || argumentLists[0].length !== 0) throw new Error("exact constructor required");
  const instance = new MyCalendarThree(), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (operationNames[i] !== "book") throw new Error("unknown method");
    result.push(instance.book(...argumentLists[i]));
  }
  return result;
}

module.exports = solve;
module.exports.MyCalendarThree = MyCalendarThree;
