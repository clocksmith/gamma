class Solution {
  largestTimeFromDigits(arr) {
    let best = -1;
    for (let first = 0; first < 4; first += 1) {
      for (let second = 0; second < 4; second += 1) {
        if (second === first) continue;
        for (let third = 0; third < 4; third += 1) {
          if (third === first || third === second) continue;
          const fourth = 6 - first - second - third;
          const hours = arr[first] * 10 + arr[second];
          const minutes = arr[third] * 10 + arr[fourth];
          if (hours < 24 && minutes < 60) {
            best = Math.max(best, hours * 60 + minutes);
          }
        }
      }
    }
    if (best < 0) return "";
    const hours = String(Math.floor(best / 60)).padStart(2, "0");
    const minutes = String(best % 60).padStart(2, "0");
    return hours + ":" + minutes;
  }
}
