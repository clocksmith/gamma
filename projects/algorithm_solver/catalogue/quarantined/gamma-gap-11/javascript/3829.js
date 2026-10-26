'use strict';

// 3829. Design Ride Sharing System.
// O(Q) expected total time and O(Q) storage for Q calls; FIFO matching with lazy cancellation.
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
    while (this.riderHead < this.riders.length && !this.waiting.has(this.riders[this.riderHead])) this.riderHead += 1;
    if (this.driverHead === this.drivers.length || this.riderHead === this.riders.length) return [-1, -1];
    const rider = this.riders[this.riderHead];
    const driver = this.drivers[this.driverHead];
    this.riderHead += 1;
    this.driverHead += 1;
    this.waiting.delete(rider);
    return [driver, rider];
  }

  cancelRider(riderId) {
    this.waiting.delete(riderId);
  }
}

function solve(operations, argumentsList) {
  // Replay the native interface with one request-local instance.
  if (operations.length === 0) return [];
  const instance = new RideSharingSystem(...argumentsList[0]);
  const result = [null];
  for (let index = 1; index < operations.length; index += 1) {
    const value = instance[operations[index]](...argumentsList[index]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = RideSharingSystem;
if (typeof module !== 'undefined') module.exports = { solve, Solution, RideSharingSystem };
