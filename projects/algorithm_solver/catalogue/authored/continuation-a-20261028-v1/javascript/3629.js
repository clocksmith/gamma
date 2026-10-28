function solve(nums) {
  let maximum = 1;
  for (const value of nums) maximum = Math.max(maximum, value);
  const smallest = new Uint32Array(maximum + 1);
  for (let value = 0; value <= maximum; value++) smallest[value] = value;
  for (let prime = 2; prime * prime <= maximum; prime++) if (smallest[prime] === prime) {
    for (let value = prime * prime; value <= maximum; value += prime) if (smallest[value] === value) smallest[value] = prime;
  }
  const divisible = new Map();
  for (const value of nums) if (value >= 2 && smallest[value] === value) divisible.set(value, []);
  for (let index = 0; index < nums.length; index++) {
    let value = nums[index];
    while (value > 1) {
      const prime = smallest[value];
      if (divisible.has(prime)) divisible.get(prime).push(index);
      while (value % prime === 0) value /= prime;
    }
  }
  const distance = new Int32Array(nums.length).fill(-1), queue = new Int32Array(nums.length);
  distance[0] = 0; queue[0] = 0; let head = 0, tail = 1;
  while (head < tail) {
    const index = queue[head++];
    if (index === nums.length - 1) return distance[index];
    const targets = divisible.get(nums[index]) || [];
    divisible.delete(nums[index]); targets.push(index - 1, index + 1);
    for (const other of targets) if (other >= 0 && other < nums.length && distance[other] < 0) {
      distance[other] = distance[index] + 1; queue[tail++] = other;
    }
  }
  return -1;
}

var minJumps = solve;
module.exports = solve;
