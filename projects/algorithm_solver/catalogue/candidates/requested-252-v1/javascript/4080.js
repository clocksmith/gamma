'use strict';

// 4080. Design Bus Seat Booking System.
// Specification: https://leetcode.com/problems/design-bus-seat-booking-system/description/
// O(1) operations after parsing a seat identifier; O(n) storage. Each active booking retains its original cost. Retains mutable state on each returned instance; inputs are not modified.
class BusBooking {
  constructor(n) { this.costs = new Uint8Array(4 * n); this.total = 0; this.count = 0; }
  toggle(seat) {
    const column = seat.charCodeAt(0) - 65;
    const row = Number(seat.slice(1)) - 1;
    const index = 4 * row + column;
    if (this.costs[index] > 0) {
      this.total -= this.costs[index];
      this.costs[index] = 0;
      this.count--;
    } else {
      let cost = 1;
      if (column === 0 && this.costs[index + 1] > 0) cost = 3;
      if (column === 3 && this.costs[index - 1] > 0) cost = 3;
      this.costs[index] = cost;
      this.total += cost;
      this.count++;
    }
  }
  getTotalTime() { return this.total; }
  getMinTime() { return this.count; }
}

function solve(n) { return new BusBooking(n); }
if (typeof module !== 'undefined') module.exports = { solve, BusBooking };
