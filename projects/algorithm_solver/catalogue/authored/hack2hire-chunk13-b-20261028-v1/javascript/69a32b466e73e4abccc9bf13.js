"use strict";
// Hack2Hire 69a32b466e73e4abccc9bf13 (Reverse Middle of Vowel Words) over an INFERRED spec; qualification unknown.

const VOWELS = new Set("aeiouAEIOU");

function solve(text) {
  return text.map((word) => {
    if (word.length >= 2 && VOWELS.has(word[0]) && VOWELS.has(word[word.length - 1])) {
      return word[0] + word.slice(1, -1).split("").reverse().join("") + word[word.length - 1];
    }
    return word;
  });
}

function reverseVowelWordMiddles(text) { return solve(text); }

module.exports = solve;
module.exports.reverseVowelWordMiddles = reverseVowelWordMiddles;
