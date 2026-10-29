"use strict";
// Hack2Hire 678884a8402dc47b67a1494c (Integer to English Converter, level 2) over an INFERRED spec; qualification unknown.

const ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
  "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"];
const TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"];

function belowThousand(x) {
  const words = [];
  if (x >= 100) { words.push(ONES[Math.floor(x / 100)], "Hundred"); x %= 100; }
  if (x >= 20) { words.push(TENS[Math.floor(x / 10)]); x %= 10; }
  if (x) words.push(ONES[x]);
  return words;
}

function solve(num) { return num === 0 ? "Zero" : belowThousand(num).join(" "); }

function numberToWords(num) { return solve(num); }

module.exports = solve;
module.exports.numberToWords = numberToWords;
