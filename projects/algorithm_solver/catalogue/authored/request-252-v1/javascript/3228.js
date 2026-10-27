// Original candidate; contract and evidence: ../batch1/manifest.json
"use strict";
function solve(s) {
    let ones = 0;
    let answer = 0;
    for (let i = 0; i < s.length; i++) {
        if (s[i] === "1") ones++;
        else if (i > 0 && s[i - 1] === "1") answer += ones;
    }
    return answer;
}
module.exports = {solve};
