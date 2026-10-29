"use strict";

class SummaryRanges {
  constructor() {
    this.intervals = [];
  }
  addNum(value) {
    const ivs = this.intervals;
    let low = 0, high = ivs.length;
    while (low < high) {
      const mid = (low + high) >> 1;
      if (ivs[mid][0] <= value) low = mid + 1;
      else high = mid;
    }
    const idx = low;
    if (idx > 0 && ivs[idx - 1][1] >= value) return;
    const leftMerge = idx > 0 && ivs[idx - 1][1] + 1 === value;
    const rightMerge = idx < ivs.length && ivs[idx][0] - 1 === value;
    if (leftMerge && rightMerge) {
      ivs[idx - 1][1] = ivs[idx][1];
      ivs.splice(idx, 1);
    } else if (leftMerge) {
      ivs[idx - 1][1] = value;
    } else if (rightMerge) {
      ivs[idx][0] = value;
    } else {
      ivs.splice(idx, 0, [value, value]);
    }
  }
  getIntervals() {
    return this.intervals.map((iv) => [iv[0], iv[1]]);
  }
}

function solve(operation_names, argument_lists) {
  const instance = new SummaryRanges();
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i];
    const args = argument_lists[i];
    if (op === "addNum") {
      instance.addNum(args[0]);
      out.push(null);
    } else if (op === "getIntervals") {
      out.push(instance.getIntervals());
    } else {
      throw new Error("unknown operation");
    }
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.SummaryRanges = SummaryRanges;
