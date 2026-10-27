'use strict';

function solve(nums) {
    let single = 0;
    let double = 0;
    for (const value of nums) {
        if (value < 10) single += value;
        else double += value;
    }
    return single !== double;
}
module.exports = { solve };
