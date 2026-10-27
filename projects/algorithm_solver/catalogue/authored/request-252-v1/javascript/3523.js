// Original candidate; contract and evidence: ../batch1/manifest.json
"use strict";
function solve(nums) {
    let maximum = 0, answer = 0;
    for (const number of nums) {
        if (number >= maximum) {
            maximum = number;
            answer++;
        }
    }
    return answer;
}
module.exports = {solve};
