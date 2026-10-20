class Solution {
  judgeCircle(values) {
    let horizontal = 0;
    let vertical = 0;
    for (const value of values) {
      if (value === 'U') vertical++;
      else if (value === 'D') vertical--;
      else if (value === 'L') horizontal--;
      else if (value === 'R') horizontal++;
    }
    return horizontal === 0 && vertical === 0;
  }
}
