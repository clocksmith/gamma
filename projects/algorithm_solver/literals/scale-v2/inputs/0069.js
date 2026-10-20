function mySqrt(x) {
  const value = BigInt(x);
  let lowerBound = 0n;
  let upperBound = value;
  let floorRoot = 0n;
  while (lowerBound <= upperBound) {
    const midpoint = lowerBound + (upperBound - lowerBound) / 2n;
    if (midpoint === 0n || midpoint <= value / midpoint) {
      floorRoot = midpoint;
      lowerBound = midpoint + 1n;
    } else {
      upperBound = midpoint - 1n;
    }
  }
  return floorRoot <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(floorRoot) : floorRoot;
}
