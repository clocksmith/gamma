function solve(values) {
  const counts = countLowercase(values);
  for (let index = 0; index < values.length; index += 1) {
    const index2 = values.charCodeAt(index) - 97;
    if (counts[index2] === 1) {
      return index;
    }
  }
  return -1;
}
function helper(values2) {
  const counts2 = new Array(26).fill(0);
  for (const value of values2) {
    const index3 = value.charCodeAt(0) - 97;
    counts2[index3] += 1;
  }
  return counts2;
}
