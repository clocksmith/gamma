function canPlantFlowers(values, requiredCount) {
  if (requiredCount <= 0) {
    return true;
  }
  let remainingCount = requiredCount;
  let previousOccupied = 0;
  for (let plotIndex = 0; plotIndex < values.length; plotIndex += 1) {
    const nextOccupied = plotIndex + 1 < values.length ? values[plotIndex + 1] : 0;
    if (values[plotIndex] === 0 && previousOccupied === 0 && nextOccupied === 0) {
      remainingCount -= 1;
      previousOccupied = 1;
      if (remainingCount <= 0) {
        return true;
      }
    } else {
      previousOccupied = values[plotIndex];
    }
  }
  return false;
}
function solve(flowerbed, n) {
  return canPlantFlowers(flowerbed, n);
}
