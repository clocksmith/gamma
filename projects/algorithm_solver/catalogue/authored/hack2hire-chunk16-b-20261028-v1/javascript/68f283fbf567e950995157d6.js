"use strict";
// Hack2Hire 68f283fbf567e950995157d6 (Pig Latin Sentence Converter) over an INFERRED spec; qualification unknown.

function solve(sentence) {
  if (sentence === "") return "";
  const out = [];
  for (const word of sentence.split(" ")) {
    if ("aeiouAEIOU".includes(word[0])) out.push(word + "way");
    else out.push(word.slice(1) + word[0] + "ay");
  }
  return out.join(" ");
}

function toPigLatin(sentence) { return solve(sentence); }

module.exports = solve;
module.exports.toPigLatin = toPigLatin;
