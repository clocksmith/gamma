// Original candidate; contract and evidence: ../batch1/manifest.json
"use strict";
function solve(nums, k) {
    const minimum = [], maximum = [], prefix = [0, 1];
    let minHead = 0, maxHead = 0, left = 0, answer = 0;
    for (let right = 0; right < nums.length; right++) {
        while (minimum.length > minHead && nums[minimum[minimum.length-1]] >= nums[right]) minimum.pop();
        while (maximum.length > maxHead && nums[maximum[maximum.length-1]] <= nums[right]) maximum.pop();
        minimum.push(right); maximum.push(right);
        while (nums[maximum[maxHead]] - nums[minimum[minHead]] > k) {
            if (minimum[minHead] === left) minHead++;
            if (maximum[maxHead] === left) maxHead++;
            left++;
        }
        answer = (prefix[right+1] - prefix[left] + 1000000007) % 1000000007;
        prefix.push((prefix[prefix.length-1] + answer) % 1000000007);
    }
    return answer;
}
module.exports = {solve};
