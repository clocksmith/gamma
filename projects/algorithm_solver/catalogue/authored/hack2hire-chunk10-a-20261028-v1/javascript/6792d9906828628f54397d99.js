"use strict";
// Hack2Hire 6792d9906828628f54397d99 (Design Query Pagination) over an INFERRED spec; qualification unknown.

function cents(amount) {
  const dot = amount.indexOf(".");
  const whole = dot < 0 ? amount : amount.slice(0, dot), frac = dot < 0 ? "" : amount.slice(dot + 1);
  return Number(whole) * 100 + Number((frac + "00").slice(0, 2));
}

function solve(records, filters, pageSize, pageNumber) {
  const [loT, hiT, loA, hiA, user, currency] = filters;
  const lt = loT === "" ? null : Number(loT), ht = hiT === "" ? null : Number(hiT);
  const la = loA === "" ? null : cents(loA), ha = hiA === "" ? null : cents(hiA);
  const hits = [];
  for (const r of records) {
    const t = Number(r[0]);
    if ((lt !== null && t < lt) || (ht !== null && t > ht)) continue;
    if ((user !== "" && r[2] !== user) || (currency !== "" && r[3] !== currency)) continue;
    if (la !== null || ha !== null) {
      const a = cents(r[4]);
      if ((la !== null && a < la) || (ha !== null && a > ha)) continue;
    }
    hits.push([t, r]);
  }
  hits.sort((a, b) => a[0] - b[0]); // stable: equal timestamps keep input order
  const start = (pageNumber - 1) * pageSize;
  return hits.slice(start, start + pageSize).map(([, r]) => r.slice());
}

function queryTransactions(records, filters, pageSize, pageNumber) { return solve(records, filters, pageSize, pageNumber); }

module.exports = solve;
module.exports.queryTransactions = queryTransactions;
