"use strict";
// Hack2Hire 6788830e402dc47b67a1494a (Integer to English Converter, level 1) over an INFERRED spec; qualification unknown.

const DIGITS = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"];

function solve(num) { return DIGITS[num]; }

function numberToWords(num) { return solve(num); }

module.exports = solve;
module.exports.numberToWords = numberToWords;
