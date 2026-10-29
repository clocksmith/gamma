"use strict";
// Hack2Hire 688bc3a43867670cfb89417c (Phone Number Word Matching) over an INFERRED spec; qualification unknown.

const DIGIT = new Map();
['', '', 'abc', 'def', 'ghi', 'jkl', 'mno', 'pqrs', 'tuv', 'wxyz'].forEach((letters, d) => { for (const ch of letters) DIGIT.set(ch, String(d)); });

function solve(knownWords, phoneNumber) {
  return knownWords.filter((w) => w.length === phoneNumber.length && Array.from(w, (ch) => DIGIT.get(ch)).join('') === phoneNumber);
}

function matchWords(knownWords, phoneNumber) { return solve(knownWords, phoneNumber); }

module.exports = solve;
module.exports.matchWords = matchWords;
