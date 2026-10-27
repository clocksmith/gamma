'use strict';

function solve(complexity) {
    let answer = 1;
    for (let i = 1; i < complexity.length; i++) {
        if (complexity[i] <= complexity[0]) return 0;
        // The unreduced product is below 1e14, within exact Number integers.
        answer = (answer * i) % 1000000007;
    }
    return answer;
}

module.exports = { solve };
