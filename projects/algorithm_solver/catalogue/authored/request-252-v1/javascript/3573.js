// Original candidate; contract and evidence: ../batch1/manifest.json
"use strict";
function solve(prices, k) {
    let cash = new Array(k+1).fill(-Infinity);
    let long = cash.slice(), short = cash.slice();
    cash[0] = 0;
    for (const price of prices) {
        const nextCash = cash.slice(), nextLong = long.slice(), nextShort = short.slice();
        for (let done = 0; done < k; done++) {
            nextLong[done] = Math.max(long[done], cash[done]-price);
            nextShort[done] = Math.max(short[done], cash[done]+price);
            nextCash[done+1] = Math.max(cash[done+1], long[done]+price, short[done]-price);
        }
        cash = nextCash; long = nextLong; short = nextShort;
    }
    return Math.max(...cash);
}
module.exports = {solve};
