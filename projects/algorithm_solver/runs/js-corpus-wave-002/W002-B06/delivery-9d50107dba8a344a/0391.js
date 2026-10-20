function isRectangleCover(rectangles) {
  if (rectangles.length === 0) return false;
  let smallestX = Infinity;
  let smallestY = Infinity;
  let largestX = -Infinity;
  let largestY = -Infinity;
  let area = 0;
  const corners = new Set();

  function toggle(x, y) {
    const key = `${x},${y}`;
    if (corners.has(key)) corners.delete(key);
    else corners.add(key);
  }

  for (const [x1, y1, x2, y2] of rectangles) {
    if (x1 >= x2 || y1 >= y2) return false;
    smallestX = Math.min(smallestX, x1);
    smallestY = Math.min(smallestY, y1);
    largestX = Math.max(largestX, x2);
    largestY = Math.max(largestY, y2);
    area += (x2 - x1) * (y2 - y1);
    toggle(x1, y1);
    toggle(x1, y2);
    toggle(x2, y1);
    toggle(x2, y2);
  }

  if (area !== (largestX - smallestX) * (largestY - smallestY) || corners.size !== 4) {
    return false;
  }
  return corners.has(`${smallestX},${smallestY}`) &&
    corners.has(`${smallestX},${largestY}`) &&
    corners.has(`${largestX},${smallestY}`) &&
    corners.has(`${largestX},${largestY}`);
}
