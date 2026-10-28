function solve(points) {
  const counts = new Map();
  for (const [, y] of points) counts.set(y, (counts.get(y) || 0) + 1);
  const mod = 1000000007n;
  let total = 0n, previous = 0n;
  for (const count of counts.values()) {
    const size = BigInt(count), pairs = size * (size - 1n) / 2n;
    total = (total + previous * pairs) % mod;
    previous = (previous + pairs) % mod;
  }
  return Number(total);
}

var countTrapezoids = solve;
module.exports = solve;
