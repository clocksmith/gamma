function solve(nums) {
    function digitSum(value) {
        let result = 0;
        while (value) { result += value % 10; value = Math.floor(value / 10); }
        return result;
    }
    const sums = nums.map(digitSum);
    const order = nums.map((_, i) => i).sort((a, b) => sums[a] - sums[b] || nums[a] - nums[b]);
    const seen = new Uint8Array(nums.length);
    let answer = 0;
    for (let start = 0; start < nums.length; ++start) {
        let length = 0, current = start;
        while (!seen[current]) {
            seen[current] = 1;
            ++length;
            current = order[current];
        }
        if (length) answer += length - 1;
    }
    return answer;
}
module.exports = {solve};
