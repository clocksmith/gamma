"use strict";
// Hack2Hire 69178d9a10632c00111ca20d (Delivery Cost Calculate, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
// scaled = sum of rateCents * seconds stays below 2**53 within the inferred bounds, so Number arithmetic is exact.
function money(scaled) {
  const twice = 2 * scaled + 3600, cents = (twice - twice % 7200) / 7200;
  return Math.floor(cents / 100) + "." + String(cents % 100).padStart(2, "0");
}
class DeliverySystem {
  constructor() {
    this.rates = new Map();
    this.total = 0;
  }
  addDriver(driverId, hourlyRateCents) { this.rates.set(driverId, hourlyRateCents); }
  addDelivery(driverId, startTime, endTime) {
    const scaled = this.rates.get(driverId) * (endTime - startTime);
    this.total += scaled;
  }
  getTotalCost() { return money(this.total); }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "DeliverySystem" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new DeliverySystem(...argumentLists[0]), allowed = new Set(["addDriver", "addDelivery", "getTotalCost"]), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.DeliverySystem = DeliverySystem;
