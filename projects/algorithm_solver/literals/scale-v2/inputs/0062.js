function uniquePaths(m, n) {
  const pathCounts = Array(n).fill(1n);
  for (let rowIndex = 1; rowIndex < m; rowIndex++) {
    for (let columnIndex = 1; columnIndex < n; columnIndex++) {
      pathCounts[columnIndex] += pathCounts[columnIndex - 1];
    }
  }
  const result = pathCounts[n - 1];
  return result <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(result) : result;
}
