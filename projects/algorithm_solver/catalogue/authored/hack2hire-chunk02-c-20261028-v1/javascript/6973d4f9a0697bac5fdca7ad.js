"use strict";
// Hack2Hire 6973d4f9a0697bac5fdca7ad (Cloud Service Usage Cost, variant 1) over an INFERRED spec; qualification unknown.
function scaled(rate) { // BigInt units of 1e-4 dollars
  const [whole, fraction = ""] = rate.split(".");
  return BigInt(whole) * 10000n + BigInt((fraction + "0000").slice(0, 4));
}
function money(units) {
  const cents = (units + 50n) / 100n;
  return String(cents / 100n) + "." + String(cents % 100n).padStart(2, "0");
}
function solve(usageReport, pricingTable) {
  const prices = Object.prototype.hasOwnProperty.call(pricingTable, usageReport.region) ? pricingTable[usageReport.region] : {};
  let total = 0n;
  for (const row of usageReport.services) {
    if (Object.prototype.hasOwnProperty.call(prices, row.service)) total += scaled(prices[row.service]) * BigInt(row.hours);
  }
  return money(total);
}
function calculateCost(usageReport, pricingTable) { return solve(usageReport, pricingTable); }
module.exports = solve;
module.exports.calculateCost = calculateCost;
