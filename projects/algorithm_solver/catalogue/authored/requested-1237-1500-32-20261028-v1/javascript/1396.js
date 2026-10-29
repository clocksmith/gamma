"use strict";

class UndergroundSystem {
  constructor() {
    this.cin = new Map();
    this.stats = new Map();
  }
  checkIn(id, stationName, t) {
    this.cin.set(id, [stationName, t]);
  }
  checkOut(id, stationName, t) {
    const [st, t0] = this.cin.get(id);
    this.cin.delete(id);
    const key = st + "#" + stationName;
    let pair = this.stats.get(key);
    if (!pair) { pair = [0, 0]; this.stats.set(key, pair); }
    pair[0] += t - t0;
    pair[1] += 1;
  }
  getAverageTime(startStation, endStation) {
    const [tot, cnt] = this.stats.get(startStation + "#" + endStation);
    return tot / cnt;
  }
}

function solve(operation_names, argument_lists) {
  const inst = new UndergroundSystem();
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i], args = argument_lists[i];
    if (op === "checkIn") { inst.checkIn(args[0], args[1], args[2]); out.push(null); }
    else if (op === "checkOut") { inst.checkOut(args[0], args[1], args[2]); out.push(null); }
    else out.push(inst.getAverageTime(args[0], args[1]));
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.UndergroundSystem = UndergroundSystem;
