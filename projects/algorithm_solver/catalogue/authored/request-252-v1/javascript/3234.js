'use strict';

function solve(s) {
    const n = s.length;
    const zeros = [];
    for (let i = 0; i < n; i++) if (s[i] === '0') zeros.push(i);
    zeros.push(n);
    let first = 0;
    let answer = 0;
    for (let left = 0; left < n; left++) {
        if (zeros[first] < left) first++;
        answer += zeros[first] - left;
        for (let count = 1;
            count * count + count <= n - left && first + count < zeros.length;
            count++) {
            const lastZero = zeros[first + count - 1];
            const nextZero = zeros[first + count];
            const minimumRight = Math.max(lastZero, left + count * count + count - 1);
            answer += Math.max(0, nextZero - minimumRight);
        }
    }
    return answer;
}

module.exports = { solve };
