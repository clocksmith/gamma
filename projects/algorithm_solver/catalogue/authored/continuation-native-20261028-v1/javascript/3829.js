"use strict";

class RideSharingSystem {
  constructor() {
    this.riders = [];
    this.drivers = [];
    this.riderHead = 0;
    this.driverHead = 0;
    this.waiting = new Set();
  }
  addRider(riderId) {
    this.riders.push(riderId);
    this.waiting.add(riderId);
  }
  addDriver(driverId) {
    this.drivers.push(driverId);
  }
  matchDriverWithRider() {
    while (this.riderHead < this.riders.length && !this.waiting.has(this.riders[this.riderHead])) this.riderHead++;
    if (this.riderHead === this.riders.length || this.driverHead === this.drivers.length) return [-1, -1];
    const rider = this.riders[this.riderHead++];
    this.waiting.delete(rider);
    return [this.drivers[this.driverHead++], rider];
  }
  cancelRider(riderId) {
    this.waiting.delete(riderId);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "RideSharingSystem" || argumentLists[0].length !== 0) throw new Error("exact constructor required");
  const instance = new RideSharingSystem(), result = [null];
  const methods = new Set(["addRider", "addDriver", "matchDriverWithRider", "cancelRider"]);
  for (let i = 1; i < operationNames.length; i++) {
    const name = operationNames[i];
    if (!methods.has(name)) throw new Error("unknown method");
    const value = instance[name](...argumentLists[i]);
    result.push(name === "matchDriverWithRider" ? value : null);
  }
  return result;
}

module.exports = solve;
module.exports.RideSharingSystem = RideSharingSystem;
