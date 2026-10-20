function solve(values, other) {
  const counts = Array(other).fill(1n);
  for (let index = 1; index < values; index++) {
    for (let index2 = 1; index2 < other; index2++) {
      counts[index2] += counts[index2 - 1];
    }
  }
  const result = counts[other - 1];
  return result <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(result) : result;
}
