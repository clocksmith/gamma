'use strict';

function solve(nums, k) {
    for (const target of [1, -1]) {
        let previousFlip = 1;
        let operations = 0;
        for (let i = 0; i + 1 < nums.length; i++) {
            if (nums[i] * previousFlip !== target) {
                operations++;
                previousFlip = -1;
            } else previousFlip = 1;
        }
        if (nums[nums.length - 1] * previousFlip === target && operations <= k) return true;
    }
    return false;
}
module.exports = { solve };
