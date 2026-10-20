function calculateMinimumHP(dungeon) {
  const rows = dungeon.length;
  const columns = dungeon[0].length;
  const health = new Array(columns + 1).fill(Infinity);
  health[columns - 1] = 1;

  for (let row = rows - 1; row >= 0; row -= 1) {
    health[columns] = Infinity;

    for (let column = columns - 1; column >= 0; column -= 1) {
      const requiredAfter = Math.min(
        health[column],
        health[column + 1]
      );
      health[column] = Math.max(
        1,
        requiredAfter - dungeon[row][column]
      );
    }
  }

  return health[0];
}
