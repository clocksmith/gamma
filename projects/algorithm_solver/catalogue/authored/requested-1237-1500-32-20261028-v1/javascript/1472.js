"use strict";

class BrowserHistory {
  constructor(homepage) {
    this.hist = [homepage];
    this.curr = 0;
    this.end = 0;
  }
  visit(url) {
    this.curr++;
    if (this.curr < this.hist.length) this.hist[this.curr] = url;
    else this.hist.push(url);
    this.end = this.curr;
  }
  back(steps) {
    this.curr = Math.max(0, this.curr - steps);
    return this.hist[this.curr];
  }
  forward(steps) {
    this.curr = Math.min(this.end, this.curr + steps);
    return this.hist[this.curr];
  }
}

function solve(operation_names, argument_lists) {
  const inst = new BrowserHistory(argument_lists[0][0]);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i], args = argument_lists[i];
    if (op === "visit") { inst.visit(args[0]); out.push(null); }
    else if (op === "back") out.push(inst.back(args[0]));
    else out.push(inst.forward(args[0]));
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.BrowserHistory = BrowserHistory;
