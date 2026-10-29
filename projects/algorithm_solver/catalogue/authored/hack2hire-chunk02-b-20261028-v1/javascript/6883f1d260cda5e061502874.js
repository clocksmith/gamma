"use strict";
// Original Hack2Hire 6883f1d260cda5e061502874 variant over an INFERRED specification; qualification unknown.
function cents(amount) {
  const dot = amount.indexOf(".");
  if (dot < 0) return Number(amount) * 100;
  return Number(amount.slice(0, dot)) * 100 + Number((amount.slice(dot + 1) + "00").slice(0, 2));
}
function format(value) {
  const sign = value < 0 ? "-" : "", v = Math.abs(value);
  return sign + Math.floor(v / 100) + "." + String(v % 100).padStart(2, "0");
}
function solve(records) {
  const column = new Map(records[0].map((name, i) => [name, i]));
  const p = column.get("product"), d = column.get("date"), c = column.get("cost"), s = column.get("sell_price");
  const profit = new Map(), months = new Set(), products = new Set();
  for (let i = 1; i < records.length; i++) {
    const row = records[i], month = row[d].slice(0, 7), key = row[p] + "\n" + month;
    months.add(month); products.add(row[p]);
    profit.set(key, (profit.get(key) || 0) + cents(row[s]) - cents(row[c]));
  }
  const monthList = [...months].sort();
  const table = [["product", ...monthList]];
  for (const product of [...products].sort()) table.push([product, ...monthList.map((m) => format(profit.get(product + "\n" + m) || 0))]);
  return table;
}
function pivotProfit(records) { return solve(records); }
module.exports = solve;
module.exports.pivotProfit = pivotProfit;
