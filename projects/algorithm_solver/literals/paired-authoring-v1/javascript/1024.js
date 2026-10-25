class Solution {
  videoStitching(clips, time) {
    if (time === 0) {
      return 0;
    }
    const ordered = clips.slice().sort((first, second) => first[0] - second[0]);
    let index = 0;
    let covered = 0;
    let count = 0;
    while (covered < time) {
      let furthest = covered;
      while (index < ordered.length && ordered[index][0] <= covered) {
        furthest = Math.max(furthest, ordered[index][1]);
        index += 1;
      }
      if (furthest === covered) {
        return -1;
      }
      covered = furthest;
      count += 1;
    }
    return count;
  }
}
