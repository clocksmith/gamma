function solve(nums) {
    const positions = [];
    for (let i = 0; i < nums.length; ++i) if (nums[i] % 2 === 0) positions.push(i);
    if (Math.abs(2 * positions.length - nums.length) > 1) return -1;
    let answer = Infinity;
    for (let start = 0; start < 2; ++start) {
        const required = Math.floor((nums.length + 1 - start) / 2);
        if (required !== positions.length) continue;
        let cost = 0;
        for (let i = 0; i < positions.length; ++i) cost += Math.abs(positions[i] - (start + 2 * i));
        answer = Math.min(answer, cost);
    }
    return answer;
}
module.exports = {solve};
