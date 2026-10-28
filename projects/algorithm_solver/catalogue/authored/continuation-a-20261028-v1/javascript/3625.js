function solve(points) {
  const directions = new Map(), lines = new Map(), midpoints = new Map(), diagonalDirections = new Map();
  const increment = (map, key) => map.set(key, (map.get(key) || 0) + 1);
  function gcd(a, b) { while (b) { const next = a % b; a = b; b = next; } return a; }
  let parallelPairs = 0, parallelograms = 0;
  for (let i = 0; i < points.length; i++) {
    const [x, y] = points[i];
    for (let j = i + 1; j < points.length; j++) {
      const [u, v] = points[j];
      let dx = u - x, dy = v - y;
      const divisor = gcd(Math.abs(dx), Math.abs(dy)); dx /= divisor; dy /= divisor;
      if (dx < 0 || (dx === 0 && dy < 0)) { dx = -dx; dy = -dy; }
      const direction = `${dx},${dy}`, line = `${direction},${dx * y - dy * x}`;
      const midpoint = `${x + u},${y + v}`, diagonal = `${midpoint},${direction}`;
      parallelPairs += (directions.get(direction) || 0) - (lines.get(line) || 0);
      parallelograms += (midpoints.get(midpoint) || 0) - (diagonalDirections.get(diagonal) || 0);
      increment(directions, direction); increment(lines, line);
      increment(midpoints, midpoint); increment(diagonalDirections, diagonal);
    }
  }
  return parallelPairs - parallelograms;
}

var countTrapezoids = solve;
module.exports = solve;
