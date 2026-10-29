"use strict";

class MyCalendar {
  constructor() {
    this.starts = [];
    this.ends = [];
  }
  book(startTime, endTime) {
    let low = 0, high = this.starts.length;
    while (low < high) {
      const middle = (low + high) >> 1;
      if (this.starts[middle] <= startTime) low = middle + 1;
      else high = middle;
    }
    if (low < this.starts.length && this.starts[low] < endTime) return false;
    if (low > 0 && this.ends[low - 1] > startTime) return false;
    this.starts.splice(low, 0, startTime);
    this.ends.splice(low, 0, endTime);
    return true;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "MyCalendar" || argumentLists[0].length !== 0) throw new Error("exact constructor required");
  const instance = new MyCalendar(), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (operationNames[i] !== "book") throw new Error("unknown method");
    result.push(instance.book(...argumentLists[i]));
  }
  return result;
}

module.exports = solve;
module.exports.MyCalendar = MyCalendar;
