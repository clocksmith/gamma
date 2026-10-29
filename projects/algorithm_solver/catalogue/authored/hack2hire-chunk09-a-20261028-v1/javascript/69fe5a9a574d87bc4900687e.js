"use strict";
// Hack2Hire 69fe5a9a574d87bc4900687e (Account Registration Deduplication, variant 2 of 2) over an INFERRED spec; qualification unknown.

function normalEmail(email) {
  const lower = email.toLowerCase();
  const at = lower.indexOf("@");
  let local = lower.slice(0, at);
  const plus = local.indexOf("+");
  if (plus >= 0) local = local.slice(0, plus);
  return local.split(".").join("") + lower.slice(at);
}

function normalPhone(phone) {
  let out = "";
  for (const ch of phone) if (ch >= "0" && ch <= "9") out += ch;
  return out;
}

function solve(names, emails, phones) {
  const seenEmail = new Set(), seenPhone = new Set(), out = [];
  for (let i = 0; i < names.length; i++) {
    const e = normalEmail(emails[i]), p = normalPhone(phones[i]);
    if (seenEmail.has(e) || seenPhone.has(p)) out.push(i);
    else { seenEmail.add(e); seenPhone.add(p); }
  }
  return out;
}

function findDuplicateAccounts(names, emails, phones) { return solve(names, emails, phones); }

module.exports = solve;
module.exports.findDuplicateAccounts = findDuplicateAccounts;
