// Original candidate; contract and evidence: ../batch1/manifest.json
"use strict";
function solve(nums, target) {
    const goal = BigInt(target), values = nums.map(BigInt);
    const total = values.reduce((product, value) => product * value, 1n);
    if (total !== goal * goal) return false;
    function search(index, product, selected) {
        if (index === values.length) return selected > 0 && selected < values.length && product === goal;
        if (search(index+1, product, selected)) return true;
        const next = product * values[index];
        return next <= goal && goal % next === 0n && search(index+1, next, selected+1);
    }
    return search(0, 1n, 0);
}
module.exports = {solve};
