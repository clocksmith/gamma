function solve(drones, target) {
  // O(n) time and O(1) space; strict improvement preserves the smallest index.
  let answer = -1;
  let bestDistance = Infinity;
  for (let index = 0; index < drones.length; index++) {
    const [x, y, travelRange] = drones[index];
    const distance = Math.abs(x - target[0]) + Math.abs(y - target[1]);
    if (distance <= travelRange && distance < bestDistance) {
      answer = index;
      bestDistance = distance;
    }
  }
  return answer;
}
