// Original candidate; contract and evidence: ../batch1/manifest.json
"use strict";
function solve(a, b, c) {
    const counts = [a, b, c].map(values => {
        let odd = 0;
        for (let value of values) {
            let parity = 0;
            while (value) {
                parity ^= 1;
                value &= value - 1;
            }
            odd += parity;
        }
        return [values.length - odd, odd];
    });
    let answer = 0;
    for (let i = 0; i < 2; i++) {
        for (let j = 0; j < 2; j++) {
            answer += counts[0][i] * counts[1][j] * counts[2][i ^ j];
        }
    }
    return answer;
}
module.exports = {solve};
