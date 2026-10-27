'use strict';

function solve(responses) {
    const counts = new Map();
    for (const day of responses) {
        for (const word of new Set(day)) counts.set(word, (counts.get(word) || 0) + 1);
    }
    let best = '';
    let frequency = -1;
    for (const [word, count] of counts) {
        if (count > frequency || (count === frequency && word < best)) {
            best = word;
            frequency = count;
        }
    }
    return best;
}

module.exports = { solve };
