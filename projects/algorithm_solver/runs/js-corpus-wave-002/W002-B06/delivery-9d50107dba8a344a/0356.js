function isReflected(points) {
  if (points.length === 0) return true;
  let smallestX = Infinity;
  let largestX = -Infinity;
  const coordinates = new Set();

  for (const [x, y] of points) {
    smallestX = Math.min(smallestX, x);
    largestX = Math.max(largestX, x);
    coordinates.add(`${x},${y}`);
  }
  const reflectedSum = smallestX + largestX;
  for (const [x, y] of points) {
    if (!coordinates.has(`${reflectedSum - x},${y}`)) return false;
  }
  return true;
}
