'use strict';

function solve(nums, m) {
    if (m === 1) {
        let answer = 0;
        for (const value of nums) answer = Math.max(answer, value * value);
        return answer;
    }
    let minimum = nums[0], maximum = nums[0], answer = -Infinity;
    for (let right = m - 1; right < nums.length; right++) {
        const value = nums[right - m + 1];
        minimum = Math.min(minimum, value);
        maximum = Math.max(maximum, value);
        answer = Math.max(answer, nums[right] * minimum, nums[right] * maximum);
    }
    return answer;
}

module.exports = { solve };
