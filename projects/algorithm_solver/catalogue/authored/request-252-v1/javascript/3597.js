// Original candidate; contract and evidence: ../batch1/manifest.json
"use strict";
function solve(s) {
    const children = [new Map()], answer = [];
    let node = 0, start = 0;
    for (let index = 0; index < s.length; index++) {
        const letter = s[index];
        if (children[node].has(letter)) node = children[node].get(letter);
        else {
            children[node].set(letter, children.length);
            children.push(new Map());
            answer.push(s.slice(start, index+1));
            start = index+1;
            node = 0;
        }
    }
    return answer;
}
module.exports = {solve};
