'use strict';

function solve(instructions, values) {
    const seen = new Uint8Array(values.length);
    let index = 0;
    let score = 0;
    while (index >= 0 && index < values.length && !seen[index]) {
        seen[index] = 1;
        if (instructions[index] === 'add') {
            score += values[index];
            index++;
        } else {
            index += values[index];
        }
    }
    return score;
}

module.exports = { solve };
