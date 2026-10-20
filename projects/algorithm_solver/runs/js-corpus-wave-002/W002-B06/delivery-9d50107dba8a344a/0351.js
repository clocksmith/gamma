function numberOfPatterns(m, n) {
  const required = Array.from({ length: 10 }, () => new Int8Array(10));
  const midpoints = [
    [1, 3, 2], [1, 7, 4], [1, 9, 5], [2, 8, 5],
    [3, 7, 5], [3, 9, 6], [4, 6, 5], [7, 9, 8]
  ];
  for (const [start, end, midpoint] of midpoints) {
    required[start][end] = midpoint;
    required[end][start] = midpoint;
  }

  function countFrom(current, selectedMask, length) {
    let total = length >= m ? 1 : 0;
    if (length === n) return total;
    for (let next = 1; next <= 9; next++) {
      const bit = 1 << next;
      const midpoint = required[current][next];
      if ((selectedMask & bit) !== 0 ||
        (midpoint !== 0 && (selectedMask & (1 << midpoint)) === 0)) continue;
      total += countFrom(next, selectedMask | bit, length + 1);
    }
    return total;
  }

  return 4 * countFrom(1, 1 << 1, 1) +
    4 * countFrom(2, 1 << 2, 1) + countFrom(5, 1 << 5, 1);
}
