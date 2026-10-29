"use strict";

class MyCalendarTwo {
  constructor() {
    this.bookings = [];
    this.overlaps = [];
  }
  book(startTime, endTime) {
    for (const [start, end] of this.overlaps) if (start < endTime && startTime < end) return false;
    for (const [start, end] of this.bookings) {
      if (start < endTime && startTime < end) this.overlaps.push([Math.max(start, startTime), Math.min(end, endTime)]);
    }
    this.bookings.push([startTime, endTime]);
    return true;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "MyCalendarTwo" || argumentLists[0].length !== 0) throw new Error("exact constructor required");
  const instance = new MyCalendarTwo(), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (operationNames[i] !== "book") throw new Error("unknown method");
    result.push(instance.book(...argumentLists[i]));
  }
  return result;
}

module.exports = solve;
module.exports.MyCalendarTwo = MyCalendarTwo;
