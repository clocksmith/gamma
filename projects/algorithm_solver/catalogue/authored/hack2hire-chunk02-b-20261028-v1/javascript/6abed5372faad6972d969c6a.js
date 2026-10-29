"use strict";
// Original Hack2Hire 6abed5372faad6972d969c6a variant over an INFERRED specification; qualification unknown.
function digits(field) {
  if (field === "") return false;
  for (let i = 0; i < field.length; i++) { const ch = field.charCodeAt(i); if (ch < 48 || ch > 57) return false; }
  return true;
}
function validRows(items) {
  const rows = [];
  for (const item of items) {
    const fields = item.split("|");
    if (fields.length !== 4) continue;
    const [sku, name, count, price] = fields;
    if (sku && name && digits(count) && digits(price)) rows.push([sku, name, Number(count), Number(price)]);
  }
  return rows;
}
function aggregate(items) {
  const totals = new Map();
  for (const [sku, name, count, price] of validRows(items)) {
    if (!totals.has(sku)) totals.set(sku, [name, 0, 0]);
    const row = totals.get(sku);
    row[1] += count; row[2] += count * price;
  }
  return totals;
}
const line = (sku, row) => sku + "|" + row[0] + "|" + row[1] + "|" + row[2];
function solve(items) {
  const totals = aggregate(items);
  return [...totals.keys()].sort().map((sku) => line(sku, totals.get(sku)));
}
function checkoutBySku(items) { return solve(items); }
module.exports = solve;
module.exports.checkoutBySku = checkoutBySku;
