"use strict";
// Original Hack2Hire 6abed50f2faad6972d969c67 variant over an INFERRED specification; qualification unknown.
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
function solve(items) {
  let quantity = 0, cost = 0;
  for (const [, , count, price] of validRows(items)) { quantity += count; cost += count * price; }
  return [quantity, cost];
}
function checkoutTotals(items) { return solve(items); }
module.exports = solve;
module.exports.checkoutTotals = checkoutTotals;
