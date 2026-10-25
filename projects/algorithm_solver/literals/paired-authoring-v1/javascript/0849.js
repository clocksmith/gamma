class Solution {
  maxDistToClosest(seats) {
    let previous = -1;
    let farthest = 0;
    for (let index = 0; index < seats.length; index += 1) {
      if (seats[index] === 0) {
        continue;
      }
      if (previous < 0) {
        farthest = index;
      } else {
        farthest = Math.max(farthest, Math.floor((index - previous) / 2));
      }
      previous = index;
    }
    return Math.max(farthest, seats.length - 1 - previous);
  }
}
