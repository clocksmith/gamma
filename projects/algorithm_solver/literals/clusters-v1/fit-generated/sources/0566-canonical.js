function solve(values, other, target) {
  const count = values.length;
  const count2 = values[0].length;
  const count3 = count * count2;
  if (count3 !== other * target) {
    return values;
  }
  const result = filledMatrix(other, target, 0);
  for (let index = 0; index < count3; index += 1) {
    result[Math.floor(index / target)][index % target] = values[Math.floor(index / count2)][index % count2];
  }
  return result;
}
function helper(values2, other2, target2) {
  const result2 = [];
  for (let index2 = 0; index2 < values2; index2 += 1) {
    result2.push(new Array(other2).fill(target2));
  }
  return result2;
}
