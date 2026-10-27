'use strict';

function solve(s) {
    const candidates = new Set();
    for (let left = 0; left < s.length; left++) {
        let value = 0;
        for (let right = left; right < s.length; right++) {
            value = 10 * value + Number(s[right]);
            candidates.add(value);
        }
    }
    let answer = 0;
    let count = 0;
    for (const number of [...candidates].sort((a, b) => b - a)) {
        if (number < 2 || (number !== 2 && number % 2 === 0)) continue;
        let prime = true;
        for (let divisor = 3; divisor * divisor <= number; divisor += 2) {
            if (number % divisor === 0) {
                prime = false;
                break;
            }
        }
        if (prime) {
            answer += number;
            if (++count === 3) break;
        }
    }
    return answer;
}

module.exports = { solve };
