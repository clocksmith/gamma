// Original candidate; contract and evidence: ../batch1/manifest.json
"use strict";
function solve(s, k) {
    const lengths = [0n];
    for (const letter of s) {
        let length = lengths[lengths.length-1];
        if (letter === "*") { if (length > 0n) length--; }
        else if (letter === "#") length *= 2n;
        else if (letter !== "%") length++;
        lengths.push(length);
    }
    let index = BigInt(k);
    if (index >= lengths[lengths.length-1]) return ".";
    for (let i = s.length-1; i >= 0; i--) {
        const letter = s[i], before = lengths[i];
        if (letter === "#") index %= before;
        else if (letter === "%") index = before-1n-index;
        else if (letter !== "*" && index === before) return letter;
    }
    return ".";
}
module.exports = {solve};
