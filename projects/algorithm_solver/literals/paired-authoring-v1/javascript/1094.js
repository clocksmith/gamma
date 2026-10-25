class Solution {
  carPooling(trips, capacity) {
    const changes = new Map();
    for (const [passengers, start, end] of trips) {
      changes.set(start, (changes.get(start) || 0) + passengers);
      changes.set(end, (changes.get(end) || 0) - passengers);
    }
    const positions = Array.from(changes.keys()).sort((first, second) => first - second);
    let onboard = 0;
    for (const position of positions) {
      onboard += changes.get(position);
      if (onboard > capacity) {
        return false;
      }
    }
    return true;
  }
}
