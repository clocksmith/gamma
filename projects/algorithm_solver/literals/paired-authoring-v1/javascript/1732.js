class Solution {
  largestAltitude(gain) {
    let altitude = 0;
    let highest = 0;
    for (const change of gain) {
      altitude += change;
      highest = Math.max(highest, altitude);
    }
    return highest;
  }
}
