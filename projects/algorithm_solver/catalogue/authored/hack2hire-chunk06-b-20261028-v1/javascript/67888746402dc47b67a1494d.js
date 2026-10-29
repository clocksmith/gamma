"use strict";
// Hack2Hire 67888746402dc47b67a1494d (Integer to English Converter, level 3) over an INFERRED spec; qualification unknown.

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

const SCALES = ["", "Thousand", "Million", "Billion"];

function solve(num) {
  if (num === 0) return "Zero";
  const groups = [];
  for (let scale = 0; num > 0; scale++) {
    const chunk = num % 1000;
    if (chunk) groups.push(belowThousand(chunk).concat(scale ? [SCALES[scale]] : []));
    num = Math.floor(num / 1000);
  }
  return groups.reverse().flat().join(" ");
}

function numberToWords(num) { return solve(num); }

module.exports = solve;
module.exports.numberToWords = numberToWords;
