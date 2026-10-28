"use strict";

class ExamTracker {
  constructor() {
    this.times = [];
    this.prefix = [0];
  }
  record(time, score) {
    this.times.push(time);
    this.prefix.push(this.prefix[this.prefix.length - 1] + score);
  }
  totalScore(startTime, endTime) {
    const boundary = (value, inclusive) => {
      let low = 0, high = this.times.length;
      while (low < high) {
        const middle = Math.floor((low + high) / 2);
        if (this.times[middle] < value || (inclusive && this.times[middle] === value)) low = middle + 1;
        else high = middle;
      }
      return low;
    };
    return this.prefix[boundary(endTime, true)] - this.prefix[boundary(startTime, false)];
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ExamTracker" || argumentLists[0].length !== 0) throw new Error("exact constructor required");
  const instance = new ExamTracker(), result = [null];
  const methods = new Set(["record", "totalScore"]);
  for (let i = 1; i < operationNames.length; i++) {
    const name = operationNames[i];
    if (!methods.has(name)) throw new Error("unknown method");
    const value = instance[name](...argumentLists[i]);
    result.push(name === "record" ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.ExamTracker = ExamTracker;
