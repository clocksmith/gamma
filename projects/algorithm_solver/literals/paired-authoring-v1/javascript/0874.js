class Solution {
  robotSim(commands, obstacles) {
    const blocked = new Set(obstacles.map(([x, y]) => `${x},${y}`));
    const directions = [[0, 1], [1, 0], [0, -1], [-1, 0]];
    let heading = 0;
    let x = 0;
    let y = 0;
    let best = 0;
    for (const command of commands) {
      if (command === -2) {
        heading = (heading + 3) % 4;
      } else if (command === -1) {
        heading = (heading + 1) % 4;
      } else {
        const [xStep, yStep] = directions[heading];
        for (let step = 0; step < command; step += 1) {
          const nextX = x + xStep;
          const nextY = y + yStep;
          if (blocked.has(`${nextX},${nextY}`)) {
            break;
          }
          x = nextX;
          y = nextY;
          best = Math.max(best, x * x + y * y);
        }
      }
    }
    return best;
  }
}
