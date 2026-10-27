function solve(nums) {
    const n = nums.length, prime = new Uint8Array(n).fill(1);
    prime[0] = 0;
    if (n > 1) prime[1] = 0;
    for (let factor = 2; factor * factor < n; ++factor) {
        if (prime[factor]) {
            for (let multiple = factor * factor; multiple < n; multiple += factor) prime[multiple] = 0;
        }
    }
    let difference = 0;
    for (let i = 0; i < n; ++i) difference += prime[i] ? nums[i] : -nums[i];
    return Math.abs(difference);
}
module.exports = {solve};
