"use strict";
// Hack2Hire 68dc5d69dd5418be11109b00 (Spelling Bee Word Finder) over an INFERRED spec; qualification unknown.

function solve(requiredLetter, optionalLetters, dictionary) {
  const required = 1 << (requiredLetter.charCodeAt(0) - 97);
  let allowed = required;
  for (const ch of optionalLetters) allowed |= 1 << (ch.charCodeAt(0) - 97);
  const out = [];
  for (const word of dictionary) {
    if (word.length < 4) continue;
    let mask = 0;
    for (let i = 0; i < word.length; i++) mask |= 1 << (word.charCodeAt(i) - 97);
    if ((mask & required) && !(mask & ~allowed)) out.push(word);
  }
  return out;
}

function findValidWords(requiredLetter, optionalLetters, dictionary) { return solve(requiredLetter, optionalLetters, dictionary); }

module.exports = solve;
module.exports.findValidWords = findValidWords;
