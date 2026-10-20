function solve(values, other) {
  const counts = countCharacters(values);
  const counts2 = countCharacters(other);
  for (const value of values) {
    if (counts[value] !== (counts2[value] || 0)) {
      return false;
    }
  }
  for (const value2 of other) {
    if (counts2[value2] !== (counts[value2] || 0)) {
      return false;
    }
  }
  return true;
}
function helper(values2) {
  const counts3 = {};
  for (const value3 of values2) {
    counts3[value3] = (counts3[value3] || 0) + 1;
  }
  return counts3;
}
