class Solution {
  minDominoRotations(tops, bottoms) {
    function rotations(target) {
      let topChanges = 0;
      let bottomChanges = 0;
      for (let index = 0; index < tops.length; index += 1) {
        if (tops[index] !== target && bottoms[index] !== target) return tops.length + 1;
        if (tops[index] !== target) topChanges += 1;
        if (bottoms[index] !== target) bottomChanges += 1;
      }
      return Math.min(topChanges, bottomChanges);
    }

    const best = Math.min(rotations(tops[0]), rotations(bottoms[0]));
    return best <= tops.length ? best : -1;
  }
}
