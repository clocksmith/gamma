'use strict';

function solve(nums) {
    const modulus = 1000000007;
    const left = new Map();
    const right = new Map();
    for (const value of nums) right.set(value, (right.get(value) || 0) + 1);
    let answer = 0;
    for (const value of nums) {
        right.set(value, right.get(value) - 1);
        answer = (answer + (left.get(2 * value) || 0) * (right.get(2 * value) || 0)) % modulus;
        left.set(value, (left.get(value) || 0) + 1);
    }
    return answer;
}
module.exports = { solve };
