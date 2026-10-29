"use strict";
// Hack2Hire 699f73ca6e73e4abccc9b540 (Caesar Cipher Rotation) over an INFERRED spec; qualification unknown.

function solve(message, shift) {
  const s = ((shift % 26) + 26) % 26;
  const table = [];
  for (let c = 0; c < 128; c++) table.push(String.fromCharCode(c));
  for (let i = 0; i < 26; i++) {
    table[97 + i] = String.fromCharCode(97 + (i + s) % 26);
    table[65 + i] = String.fromCharCode(65 + (i + s) % 26);
  }
  const out = new Array(message.length);
  for (let i = 0; i < message.length; i++) out[i] = table[message.charCodeAt(i)];
  return out.join("");
}

function rotateMessage(message, shift) { return solve(message, shift); }

module.exports = solve;
module.exports.rotateMessage = rotateMessage;
