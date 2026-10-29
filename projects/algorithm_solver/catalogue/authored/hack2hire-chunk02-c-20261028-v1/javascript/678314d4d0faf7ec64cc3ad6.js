"use strict";
// Hack2Hire 678314d4d0faf7ec64cc3ad6 (Calculate Dasher Salary, variant 1) over an INFERRED spec; qualification unknown.
const RATE_CENTS_PER_MINUTE = 30;
function solve(records) {
  const accepted = new Map(), delivered = new Map();
  for (const [orderId, stamp, status] of records) {
    const minute = Number(stamp.slice(0, 2)) * 60 + Number(stamp.slice(3));
    if (status === "ACCEPTED") accepted.set(orderId, minute);
    else if (status === "DELIVERED") delivered.set(orderId, minute);
  }
  let total = 0;
  for (const [orderId, end] of delivered) total += RATE_CENTS_PER_MINUTE * (end - accepted.get(orderId));
  return total;
}
function calculateSalary(records) { return solve(records); }
module.exports = solve;
module.exports.calculateSalary = calculateSalary;
