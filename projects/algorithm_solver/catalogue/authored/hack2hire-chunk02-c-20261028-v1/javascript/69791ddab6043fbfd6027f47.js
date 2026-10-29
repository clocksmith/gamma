"use strict";
// Hack2Hire 69791ddab6043fbfd6027f47 (Cloud Service Usage Cost, variant 2) over an INFERRED spec; qualification unknown.
function scaled(rate) { // BigInt units of 1e-4 dollars
  const [whole, fraction = ""] = rate.split(".");
  return BigInt(whole) * 10000n + BigInt((fraction + "0000").slice(0, 4));
}
function money(units) {
  const cents = (units + 50n) / 100n;
  return String(cents / 100n) + "." + String(cents % 100n).padStart(2, "0");
}
function serviceCost(rate, hours) {
  if (typeof rate === "string") return scaled(rate) * BigInt(hours);
  let cost = 0n, charged = 0;
  for (const [limit, tierRate] of rate) {
    const upto = limit === null ? hours : Math.min(limit, hours);
    if (upto > charged) { cost += BigInt(upto - charged) * scaled(tierRate); charged = upto; }
    if (charged >= hours) break;
  }
  return cost;
}
function costs(usageReport, pricingTable) {
  const prices = Object.prototype.hasOwnProperty.call(pricingTable, usageReport.region) ? pricingTable[usageReport.region] : {};
  const hours = new Map();
  for (const row of usageReport.services) {
    if (Object.prototype.hasOwnProperty.call(prices, row.service)) hours.set(row.service, (hours.get(row.service) || 0) + row.hours);
  }
  return [...hours].map(([name, total]) => [name, serviceCost(prices[name], total)]);
}
function solve(usageReport, pricingTable) {
  return money(costs(usageReport, pricingTable).reduce((sum, entry) => sum + entry[1], 0n));
}
function calculateCost(usageReport, pricingTable) { return solve(usageReport, pricingTable); }
module.exports = solve;
module.exports.calculateCost = calculateCost;
