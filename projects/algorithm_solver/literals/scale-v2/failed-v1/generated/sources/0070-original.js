/* 70. Climbing Stairs */
function climbStairs(n) {
  let previousCount = 1,
    currentCount = 1;
  for (let step = 1; step <= n; step++) {
    [previousCount, currentCount] = [currentCount, previousCount + currentCount];
  }
  return previousCount;
}
