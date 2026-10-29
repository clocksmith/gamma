// Original hack2hire:688466f560cda5e0615028a4; inferred public-preview contract; qualification unknown.
"use strict";
function decodePassword(text) {
  const coordinates = text[0].trim().slice(1, -1).split(',').map(v => Number(v.trim()));
  return text[coordinates[1] + 1][coordinates[0]];
}

const solve = decodePassword;
module.exports = solve;
module.exports.decodePassword = decodePassword;
module.exports.Solution = class { decodePassword(...args) { return decodePassword(...args); } };
