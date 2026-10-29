"use strict";
// Hack2Hire 696feb8db7afade5b30a39ca (Business CSV Data Validator, variant 1) over an INFERRED spec; qualification unknown.
const ID = /^[A-Za-z0-9]+$/, AMOUNT = /^(0|[1-9][0-9]*)(\.[0-9]{2})?$/, DATE = /^([0-9]{4})-([0-9]{2})-([0-9]{2})$/;
function words(field) { return field.toLowerCase().match(/[a-z0-9]+/g) || []; }
function validDate(text) {
  const match = DATE.exec(text);
  if (!match) return false;
  const year = Number(match[1]), month = Number(match[2]), day = Number(match[3]);
  if (year < 1900 || year > 2099 || month < 1 || month > 12) return false;
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1];
  return day >= 1 && day <= days;
}
function solve(data, forbiddenWords, ignoreWords) {
  const forbidden = new Set(forbiddenWords), ignore = new Set(ignoreWords), seenIds = new Set(), valid = [];
  for (let index = 1; index < data.length; index++) {
    const fields = data[index].split(",");
    if (fields.length !== 6 || fields.some(f => f === "" || f !== f.replace(/^ +| +$/g, ""))) continue;
    const [recordId, name, description, category, amount, day] = fields;
    if (!ID.test(recordId) || seenIds.has(recordId) || !AMOUNT.test(amount) || !validDate(day)) continue;
    const groups = [name, description, category].map(words);
    if (groups.some(group => group.some(word => forbidden.has(word)))) continue;
    const left = groups[0].filter(w => !ignore.has(w)), right = groups[1].filter(w => !ignore.has(w));
    if (left.length === right.length && left.every((w, i) => w === right[i])) continue;
    seenIds.add(recordId);
    valid.push(index);
  }
  return valid;
}
function validateRows(data, forbiddenWords, ignoreWords) { return solve(data, forbiddenWords, ignoreWords); }
module.exports = solve;
module.exports.validateRows = validateRows;
