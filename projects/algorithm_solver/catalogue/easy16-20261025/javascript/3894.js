function solve(timer) {
  // O(1) time and auxiliary space.
  if (timer === 0) return "Green";
  if (timer === 30) return "Orange";
  if (timer > 30 && timer <= 90) return "Red";
  return "Invalid";
}
