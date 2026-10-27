function solve(nums, k) {
    function gcd(a, b) { while (b) [a, b] = [b, a % b]; return a; }
    const twos = nums.map(value => {
        let count = 0;
        while (value % 2 === 0) { ++count; value /= 2; }
        return count;
    });
    let answer = 0;
    for (let left = 0; left < nums.length; ++left) {
        let divisor = 0, minimumTwos = 31, minimumCount = 0;
        for (let right = left; right < nums.length; ++right) {
            divisor = gcd(divisor, nums[right]);
            if (twos[right] < minimumTwos) { minimumTwos = twos[right]; minimumCount = 1; }
            else if (twos[right] === minimumTwos) ++minimumCount;
            const multiplier = minimumCount <= k ? 2 : 1;
            answer = Math.max(answer, divisor * multiplier * (right - left + 1));
        }
    }
    return answer;
}
module.exports = {solve};
