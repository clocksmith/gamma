function hIndex(citations) {
  const sorted = [...citations].sort((a, b) => b - a);
  let result = 0;
  while (result < sorted.length && sorted[result] > result) result++;
  return result;
}
