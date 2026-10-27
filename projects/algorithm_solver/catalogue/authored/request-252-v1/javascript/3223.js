'use strict';

function solve(s) {
    const counts = new Int32Array(26);
    for (const ch of s) counts[ch.charCodeAt(0) - 97]++;
    let answer = 0;
    for (const count of counts) {
        if (count) answer += count % 2 ? 1 : 2;
    }
    return answer;
}
module.exports = { solve };
