"use strict";
// Hack2Hire 69fe5a7f574d87bc4900687d (Account Registration Deduplication, variant 1 of 2) over an INFERRED spec; qualification unknown.

function solve(names, emails, phones) {
  const seenEmail = new Set(), seenPhone = new Set(), out = [];
  for (let i = 0; i < names.length; i++) {
    const e = emails[i], p = phones[i];
    if (seenEmail.has(e) || seenPhone.has(p)) out.push(i);
    else { seenEmail.add(e); seenPhone.add(p); }
  }
  return out;
}

function findDuplicateAccounts(names, emails, phones) { return solve(names, emails, phones); }

module.exports = solve;
module.exports.findDuplicateAccounts = findDuplicateAccounts;
